#!/usr/bin/env python3
"""
Companion WebSocket Server — 实时聊天 WebSocket 服务 (python-socketio)
端口: 5001
"""
import json
import time
import threading
import queue
import sys
import os

sys.path.insert(0, '/home/robot/.openclaw/workspace/humantogether')
from companion_manager import send_to_companion, _gateway_invoke

import socketio

# ── Persistent session cache ──
session_cache = {}

def get_or_create_session(uid, cid):
    """获取或创建持久 subagent session"""
    cache_key = f"{uid}_{cid}"
    if cache_key in session_cache:
        return session_cache[cache_key]
    
    from companion_manager import build_task_message
    task = build_task_message(uid, cid, "你好！请用简短活泼的一句话介绍自己。", "用户")
    
    try:
        spawn_result = _gateway_invoke("sessions_spawn", {
            "task": task,
            "label": f"companion_{cid}_{uid[:8]}",
            "runtime": "subagent",
            "mode": "session",
            "cleanup": "keep",
        })
        inner_text = spawn_result["content"][0]["text"]
        inner = json.loads(inner_text)
        child_key = inner["childSessionKey"]
        session_cache[cache_key] = child_key
        return child_key
    except Exception as e:
        print(f"[WSS] Failed to create session for {cid}: {e}")
        return None

# ── Request queue for worker thread ──
request_queue = queue.Queue()

def worker_loop():
    """后台线程：处理聊天请求，轮询 subagent 响应"""
    while True:
        try:
            item = request_queue.get(timeout=1)
            if item is None:
                continue
            uid, cid, user_msg, sid, resp_queue = item
            
            # Get or create persistent session
            session_key = get_or_create_session(uid, cid)
            if not session_key:
                resp_queue.put({"error": "无法创建AI会话，请稍后重试", "sid": sid})
                continue
            
            # Send message to existing session
            try:
                _gateway_invoke("sessions_send", {
                    "sessionKey": session_key,
                    "message": user_msg,
                })
            except Exception as e:
                print(f"[WSS] sessions_send error: {e}")
                # Fallback: spawn new
                reply, err = send_to_companion(uid, cid, user_msg, timeout=30)
                resp_queue.put({"reply": reply, "error": err, "sid": sid})
                continue
            
            # Poll for result (0.4s interval)
            start = time.time()
            found = False
            last_count = 0
            
            while time.time() - start < 30:
                time.sleep(0.4)
                try:
                    hist_result = _gateway_invoke("sessions_history", {
                        "sessionKey": session_key,
                        "limit": 3,
                    })
                    hist_text = hist_result["content"][0]["text"]
                    msgs = json.loads(hist_text).get("messages", [])
                    assistant_msgs = [m for m in msgs if m["role"] == "assistant"]
                    
                    if len(assistant_msgs) > last_count:
                        last_count = len(assistant_msgs)
                        latest = assistant_msgs[-1]
                        for c in latest.get("content", []):
                            if c.get("type") == "text" and "<final>" in c["text"]:
                                t = c["text"]
                                start_idx = t.find("<final>") + 7
                                end_idx = t.find("</final>")
                                reply = t[start_idx:end_idx].strip()
                                resp_queue.put({"reply": reply, "error": None, "sid": sid})
                                found = True
                                break
                    if found:
                        break
                except Exception as e:
                    if "404" in str(e) or "not found" in str(e).lower():
                        continue
                    break
            
            if not found:
                resp_queue.put({"reply": None, "error": "timeout", "sid": sid})
                
        except queue.Empty:
            continue
        except Exception as e:
            print(f"[WSS] Worker error: {e}")

# Start worker thread
worker_thread = threading.Thread(target=worker_loop, daemon=True)
worker_thread.start()

# ── SocketIO server ──
sio = socketio.AsyncServer(async_mode='gevent', cors_allowed_origins='*')

@sio.event
def connect(sid, environ):
    print(f"[WSS] Client connected: {sid}")

@sio.event
def auth(sid, data):
    """Receive auth, register session"""
    uid = data.get('uid', 'guest') if data else 'guest'
    sio.enter_room(sid, uid)
    print(f"[WSS] {sid} authenticated as {uid}")
    sio.emit('connected', {'uid': uid}, room=sid)

@sio.event
def chat_message(sid, data):
    """Handle incoming chat message"""
    uid = data.get('uid', 'guest')
    cid = data.get('cid', 'luna')
    text = data.get('text', '')
    if not text:
        return
    
    # Queue the request
    resp_queue = queue.Queue()
    request_queue.put((uid, cid, text, sid, resp_queue))
    
    # Wait for result (with timeout)
    try:
        result = resp_queue.get(timeout=35)
        reply = result.get('reply', '抱歉出了点小问题 😅')
        error = result.get('error')
        if error:
            reply = f"等待回复超时... 😅"
        sio.emit('chat_reply', {
            'cid': cid,
            'reply': reply,
            'error': error
        }, room=sid)
    except queue.Empty:
        sio.emit('chat_reply', {
            'cid': cid,
            'reply': '抱歉，响应超时 😅',
            'error': 'timeout'
        }, room=sid)

@sio.event
def disconnect(sid):
    print(f"[WSS] Client disconnected: {sid}")

# Wrap as WSGI app and run
app = socketio.WSGIApp(sio)

if __name__ == '__main__':
    from gevent.pywsgi import WSGIServer
    print(f"[WSS] Starting Companion WS Server on 0.0.0.0:5001")
    WSGIServer(('0.0.0.0', 5001), app).serve_forever()
