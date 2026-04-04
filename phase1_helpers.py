# Phase 1 Helper Functions for 共生境

def extract_memory(msg):
    """Extract potential memory from user message"""
    msg_lower = msg.lower()
    memories = []
    for key in ["我在", "我去过", "我喜欢", "我的", "我是"]:
        if key in msg_lower:
            idx = msg_lower.find(key)
            start = max(0, idx - 5)
            end = idx + 20
            sentence = msg[start:end].strip()
            if len(sentence) > 5:
                memories.append(("fact", sentence, 6))
    for key in ["昨天", "今天", "上周"]:
        if key in msg_lower:
            idx = msg_lower.find(key)
            start = max(0, idx - 5)
            end = idx + 25
            sentence = msg[start:end].strip()
            if len(sentence) > 5:
                memories.append(("event", sentence, 7))
    for key in ["感觉", "觉得", "心情"]:
        if key in msg_lower:
            idx = msg_lower.find(key)
            start = max(0, idx - 5)
            end = idx + 20
            sentence = msg[start:end].strip()
            if len(sentence) > 5:
                memories.append(("emotion", sentence, 5))
    return memories


def save_memories(uid, cid, msg, sqlite3, DB):
    """Save extracted memories to database"""
    memories = extract_memory(msg)
    if not memories:
        return
    d = sqlite3.connect(DB)
    for mtype, content, importance in memories:
        d.execute(
            "INSERT INTO ai_memories (user_id, companion_id, memory_type, content, importance) VALUES (?,?,?,?,?)",
            (uid, cid, mtype, content, importance)
        )
    d.commit()
    d.close()


def get_memories(uid, cid, limit=10):
    """Get important memories for a user-companion pair"""
    import sqlite3
    DB = "/home/robot/.openclaw/workspace/humantogether/sgj_warm.db"
    d = sqlite3.connect(DB)
    d.row_factory = sqlite3.Row
    rows = d.execute(
        "SELECT content, memory_type, importance, created_at FROM ai_memories WHERE user_id=? AND companion_id=? ORDER BY importance DESC, created_at DESC LIMIT ?",
        (uid, cid, limit)
    ).fetchall()
    d.close()
    return [
        {"content": r["content"], "memory_type": r["memory_type"], "importance": r["importance"], "created_at": r["created_at"]}
        for r in rows
    ]


def build_memory_context(uid, cid):
    """Build a memory context string for AI prompts"""
    memories = get_memories(uid, cid, 5)
    if not memories:
        return ""
    ctx = "\n[关于你的重要记忆]\n"
    for m in memories:
        type_emoji = {"fact": "📝", "event": "📅", "emotion": "💭"}.get(m["memory_type"], "📝")
        ctx = ctx + "- " + type_emoji + " " + m["content"] + "\n"
    return ctx
