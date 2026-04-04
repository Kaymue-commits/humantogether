"""
Companion Manager — 伙伴AI管理系统
通过 OpenClaw Gateway API 调用 subagent（MiniMax-M2.7模型），为每个伙伴配置专属人格
"""
import json
import time
import sqlite3
import urllib.request
import urllib.error
from datetime import datetime

# Companion personality system prompts
from companions.luna import SYSTEM_PROMPT as LUNA_PROMPT
from companions.kai import SYSTEM_PROMPT as KAI_PROMPT
from companions.nova import SYSTEM_PROMPT as NOVA_PROMPT
from companions.milo import SYSTEM_PROMPT as MILO_PROMPT
from companions.sage import SYSTEM_PROMPT as SAGE_PROMPT

COMPANION_PROMPTS = {
    "luna": LUNA_PROMPT,
    "kai": KAI_PROMPT,
    "nova": NOVA_PROMPT,
    "milo": MILO_PROMPT,
    "sage": SAGE_PROMPT,
}

COMPANION_INFO = {
    "luna": {"name": "Luna",  "emoji": "🌙", "personality": "温柔倾听型", "room_color": 0xFFF5F0, "wall": 0xFFE4E1, "floor": 0xE8D5C4, "accent": 0xFFB6C1},
    "kai":  {"name": "Kai",   "emoji": "🌊", "personality": "冷静理性型", "room_color": 0xF0F8FF, "wall": 0xE6F0FA, "floor": 0xD0D8E4, "accent": 0x4169E1},
    "nova": {"name": "Nova",  "emoji": "⭐", "personality": "积极激励型", "room_color": 0xFFF8E7, "wall": 0xFFF3CC, "floor": 0xE8D8A0, "accent": 0xFF8C00},
    "milo": {"name": "Milo",  "emoji": "🌿", "personality": "平和佛系型", "room_color": 0xF0FFF0, "wall": 0xE0F5E0, "floor": 0xC8D8C0, "accent": 0x228B22},
    "sage": {"name": "Sage",  "emoji": "📚", "personality": "智慧导师型", "room_color": 0xFAF0E6, "wall": 0xF5E6D3, "floor": 0xD8C8A8, "accent": 0x8B4513},
}

GATEWAY_URL = "http://127.0.0.1:18789"
GATEWAY_TOKEN = "b57d8f4cae1d60a92c80812ff8f5dca7598a4a7496e1869f"
DB_PATH = "sgj_warm.db"


def _gateway_invoke(tool, args=None, session_key=None):
    """Call OpenClaw Gateway /tools/invoke"""
    payload = {"tool": tool, "args": args or {}}
    if session_key:
        payload["sessionKey"] = session_key
    req = urllib.request.Request(
        f"{GATEWAY_URL}/tools/invoke",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {GATEWAY_TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        result = json.loads(resp.read())
        if not result.get("ok"):
            raise Exception(f"Gateway error: {result}")
        return result.get("result")


def get_memory_context(uid, cid, limit=8):
    """获取用户和该伙伴的对话历史"""
    try:
        d = sqlite3.connect(DB_PATH)
        d.execute("PRAGMA encoding='UTF-8'")
        rows = d.execute("""
            SELECT content, role FROM ai_messages
            WHERE user_id=? AND companion_id=? AND role IN ('user','assistant')
            ORDER BY created_at DESC LIMIT ?
        """, (uid, cid, limit * 2)).fetchall()
        d.close()
        if not rows:
            return ""
        turns = []
        for content, role in reversed(rows):
            role_label = "\u7528\u6237" if role == "user" else COMPANION_INFO.get(cid, {}).get("name", "AI")
            turns.append(f"{role_label}\uff1a{content[:250]}")
        return "\n".join(turns)
    except Exception:
        return ""


def build_task_message(uid, cid, user_message, user_name="\u966a\u4f34"):
    """构建发送给subagent的完整task"""
    memory = get_memory_context(uid, cid, limit=10)
    info = COMPANION_INFO.get(cid, COMPANION_INFO["luna"])
    base = COMPANION_PROMPTS.get(cid, COMPANION_PROMPTS["luna"])

    history_section = f"\n\n# \u4f60\u4eec\u4e4b\u95f4\u7684\u5bf9\u8bdd\n{memory}\n\n\u8bf7\u6839\u636e\u5bf9\u8bdd\u5386\u53f2\uff0c\u4fdd\u6301\u4f60\u7684\u6027\u683c\u7279\u70b9\uff0c\u81ea\u7136\u5ef6\u7eed\u5bf9\u8bdd\u3002" if memory else ""

    return base + history_section + f"\n\n# \u5f53\u524d\u7528\u6237\n\u7528\u6237\u540d{user_name}\uff0c\u4f60\u7684\u597d\u4f19\u4f34\u3002\n\n\u7528\u6237\u8bf4\uff1a{user_message}"


def send_to_companion(uid, cid, user_message, user_name="\u966a\u4f34", timeout=35):
    """
    发送消息给指定伙伴的AI subagent，等待回复。
    返回 (reply_text, error)
    """
    task = build_task_message(uid, cid, user_message, user_name)
    info = COMPANION_INFO.get(cid, COMPANION_INFO["luna"])

    # Spawn subagent
    spawn_result = _gateway_invoke("sessions_spawn", {
        "task": task,
        "label": f"{info['name']}_chat",
        "runtime": "subagent",
        "mode": "run",
        "cleanup": "keep",
    })

    # Extract child session key from nested JSON
    inner_text = spawn_result["content"][0]["text"]
    inner = json.loads(inner_text)
    child_key = inner["childSessionKey"]

    # Poll for result
    start = time.time()
    while time.time() - start < timeout:
        time.sleep(0.4)
        try:
            hist_result = _gateway_invoke("sessions_history", {
                "sessionKey": child_key,
                "limit": 5,
            })
            hist_text = hist_result["content"][0]["text"]
            msgs = json.loads(hist_text).get("messages", [])

            for m in msgs:
                if m["role"] == "assistant":
                    for c in m.get("content", []):
                        if c.get("type") == "text" and c["text"].strip():
                            reply = c["text"].strip()
                            # Save to DB
                            _save_message(uid, cid, user_message, reply)
                            return reply, None
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                continue
            return None, str(e)

    return None, "timeout"


def _save_message(uid, cid, user_msg, assistant_msg):
    """保存对话到数据库"""
    try:
        d = sqlite3.connect(DB_PATH)
        now = datetime.now().isoformat()
        d.execute("""
            INSERT INTO ai_messages (id, user_id, companion_id, role, content, mood_tag, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (str(time.time())[:12].replace(".", ""), uid, cid, "user", user_msg[:1000], "chat", now))
        d.execute("""
            INSERT INTO ai_messages (id, user_id, companion_id, role, content, mood_tag, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (str(time.time())[:12].replace(".", "") + "a", uid, cid, "assistant", assistant_msg[:1000], "chat", now))
        d.commit()
        d.close()
    except Exception:
        pass


def get_all_companions():
    return COMPANION_INFO


def get_companion_info(cid):
    return COMPANION_INFO.get(cid, COMPANION_INFO["luna"])
