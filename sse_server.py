#!/usr/bin/env python3
"""
Companion Chat SSE Server — 实时聊天推送服务
Flask app.py 之外独立运行，处理 subagent 响应推送
端口: 5002
"""
import json
import time
import threading
import queue
import sys
import os
sys.path.insert(0, '/home/robot/.openclaw/workspace/humantogether')
from companion_manager import send_to_companion

from flask import Flask, Response, request, jsonify

app = Flask(__name__)

# Pending response queues per uid
pending_queues = {}
pending_lock = threading.Lock()

def get_queue(uid):
    with pending_lock:
        if uid not in pending_queues:
            pending_queues[uid] = queue.Queue()
        return pending_queues[uid]

# ── Worker thread ──
request_queue = queue.Queue()

def worker_loop():
    while True:
        try:
            item = request_queue.get(timeout=1)
            if item is None:
                continue
            uid, cid, user_msg = item
            q = get_queue(uid)
            
            try:
                reply, err = send_to_companion(uid, cid, user_msg, timeout=30)
                q.put({"reply": reply, "error": err})
            except Exception as e:
                q.put({"reply": None, "error": str(e)})
                
        except queue.Empty:
            continue
        except Exception as e:
            print(f"[SSE] Worker error: {e}")

worker = threading.Thread(target=worker_loop, daemon=True)
worker.start()

# ── Routes ──

@app.route("/stream/<uid>/<cid>")
def stream(uid, cid):
    """SSE endpoint: browser connects here to receive responses"""
    def event_stream():
        q = get_queue(uid)
        yield "event: connected\ndata: {}\n\n"
        while True:
            try:
                result = q.get(timeout=60)
                if result:
                    yield f"event: reply\ndata: {json.dumps(result)}\n\n"
            except queue.Empty:
                yield "event: heartbeat\ndata: {}\n\n"
    
    return Response(event_stream(), mimetype='text/event-stream')

@app.route("/chat/send", methods=["POST"])
def chat_send():
    data = request.json
    uid = data.get("uid", "guest")
    cid = data.get("cid", "luna")
    text = data.get("text", "")
    if not text:
        return jsonify({"error": "empty message"})
    request_queue.put((uid, cid, text))
    return jsonify({"status": "queued"})

@app.route("/chat/status", methods=["GET"])
def chat_status():
    return jsonify({"status": "ok", "worker": "running"})

if __name__ == "__main__":
    print("[SSE] Starting Companion SSE Chat Server on 0.0.0.0:5002")
    app.run(host="0.0.0.0", port=5002, threaded=True, debug=False)
