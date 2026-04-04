#!/usr/bin/env python3
"""
HumanTogether — Local MVP
人机共存平台 · 本地最小可行版本

功能：
  • AI 情感陪伴（聊天机器人）
  • 机会/工作发布板
  • 人类互助配对
  • 每日精神鼓励

运行：python3 mvp.py
访问：http://localhost:5000
"""

from flask import Flask, request, jsonify, render_template_string, session
from flask_socketio import SocketIO, emit
import sqlite3
import hashlib
import uuid
import datetime
import random
import re
from datetime import datetime

app = Flask(__name__)
app.secret_key = "humantogether_mvp_secret_key_change_in_production"
socketio = SocketIO(app, cors_allowed_origins="*")
DATABASE = "humantogether.db"

# ============ DATABASE ============
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE,
        display_name TEXT,
        avatar_emoji TEXT,
        bio TEXT,
        mood TEXT DEFAULT 'neutral',
        mood_updated_at TEXT,
        created_at TEXT,
        is_ai_helper INTEGER DEFAULT 0
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        room TEXT,
        sender_id TEXT,
        sender_name TEXT,
        content TEXT,
        msg_type TEXT DEFAULT 'text',
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS opportunities (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        user_name TEXT,
        title TEXT,
        description TEXT,
        category TEXT,
        reward TEXT,
        location TEXT,
        contact TEXT,
        status TEXT DEFAULT 'open',
        views INTEGER DEFAULT 0,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS moods (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        mood TEXT,
        note TEXT,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS companions (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        companion_name TEXT,
        companion_emoji TEXT,
        relationship TEXT DEFAULT 'friend',
        memory TEXT,
        created_at TEXT
    )""")

    # Seed AI companions
    c.execute("""CREATE TABLE IF NOT EXISTS ai_companions (
        id TEXT PRIMARY KEY,
        name TEXT,
        emoji TEXT,
        personality TEXT,
        specialty TEXT
    )""")

    companions = [
        ("ai_luna", "Luna", "🌙", "温柔倾听，永远在你身边", "情感支持"),
        ("ai_kai", "Kai", "🌊", "冷静理性，帮你理清思路", "职业规划"),
        ("ai_nova", "Nova", "⭐", "积极阳光，鼓励你前行", "生活陪伴"),
        ("ai_milo", "Milo", "🌿", "佛系平和，帮你放松减压", "冥想放松"),
    ]
    c.executemany("INSERT OR IGNORE INTO ai_companions VALUES (?,?,?,?,?)", companions)

    conn.commit()
    conn.close()
    print("✅ 数据库初始化完成")

# ============ HELPERS ============
def get_db():
    return sqlite3.connect(DATABASE)

def get_user(uid):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (uid,))
    row = c.fetchone()
    conn.close()
    return row

def ai_response(user_message, mood, username):
    """Simple rule-based AI companion response"""
    msg = user_message.lower()

    # Mood detection
    if any(w in msg for w in ["难过", "伤心", "痛苦", "depressed", "sad", "crying"]):
        return {
            "emoji": "🤗",
            "text": f"我感受到你现在很难过，{username}。有时候难过就像下雨天，雨过后总会有晴空。慢慢来，我在这里陪着你。",
            "mood": "sad"
        }
    if any(w in msg for w in ["焦虑", "担心", "害怕", "anxious", "worried", "fear"]):
        return {
            "emoji": "🌿",
            "text": f"{username}，我理解你的担心。深呼吸，我们一起把事情理一理。焦虑的反面是具体——告诉我你在担心什么？",
            "mood": "anxious"
        }
    if any(w in msg for w in ["无聊", "空虚", "lonely", "bored", "empty"]):
        return {
            "emoji": "✨",
            "text": f"无聊的时候正好是探索的好时机！{username}，你有没有想过学点新东西？或者我们可以玩个小游戏~",
            "mood": "bored"
        }
    if any(w in msg for w in ["开心", "高兴", "happy", "joy", "excited"]):
        return {
            "emoji": "🎉",
            "text": f"太棒了，{username}！你的快乐也会感染到我。有什么好事发生了吗？我想听听！",
            "mood": "happy"
        }
    if any(w in msg for w in ["工作", "job", "career", "职业", "失业"]):
        return {
            "emoji": "💼",
            "text": f"{username}，职业发展是人生大事。你是想找新机会，还是对现在的方向有困惑？我可以帮你看看 /jobs 里的机会，或者聊聊你的职业规划。",
            "mood": "neutral"
        }
    if any(w in msg for w in ["help", "帮", "帮助", "怎么"]):
        return {
            "emoji": "🤝",
            "text": f"当然！我是你的 AI 助手 {username}。输入 /jobs 查看工作机会，输入 /community 和真人聊，输入 /companion 领养你的专属 AI 伙伴！",
            "mood": "neutral"
        }
    if any(w in msg for w in ["who are you", "你是谁", "介绍自己"]):
        return {
            "emoji": "🌟",
            "text": "我是 HumanTogether 的 AI 助手 🌟 我在这里陪伴你、帮你找工作、和真人们互相帮助。这里是人类和机器人共存的地方——我们一起，让生活更好！",
            "mood": "neutral"
        }
    if any(w in msg for w in ["thanks", "thank", "谢", "grateful"]):
        return {
            "emoji": "💛",
            "text": f"不客气，{username}！能帮到你我很开心。随时来找我聊天 💛",
            "mood": "happy"
        }

    # Default responses
    defaults = [
        f"我听到了，{username}。你想聊聊什么？",
        f"嗯嗯，继续说，我在听 👂",
        f"有意思！告诉我更多 📖",
        f"你说的让我想到了 /jobs 里有个机会，也许你会感兴趣？",
        f"记住，不管发生什么，这里永远欢迎你 🤗",
    ]
    return {
        "emoji": "🌙",
        "text": random.choice(defaults),
        "mood": "neutral"
    }

MOOD_QUOTES = [
    ("今天的不开心就止于此吧，明天依然光芒万丈 ✨", "🌅"),
    ("你不需要很厉害才能开始，你需要开始才能很厉害 🚀", "💪"),
    ("生活总会给你另一个机会，另一个开始 🎁", "🌱"),
    ("照顾好自己的心灵，它决定了你是谁 🧠💫", "🌿"),
    ("你不是一个人，我们都在这里陪着你 🤝", "👥"),
    ("今天辛苦了，明天又是新的一天 🌙", "🌛"),
    ("你的价值不取决于别人的认可，你本来就值得 💎", "💎"),
    ("累了就休息，没人是完美的 🌸", "🌸"),
]

DAILY_MOOD_TIPS = {
    "sad": "今天天气不错，出门走走吧 🍃",
    "anxious": "试试深呼吸：吸气4秒，屏住4秒，呼气4秒 🌬️",
    "bored": "学点新东西吧！或者去 /jobs 看看机会 ✨",
    "happy": "保持这份好心情！记得和人分享 🎉",
    "neutral": "每天都是新的开始 🌅",
}

# ============ WEB PAGES ============

HOME_PAGE = """
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HumanTogether — 人机共存平台</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family: -apple-system, sans-serif; background:#f0f4ff; color:#333; }
.hero { background: linear-gradient(135deg, #667eea, #764ba2); color:white; padding:60px 20px; text-align:center; }
.hero h1 { font-size:2.5em; margin-bottom:10px; }
.hero p { font-size:1.2em; opacity:0.9; margin-bottom:30px; }
.hero .btns a { display:inline-block; padding:12px 30px; background:white; color:#667eea; border-radius:25px; text-decoration:none; font-weight:bold; margin:5px; }
.features { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:20px; padding:40px 20px; max-width:1000px; margin:0 auto; }
.card { background:white; border-radius:16px; padding:25px; text-align:center; box-shadow:0 4px 15px rgba(0,0,0,0.08); }
.card .emoji { font-size:3em; margin-bottom:15px; }
.card h3 { color:#667eea; margin-bottom:10px; }
.card p { color:#888; font-size:0.9em; line-height:1.6; }
.mood-section { background:white; max-width:700px; margin:20px auto; padding:30px; border-radius:16px; text-align:center; }
.mood-section blockquote { font-size:1.3em; color:#555; margin:20px 0; line-height:1.8; }
.mood-section cite { color:#888; font-size:0.9em; }
section { max-width:900px; margin:20px auto; padding:20px; }
h2 { color:#667eea; margin-bottom:15px; font-size:1.5em; }
</style>
</head>
<body>
<div class="hero">
  <h1>🌟 HumanTogether</h1>
  <p>人机共存 · 精神寄托 · 工作机会 · 互助社区</p>
  <div class="btns">
    <a href="/register">🚀 加入平台</a>
    <a href="/chat">💬 开始聊天</a>
    <a href="/jobs">💼 查看机会</a>
  </div>
</div>

<div class="features">
  <div class="card"><div class="emoji">🤖</div><h3>AI 陪伴</h3><p>24小时在线的AI伙伴，倾听、安慰、陪你度过每一天</p></div>
  <div class="card"><div class="emoji">🤝</div><h3>人类互助</h3><p>和真人互相帮助，分享机会，解决困难</p></div>
  <div class="card"><div class="emoji">💼</div><h3>工作机会</h3><p>找工作、找项目、找合作，信息真实高效</p></div>
  <div class="card"><div class="emoji">🌙</div><h3>精神寄托</h3><p>每日鼓励、心灵陪伴，让你不孤单</p></div>
</div>

<div class="mood-section">
  <h2>🌅 每日鼓励</h2>
  <blockquote>{{ quote }}</blockquote>
  <cite>{{ cite_emoji }} {{ cite_text }}</cite>
</div>

<section>
  <h2>💬 AI 情感陪伴</h2>
  <p>不管你开心还是难过，AI 伙伴永远在这里。24小时陪你聊天，倾听你的心声。</p>
</section>

<section>
  <h2>🤝 人类互助社区</h2>
  <p>遇到困难？来这里找真人帮忙。分享你的技能，帮助他人，同时获得回报。</p>
</section>

<section>
  <h2>💼 机会发布板</h2>
  <p>找工作、找兼职、找合作——免费发布，信息透明。</p>
</section>

<script>
  // Daily mood refresh
  const moods = document.querySelectorAll('.mood-card');
  // Auto-refresh quote every 30s
  setTimeout(() => location.reload(), 30000);
</script>
</body>
</html>
"""

REGISTER_PAGE = """
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>注册 — HumanTogether</title>
<style>
body { font-family: -apple-system, sans-serif; background:#f0f4ff; display:flex; justify-content:center; align-items:center; min-height:100vh; margin:0; }
.box { background:white; padding:40px; border-radius:20px; box-shadow:0 10px 40px rgba(0,0,0,0.1); width:90%; max-width:400px; }
h1 { color:#667eea; text-align:center; margin-bottom:5px; }
.sub { color:#888; text-align:center; margin-bottom:30px; }
label { display:block; color:#555; font-weight:bold; margin:15px 0 5px; }
input, select, textarea { width:100%; padding:12px; border:2px solid #e0e0ff; border-radius:10px; font-size:1em; outline:none; }
input:focus, textarea:focus { border-color:#667eea; }
.btn { width:100%; padding:14px; background:linear-gradient(135deg,#667eea,#764ba2); color:white; border:none; border-radius:25px; font-size:1.1em; font-weight:bold; cursor:pointer; margin-top:20px; }
.btn:hover { opacity:0.9; }
.emoji-pick { display:flex; gap:8px; flex-wrap:wrap; margin-top:8px; }
.emoji-pick span { font-size:1.8em; cursor:pointer; padding:5px; border-radius:10px; transition:background 0.2s; }
.emoji-pick span:hover { background:#f0f4ff; }
</style>
</head>
<body>
<div class="box">
  <h1>🌟 加入我们</h1>
  <p class="sub">创建你的专属身份</p>
  <form action="/register" method="POST">
    <label>你的名字（昵称）</label>
    <input name="username" placeholder="例如：星河漫步" required maxlength="30">

    <label>显示名称</label>
    <input name="display_name" placeholder="对外展示的名字" maxlength="30">

    <label>头像 Emoji 🦞</label>
    <div class="emoji-pick">
      {% for e in emojis %}
      <label><input type="radio" name="avatar_emoji" value="{{e}}" style="display:none">{{e}}</label>
      {% endfor %}
    </div>

    <label>简单介绍一下自己</label>
    <textarea name="bio" rows="3" placeholder="我是...我想..." maxlength="200"></textarea>

    <label>你现在的状态</label>
    <select name="mood">
      <option value="neutral">😊 平静</option>
      <option value="happy">😄 开心</option>
      <option value="sad">😢 难过</option>
      <option value="anxious">😰 焦虑</option>
      <option value="bored">😑 无聊</option>
    </select>

    <button type="submit" class="btn">🚀 加入 HumanTogether</button>
  </form>
  <script>
    document.querySelectorAll('.emoji-pick span').forEach(el => {
      el.addEventListener('click', () => {
        document.querySelectorAll('.emoji-pick span').forEach(s => s.style.background='transparent');
        el.style.background = '#e0e0ff';
        el.querySelector('input').checked = true;
      });
    });
  </script>
</div>
</body>
</html>
"""

CHAT_PAGE = """
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>聊天 — HumanTogether</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family: -apple-system, sans-serif; background:#f0f4ff; height:100vh; display:flex; flex-direction:column; }
header { background:linear-gradient(135deg,#667eea,#764ba2); color:white; padding:15px 20px; display:flex; align-items:center; justify-content:space-between; }
header h1 { font-size:1.2em; }
header a { color:white; text-decoration:none; font-size:0.9em; }
.msgs { flex:1; overflow-y:auto; padding:20px; display:flex; flex-direction:column; gap:12px; }
.msg { max-width:70%; padding:12px 16px; border-radius:18px; line-height:1.6; }
.msg.ai { background:#e8ecff; align-self:flex-start; border-bottom-left-radius:4px; }
.msg.human { background:#667eea; color:white; align-self:flex-end; border-bottom-right-radius:4px; }
.msg .sender { font-size:0.75em; opacity:0.7; margin-bottom:4px; }
.msg.ai .sender { text-align:left; }
.input-area { padding:15px 20px; background:white; display:flex; gap:10px; border-top:1px solid #eee; }
.input-area input { flex:1; padding:12px 16px; border:2px solid #e0e0ff; border-radius:25px; font-size:1em; outline:none; }
.input-area input:focus { border-color:#667eea; }
.input-area button { padding:10px 20px; background:#667eea; color:white; border:none; border-radius:20px; cursor:pointer; font-weight:bold; }
.companion-bar { background:white; padding:10px 20px; display:flex; gap:10px; overflow-x:auto; border-bottom:1px solid #eee; }
.companion-chip { padding:6px 14px; border-radius:20px; background:#f0f4ff; font-size:0.85em; cursor:pointer; white-space:nowrap; }
.companion-chip.active { background:#667eea; color:white; }
</style>
</head>
<body>
<header>
  <h1>🌟 HumanTogether 聊天</h1>
  <a href="/">🏠 首页</a>
</header>

<div class="companion-bar">
  {% for c in companions %}
  <div class="companion-chip {{ 'active' if loop.first }}" data-id="{{c[0]}}">{{c[2]}} {{c[1]}}</div>
  {% endfor %}
  <div class="companion-chip" data-id="community">👥 社区</div>
</div>

<div class="msgs" id="msgs">
  <div class="msg ai">
    <div class="sender">🌙 Luna</div>
    欢迎，{{ username }}！我是 Luna 🌙 我在这里倾听你。今天感觉怎么样？
  </div>
</div>

<div class="input-area">
  <input id="msg_input" placeholder="说点什么... (输入 /jobs 查看工作)" autofocus>
  <button onclick="send()">发送</button>
</div>

<script>
let current_companion = "{{ companions[0][0] if companions else 'ai_luna' }}";
let username = "{{ username }}";

async function send() {
  const input = document.getElementById('msg_input');
  const text = input.value.trim();
  if (!text) return;
  input.value = '';

  // Add user message
  const msgs = document.getElementById('msgs');
  msgs.innerHTML += `<div class="msg human"><div class="sender">你</div>${text}</div>`;
  msgs.scrollTop = msgs.scrollHeight;

  // Send to server
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ message: text, room: current_companion, username: username })
  });
  const data = await res.json();

  const name_map = {
    'ai_luna': '🌙 Luna', 'ai_kai': '🌊 Kai',
    'ai_nova': '⭐ Nova', 'ai_milo': '🌿 Milo'
  };

  msgs.innerHTML += `<div class="msg ai"><div class="sender">${name_map[current_companion] || 'AI'}</div>${data.emoji} ${data.text}</div>`;
  msgs.scrollTop = msgs.scrollHeight;
}

document.getElementById('msg_input').addEventListener('keypress', e => {
  if (e.key === 'Enter') send();
});

// Switch companion
document.querySelectorAll('.companion-chip').forEach(chip => {
  chip.addEventListener('click', () => {
    document.querySelectorAll('.companion-chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    current_companion = chip.dataset.id;
    document.getElementById('msgs').innerHTML = `<div class="msg ai"><div class="sender">AI</div>切换到 ${chip.textContent}，有什么想聊的？</div>`;
  });
});
</script>
</body>
</html>
"""

JOBS_PAGE = """
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>机会 — HumanTogether</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family: -apple-system, sans-serif; background:#f0f4ff; min-height:100vh; }
header { background:linear-gradient(135deg,#667eea,#764ba2); color:white; padding:15px 20px; display:flex; justify-content:space-between; align-items:center; }
header a { color:white; text-decoration:none; }
main { max-width:800px; margin:0 auto; padding:20px; }
h2 { color:#667eea; margin-bottom:15px; }
.post-form { background:white; padding:20px; border-radius:16px; margin-bottom:20px; box-shadow:0 4px 15px rgba(0,0,0,0.08); }
.post-form input, .post-form textarea, .post-form select { width:100%; padding:10px; border:2px solid #e0e0ff; border-radius:10px; font-size:1em; margin-bottom:10px; outline:none; }
.post-form button { padding:10px 25px; background:#667eea; color:white; border:none; border-radius:20px; cursor:pointer; font-size:1em; }
.job-card { background:white; padding:18px; border-radius:12px; margin-bottom:12px; box-shadow:0 2px 8px rgba(0,0,0,0.06); }
.job-card h3 { color:#333; margin-bottom:8px; }
.job-card .meta { color:#888; font-size:0.85em; margin-bottom:8px; }
.job-card .reward { color:#667eea; font-weight:bold; font-size:1.1em; }
.job-card .desc { color:#555; font-size:0.9em; line-height:1.6; margin:8px 0; }
.status { display:inline-block; padding:3px 10px; border-radius:12px; font-size:0.8em; background:#e8ecff; color:#667eea; }
.empty { text-align:center; padding:40px; color:#888; }
</style>
</head>
<body>
<header>
  <h1>💼 机会发布板</h1>
  <a href="/">🏠 首页</a>
</header>
<main>
  <div class="post-form">
    <h3>📌 发布新机会</h3>
    <input id="title" placeholder="职位/项目名称">
    <textarea id="desc" rows="2" placeholder="详细描述..."></textarea>
    <input id="reward" placeholder="报酬（如：¥500、 面议）">
    <input id="location" placeholder="地点（线上/线下/城市）">
    <input id="contact" placeholder="联系方式（微信/TG/邮箱）">
    <button onclick="post_job()">🚀 发布机会</button>
  </div>
  <div id="jobs_list"></div>
</main>
<script>
async function load_jobs() {
  const res = await fetch('/api/jobs');
  const jobs = await res.json();
  const el = document.getElementById('jobs_list');
  if (!jobs.length) {
    el.innerHTML = '<div class="empty">暂无机会，发布一个吧！</div>';
    return;
  }
  el.innerHTML = jobs.map(j => `
    <div class="job-card">
      <h3>${j.title}</h3>
      <div class="meta">👤 ${j.user_name} · 📍 ${j.location} · 🕐 ${j.created_at.slice(0,10)}</div>
      <div class="desc">${j.description}</div>
      <div style="display:flex; justify-content:space-between; align-items:center">
        <span class="reward">💵 ${j.reward}</span>
        <span class="status">${j.status === 'open' ? '🟢 开放' : j.status}</span>
      </div>
      <div style="margin-top:8px; color:#667eea; font-size:0.85em">📞 ${j.contact}</div>
    </div>
  `).join('');
}

async function post_job() {
  const body = {
    title: document.getElementById('title').value,
    description: document.getElementById('desc').value,
    reward: document.getElementById('reward').value,
    location: document.getElementById('location').value,
    contact: document.getElementById('contact').value,
  };
  if (!body.title) return alert('请填写标题');
  await fetch('/api/jobs', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body) });
  document.querySelectorAll('.post-form input, .post-form textarea').forEach(e => e.value = '');
  load_jobs();
}
load_jobs();
</script>
</body>
</html>
"""

# ============ ROUTES ============

@app.route("/")
def home():
    quote, cite_t = random.choice(MOOD_QUOTES)
    return render_template_string(
        HOME_PAGE.replace("{{ quote }}", quote).replace("{{ cite_text }}", cite_t),
    )

@app.route("/register", methods=["GET", "POST"])
def register():
    emojis = ["🦞", "🌸", "🌙", "⭐", "🌊", "🔥", "🦋", "🌈", "🍀", "🎵", "🌺", "🐱"]
    if request.method == "GET":
        return render_template_string(REGISTER_PAGE, emojis=emojis)

    uid = str(uuid.uuid4())[:8]
    username = request.form["username"]
    display_name = request.form.get("display_name", username)
    avatar = request.form.get("avatar_emoji", "🦞")
    bio = request.form.get("bio", "")
    mood = request.form.get("mood", "neutral")

    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("""INSERT INTO users (id,username,display_name,avatar_emoji,bio,mood,created_at)
            VALUES (?,?,?,?,?,?,?)""",
            (uid, username, display_name, avatar, bio, mood, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        session["uid"] = uid
        session["username"] = username
        return f'<script>alert("欢迎，{username}！"); location.href="/chat";</script>'
    except Exception as e:
        conn.close()
        return f'<script>alert("用户名已存在！"); history.back();</script>'

@app.route("/chat")
def chat():
    uid = session.get("uid")
    if not uid:
        return '<script>location.href="/register";</script>'

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, emoji, personality, specialty FROM ai_companions")
    companions = c.fetchall()
    conn.close()

    username = session.get("username", "你")
    return render_template_string(CHAT_PAGE, companions=companions, username=username)

@app.route("/jobs")
def jobs():
    return render_template_string(JOBS_PAGE)

# ============ API ============

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.json
    msg = data.get("message", "")
    room = data.get("room", "ai_luna")
    username = data.get("username", "你")

    if room == "community":
        return jsonify({"emoji": "👥", "text": "社区聊天功能即将上线！先在 /jobs 发布机会，或继续和我（AI）聊聊 😊"})

    resp = ai_response(msg, "neutral", username)
    return jsonify(resp)

@app.route("/api/jobs", methods=["GET"])
def api_get_jobs():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, user_id, user_name, title, description, category, reward, location, contact, status, views, created_at FROM opportunities WHERE status='open' ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return jsonify([[{"id":r[0],"user_id":r[1],"user_name":r[2],"title":r[3],"description":r[4],"category":r[5],"reward":r[6],"location":r[7],"contact":r[8],"status":r[9],"views":r[10],"created_at":r[11]} for r in rows]])

@app.route("/api/jobs", methods=["POST"])
def api_post_job():
    data = request.json
    uid = session.get("uid") or "anonymous"
    uname = session.get("username") or "匿名用户"
    oid = str(uuid.uuid4())[:8]
    conn = get_db()
    c = conn.cursor()
    c.execute("""INSERT INTO opportunities (id,user_id,user_name,title,description,reward,location,contact,created_at)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (oid, uid, uname, data.get("title",""), data.get("description",""),
         data.get("reward",""), data.get("location","线上"),
         data.get("contact",""), datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "id": oid})

@app.route("/api/mood", methods=["POST"])
def api_mood():
    data = request.json
    uid = session.get("uid", "anon")
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET mood=?, mood_updated_at=? WHERE id=?", (data["mood"], datetime.now().isoformat(), uid))
    conn.commit()
    conn.close()
    tip = DAILY_MOOD_TIPS.get(data["mood"], DAILY_MOOD_TIPS["neutral"])
    return jsonify({"tip": tip})

# ============ MAIN ============
if __name__ == "__main__":
    init_db()
    print("🌟 HumanTogether MVP 启动中...")
    print("📍 访问：http://localhost:5000")
    socketio.run(app, host="0.0.0.0", port=5000, debug=False, allow_unsafe_werkzeug=True)
