#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sqlite3, uuid, random
from datetime import datetime, timedelta
from flask import Flask, request, session, jsonify, render_template, send_from_directory

app = Flask(__name__, template_folder="templates")
app.secret_key = "sgj2026warmv6"
app.config["JSON_AS_ASCII"] = False
DB = "sgj_warm.db"

# ─── 3D HOMEPAGE ─────────────────────────────
@app.route("/3d")
def index_3d():
    """共生境 3D warm metaverse homepage"""
    return send_from_directory("templates", "index3d.html")

@app.route("/home2d")
def home2d():
    """共生境 2D warm homepage — full template"""
    return render_template("index2d.html", title="共生境 · HumanTogether")

def sql(q, *a):
    d = sqlite3.connect(DB)
    d.execute("PRAGMA encoding='UTF-8'")
    cur = d.execute(q, a)
    cols = [x[0] for x in cur.description]
    rows = cur.fetchall()
    d.close()
    return cols, rows

def get_user(uid):
    if not uid: return None
    c, r = sql("SELECT * FROM users WHERE id=?", uid)
    return dict(zip(c, r[0])) if r else None

def get_companion(cid):
    c, r = sql("SELECT * FROM companions WHERE id=?", "global_" + cid)
    return dict(zip(c, r[0])) if r else None

def recent_msgs(uid, cid, limit=30):
    c, r = sql(
        "SELECT * FROM ai_messages WHERE user_id=? AND companion_id=? ORDER BY created_at ASC LIMIT ?",
        uid, cid, limit)
    return [dict(zip(c, x)) for x in r]

def ai_reply(uid, cid, user_msg, mood="neutral"):
    comp = get_companion(cid)
    cname = comp["companion_name"] if comp else "AI"
    emoji = comp["companion_emoji"] if comp else "?"
    msg = user_msg.lower()
    if any(w in msg for w in ["难过","伤心","sad","depressed"]): det = "sad"
    elif any(w in msg for w in ["焦虑","担心","anxious","worried"]): det = "anxious"
    elif any(w in msg for w in ["无聊","空虚","bored","lonely"]): det = "bored"
    elif any(w in msg for w in ["开心","高兴","happy","joy"]): det = "happy"
    else: det = mood
    _, tr = sql("SELECT content,emoji FROM tips WHERE mood=? ORDER BY RANDOM() LIMIT 1", det)
    tip = tr[0][1] + " " + tr[0][0] if tr else ""
    if any(w in msg for w in ["你是谁","who are you"]):
        reply = emoji + " 我是" + cname + "！" + (comp["personality"] if comp else "")
    elif any(w in msg for w in ["职业","job","career","工作","失业"]):
        reply = emoji + " 职业发展是大事！去 /opportunities 看看机会？"
    elif any(w in msg for w in ["help","帮","帮助","怎么","how"]):
        reply = "当然愿意帮忙！" + emoji + "\n\n可以帮你：\n💬 聊天倾诉\n🌙 情感支持\n💼 职业规划\n📚 技能学习\n🌿 放松减压"
    elif any(w in msg for w in ["谢谢","thanks","thank"]):
        reply = "不客气！" + emoji + "\n\n能帮到你我很开心 💛"
    elif det == "sad":
        reply = emoji + " 我感受到你现在很难过。\n\n" + tip + "\n\n慢慢来，我在这里陪着你 🤗"
    elif det == "anxious":
        reply = emoji + " 焦虑是正常的，我理解。\n\n试试深呼吸：吸气4秒，屏气7秒，呼气8秒 🌬️\n\n" + tip
    elif det == "bored":
        reply = "无聊的时候，正好是探索的好时机！" + emoji
    elif det == "happy":
        reply = "太棒了！" + emoji + " 你的快乐会传染给我的！🎉"
    elif any(w in msg for w in ["冥想","meditate","放松","relax"]):
        reply = "好的，一起放松一下吧。" + emoji + "\n\n🌿 请闭上眼睛，深呼吸...\n\n想象安静的森林，阳光洒落，微风轻拂...\n\n感受此刻的平静 🌿"
    else:
        opts = [
            "我听到了，" + cname + "在这里 👂 继续说吧，我在听",
            "嗯嗯，" + emoji + "有意思，告诉我更多 📖",
            "不管发生什么，这里永远欢迎你 🤗"
        ]
        reply = emoji + " " + random.choice(opts)
    if uid:
        now = datetime.now().isoformat()
        d = sqlite3.connect(DB)
        d.execute("INSERT INTO ai_messages VALUES (?,?,?,?,?,?,?)",
            (str(uuid.uuid4())[:12], uid, cid, "user", user_msg, det, now))
        d.execute("INSERT INTO ai_messages VALUES (?,?,?,?,?,?,?)",
            (str(uuid.uuid4())[:12], uid, cid, "assistant", reply, det, now))
        d.execute("UPDATE users SET mood=?, last_active=? WHERE id=?", (det, now, uid))
        d.commit()
        d.close()
    return reply, det

def page(html, user=None, active=""):
    u = user or {}
    return render_template("base.html",
        coin="{:.0f}".format(u.get("coin_balance", 0)),
        avatar=u.get("avatar_emoji", "😊"),
        is_vip=1 if u.get("is_vip") else 0,
        active=active,
        title="共生境 · HumanTogether",
        content=html)

# ── HOME ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    """共生境 2D warm homepage — rich standalone template"""
    return render_template("index2d.html", title="共生境 · HumanTogether")
    uid = session.get("user_id")
    user = get_user(uid)
    _, r = sql("SELECT COUNT(*) FROM users")
    total = r[0][0] if r else 0
    _, r2 = sql("SELECT COUNT(*) FROM opportunities WHERE status='open'")
    opcnt = r2[0][0] if r2 else 0
    _, dm = sql("SELECT content,author FROM daily_messages ORDER BY RANDOM() LIMIT 1")
    quote = dm[0][0] if dm else "每天都是新的开始 ✨"
    qath = dm[0][1] if dm else "共生境"
    if not user:
        cp = "".join([
            '<div class="companion-card" onclick="location.href=\'/register\'"><div class="emoji">' + e + '</div><div class="name">' + n + '</div><div class="type">' + p + '</div></div>'
            for e, n, p in [
                ("🌙","Luna","温柔倾听"),("🌊","Kai","冷静理性"),("⭐","Nova","积极激励"),
                ("🌿","Milo","平和佛系"),("📚","Sage","智慧导师")
            ]
        ])
        c = """
<div class="quote-box">
  <blockquote>""" + quote + """</blockquote>
  <cite>— """ + qath + """ 🌙</cite>
</div>
<div class="stats-row">
  <div class="stat-card"><div class="num">""" + str(total) + """</div><div class="label">入驻公民</div></div>
  <div class="stat-card"><div class="num">""" + str(opcnt) + """</div><div class="label">开放机会</div></div>
  <div class="stat-card"><div class="num">0</div><div class="label">已完成</div></div>
</div>
<div class="grid-3" style="margin-bottom:24px">
  <div class="card" style="text-align:center;cursor:pointer" onclick="location.href='/register'">
    <div style="font-size:36px;margin-bottom:10px">🌙</div>
    <div class="card-title" style="justify-content:center">AI暖心陪伴</div>
    <p style="color:var(--text2);font-size:12px;line-height:1.8;margin:8px 0">有记忆的AI伙伴，7×24小时倾听、共情、治愈</p>
    <div class="btn btn-primary" style="margin-top:12px">免费加入</div>
  </div>
  <div class="card" style="text-align:center;cursor:pointer" onclick="location.href='/opportunities'">
    <div style="font-size:36px;margin-bottom:10px">💼</div>
    <div class="card-title" style="justify-content:center">机会大厅</div>
    <p style="color:var(--text2);font-size:12px;line-height:1.8;margin:8px 0">找工作、找项目、找合作，免费发布</p>
    <div class="btn btn-secondary" style="margin-top:12px">去看看</div>
  </div>
  <div class="card" style="text-align:center;cursor:pointer" onclick="location.href='/community'">
    <div style="font-size:36px;margin-bottom:10px">🤝</div>
    <div class="card-title" style="justify-content:center">互助社区</div>
    <p style="color:var(--text2);font-size:12px;line-height:1.8;margin:8px 0">真人互帮互助，扩大人脉</p>
    <div class="btn btn-secondary" style="margin-top:12px">加入社区</div>
  </div>
</div>
<div class="section-head"><div class="section-num">AI伙伴</div><div><div class="section-title">5种性格的AI伙伴</div></div></div>
<div class="grid-3" style="margin-bottom:20px">""" + cp + """</div>
<div class="section-head"><div class="section-num">✓</div><div><div class="section-title">平台特色</div></div></div>
<div class="grid-2">
  <div class="card"><div class="card-title">🤖 有记忆的AI伙伴</div>
    <p style="color:var(--text2);font-size:12px;line-height:1.9">Luna、Kai、Nova、Milo、Sage——5种不同性格的AI伙伴，会记住你的故事，理解你的情绪。</p>
  </div>
  <div class="card"><div class="card-title">💼 真实的机会</div>
    <p style="color:var(--text2);font-size:12px;line-height:1.9">工作、项目、合作——免费发布，直接联系，没有中间商。</p>
  </div>
</div>"""
        return page(c, None, "home")
    companions_html = "".join([
        '<div class="companion-card" onclick="location.href=\'/chat?companion=' + cid + '\'"><div class="emoji">' + e + '</div><div class="name">' + n + '</div><div class="type">' + p + '</div></div>'
        for cid, e, n, p in [
            ("luna","🌙","Luna","温柔倾听型"),("kai","🌊","Kai","冷静理性型"),
            ("nova","⭐","Nova","积极激励型"),("milo","🌿","Milo","平和佛系型"),
            ("sage","📚","Sage","智慧导师型")
        ]
    ])
    c = """
<div class="profile-header" style="margin-bottom:20px">
  <div class="profile-avatar">""" + user.get("avatar_emoji","") + """</div>
  <div class="profile-name">""" + (user.get("display_name") or user.get("username","")) + """</div>
  <div class="profile-username">@""" + user.get("username","") + """ · 连续签到 """ + str(user.get("daily_streak",0)) + """ 天</div>
</div>
<div class="quote-box">
  <blockquote>""" + quote + """</blockquote>
  <cite>— """ + qath + """ 🌙</cite>
</div>
<div class="section-head"><div class="section-num">✓</div><div><div class="section-title">每日签到 · 记录心情</div></div></div>
<div class="card">
  <p style="color:var(--text2);font-size:12px;margin-bottom:12px">今天的情绪怎么样？签到获得10共币 🪙</p>
  <div class="mood-selector">
    <form action="/checkin" method="post" style="display:inline"><button name="mood" value="happy" class="mood-chip">😊 开心</button></form>
    <form action="/checkin" method="post" style="display:inline"><button name="mood" value="neutral" class="mood-chip">😐 一般</button></form>
    <form action="/checkin" method="post" style="display:inline"><button name="mood" value="sad" class="mood-chip">😢 难过</button></form>
    <form action="/checkin" method="post" style="display:inline"><button name="mood" value="anxious" class="mood-chip">😰 焦虑</button></form>
  </div>
</div>
<div class="section-head"><div class="section-num">🌙</div><div><div class="section-title">找你的AI伙伴聊聊</div></div></div>
<div class="grid-3" style="margin-bottom:20px">""" + companions_html + """</div>
<div class="section-head"><div class="section-num">💼</div><div><div class="section-title">最新机会</div></div></div>
<div id="recent_opp"><div class="empty">加载中...</div></div>
<script>
(function() {
  fetch('/api/opportunities?limit=3')
    .then(function(r) { return r.json(); })
    .then(function(data) {
      var el = document.getElementById('recent_opp');
      if (!data.length) { el.innerHTML = '<div class="empty">暂无机会</div>'; return; }
      el.innerHTML = data.map(function(o) {
        var t = o.created_at ? o.created_at.slice(0,10) : '';
        return '<div class="opp-card" style="margin-bottom:10px;cursor:pointer" onclick="location.href=\'/opportunities\'"><div class="title">' + o.title + '</div><div class="meta">👤 ' + (o.user_name||'匿名') + ' · 📍 ' + (o.location||'线上') + ' · 🕐 ' + t + '</div><div class="reward">' + (o.reward||'面议') + '</div></div>';
      }).join('');
    })
    .catch(function() {});
})();
</script>"""
    return page(c, user, "home")

# ── REGISTER ─────────────────────────────────────────────────────────────────
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "GET":
        avs = "".join([
            '<div class="avatar-opt" data-val="' + e + '">' + e + '</div>'
            for e in ["😊","🌙","⭐","🌊","🌿","📚","🦋","🌸","🌈","🍀","🎵","🌺","🐱","🦄","👾","🤖"]
        ])
        c = '''
<div style="max-width:480px;margin:0 auto;padding-top:32px">
  <div class="card">
    <div class="card-title">🌙 加入共生境</div>
    <p style="color:var(--text2);font-size:12px;margin-bottom:16px">创建你的专属虚拟身份，开始AI伙伴之旅</p>
    <form action="/register" method="post">
      <label style="color:var(--text2);font-size:12px;display:block;margin-bottom:6px">选择头像</label>
      <input type="hidden" name="avatar" id="avatar_val" value="😊">
      <div class="avatar-grid" style="margin-bottom:14px">''' + avs + '''</div>
      <input name="username" class="input" placeholder="用户名（登录用，唯一）" required maxlength="20" style="margin-top:8px">
      <input name="display_name" class="input" placeholder="显示名称（别人看到的名字）" maxlength="20">
      <input name="bio" class="input" placeholder="介绍一下自己（可选）" maxlength="200">
      <button type="submit" class="btn btn-primary" style="width:100%;padding:13px;margin-top:8px">🌙 加入共生境</button>
    </form>
  </div>
</div>
<script>
document.querySelectorAll('.avatar-opt').forEach(function(el) {
  el.addEventListener('click', function() {
    document.querySelectorAll('.avatar-opt').forEach(function(s) { s.classList.remove('selected'); });
    el.classList.add('selected');
    document.getElementById('avatar_val').value = el.dataset.val;
  });
});
document.querySelector('.avatar-opt').click();
</script>'''
        return page(c, None)
    uid = str(uuid.uuid4())[:12]
    username = request.form.get("username","").strip()
    display_name = request.form.get("display_name", username)
    avatar = request.form.get("avatar", "😊")
    bio = request.form.get("bio", "")
    now = datetime.now().isoformat()
    try:
        d = sqlite3.connect(DB)
        d.execute("INSERT INTO users (id,username,display_name,avatar_emoji,bio,created_at,last_active) VALUES (?,?,?,?,?,?,?)",
                  (uid, username, display_name, avatar, bio, now, now))
        d.commit()
        session["user_id"] = uid
        d.close()
        return '<script>location.href="/chat?companion=luna"</script>'
    except:
        return '<script>alert("用户名已存在！");history.back();</script>'

# ── CHAT ──────────────────────────────────────────────────────────────────────
@app.route("/chat")
def chat():
    uid = session.get("user_id")
    if not uid: return '<script>location.href="/register"</script>'
    user = get_user(uid)
    cid = request.args.get("companion", user.get("ai_companion","luna") if user else "luna")
    comp = get_companion(cid) or get_companion("luna")
    cname = comp["companion_name"]
    emoji = comp["companion_emoji"]
    greeting = ""
    if comp and comp.get("memory"):
        parts = comp["memory"].split("\n")
        greeting = emoji + " 你好！我是" + cname + "，有什么想和我聊的吗？"
    else:
        greeting = emoji + " 你好！我是" + cname + "，有什么想和我聊的吗？"
    msgs = recent_msgs(uid, cid, 30)
    now_str = datetime.now().strftime("%H:%M")
    msgs_html = ""
    for m in msgs:
        cls = "msg-user" if m["role"] == "user" else "msg-ai"
        sender = "你" if m["role"] == "user" else cname
        em = "" if m["role"] == "user" else emoji
        t = m["created_at"][:16] if m.get("created_at") else ""
        msgs_html += '<div class="msg-bubble ' + cls + '"><div class="msg-meta">' + em + ' ' + sender + '</div>' + m["content"] + '<div class="msg-time">' + t + '</div></div>'
    if not msgs:
        msgs_html = '<div class="msg-bubble msg-ai"><div class="msg-meta">' + emoji + ' ' + cname + '</div>' + greeting + '<div class="msg-time">' + now_str + '</div></div>'
    companions_html = "".join([
        '<div class="companion-card ' + ("active" if c == cid else "") + '" onclick="location.href=\'/chat?companion=' + c + '\'"><div style="font-size:24px">' + e + '</div><div class="name">' + n + '</div></div>'
        for c, e, n in [("luna","🌙","Luna"),("kai","🌊","Kai"),("nova","⭐","Nova"),("milo","🌿","Milo"),("sage","📚","Sage")]
    ])
    quick = "".join([
        '<span class="tag" onclick="quick(\'' + t + '\')">' + l + '</span>'
        for t, l in [
            ("我最近有点焦虑怎么办","😰 焦虑"),
            ("推荐个工作机会？","💼 工作"),
            ("我想学编程，从哪开始？","💻 学编程"),
            ("陪我冥想一下吧","🌿 冥想"),
            ("今天开心的事：","😊 分享开心")
        ]
    ])
    js = """
<script>
var emoji = '""" + emoji + """';
var cname = '""" + cname + """';
function quick(t) { document.getElementById('msg_input').value = t; document.getElementById('msg_input').focus(); }
async function send_msg() {
  var inp = document.getElementById('msg_input');
  var msg = inp.value.trim();
  if (!msg) return;
  var area = document.getElementById('chat_area');
  var now = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
  area.innerHTML += '<div class="msg-bubble msg-user"><div class="msg-meta">你</div>' + msg + '<div class="msg-time">' + now + '</div></div>';
  inp.value = '';
  area.scrollTop = area.scrollHeight;
  var cid = document.getElementById('chat_cid').value;
  var res = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: msg, companion: cid }) });
  var d = await res.json();
  area.innerHTML += '<div class="msg-bubble msg-ai"><div class="msg-meta">' + emoji + ' ' + cname + '</div>' + d.text + '<div class="msg-time">' + now + '</div></div>';
  area.scrollTop = area.scrollHeight;
}
document.getElementById('msg_input').addEventListener('keypress', function(e) { if (e.key === 'Enter') { e.preventDefault(); send_msg(); } });
document.getElementById('msg_input').focus();
</script>"""
    c = """
<div class="grid-2" style="gap:16px;align-items:start">
  <div class="card">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
      <div style="display:flex;align-items:center;gap:10px">
        <span style="font-size:24px">""" + emoji + """</span>
        <div>
          <div style="font-size:15px;font-weight:800">""" + cname + """</div>
          <div style="font-size:10px;color:var(--text3)">""" + (comp.get("personality","")[:18] if comp else "") + """</div>
        </div>
      </div>
      <span class="tag" onclick="location.href='/profile'">👤 我的</span>
    </div>
    <div class="chat-area" id="chat_area">""" + msgs_html + """</div>
    <input type="hidden" id="chat_cid" value=\"""" + cid + """\">
    <div class="input-row">
      <input id="msg_input" class="input" placeholder=\"和""" + cname + """聊聊...\" autocomplete="off" style="flex:1">
      <button class="btn btn-primary" onclick="send_msg()">发送</button>
    </div>
  </div>
  <div>
    <div class="card" style="margin-bottom:16px">
      <div class="card-title">🌙 AI伙伴</div>
      <div class="grid-3" style="gap:8px;margin-bottom:14px">""" + companions_html + """</div>
      <hr>
      <div class="card-title">💡 快速话题</div>
      <div style="display:flex;flex-wrap:wrap;gap:6px">""" + quick + """</div>
    </div>
    <div class="card">
      <div class="card-title">💬 小提示</div>
      <p style="color:var(--text2);font-size:11px;line-height:2">
        🤖 和AI聊得越多，它越懂你<br>
        📅 签到领共币，解锁更多功能<br>
        💼 去机会大厅找真实工作机会
      </p>
    </div>
  </div>
</div>""" + js
    return page(c, user, "chat")

@app.route("/api/chat", methods=["POST"])
def api_chat():
    uid = session.get("user_id")
    data = request.json
    msg = data.get("message","")
    cid = data.get("companion","luna")
    if not msg: return jsonify({"text":"说点什么吧...","mood":"neutral"})
    user = get_user(uid)
    mood = user.get("mood","neutral") if user else "neutral"
    reply, det = ai_reply(uid, cid, msg, mood)
    return jsonify({"text":reply,"mood":det})

# ── OPPORTUNITIES ─────────────────────────────────────────────────────────────
@app.route("/opportunities")
def opportunities():
    uid = session.get("user_id")
    user = get_user(uid)
    cat = request.args.get("category","all")
    if cat == "all":
        _, rows = sql("SELECT * FROM opportunities WHERE status='open' ORDER BY created_at DESC LIMIT 30")
    else:
        _, rows = sql("SELECT * FROM opportunities WHERE status='open' AND category=? ORDER BY created_at DESC LIMIT 30", cat)
    d2 = sqlite3.connect(DB)
    d2.execute("PRAGMA encoding='UTF-8'")
    opp_cols = [x[0] for x in d2.execute("SELECT * FROM opportunities LIMIT 1").description]
    d2.close()
    opps = [dict(zip(opp_cols, r)) for r in rows]
    opps_html = ""
    for o in opps:
        tags = "".join(['<span class="tag">' + t + '</span>' for t in (o.get("tags","") or "").split(",") if t][:3])
        opps_html += '<div class="opp-card">'
        opps_html += '<div style="display:flex;justify-content:space-between;align-items:start">'
        opps_html += '<div class="title">' + o["title"] + '</div>'
        opps_html += '<span class="badge b-open">🟢 开放</span></div>'
        opps_html += '<div class="meta">' + (o.get("user_avatar","") or "") + " " + (o.get("user_name","匿名") or "匿名") + " · 📍 " + (o.get("location","线上") or "线上") + " · 🕐 " + str(o.get("created_at",""))[:10] + '</div>'
        opps_html += '<div class="desc">' + str(o.get("description","") or "")[:180] + '</div>'
        if tags: opps_html += tags
        opps_html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-top:10px">'
        opps_html += '<div class="reward">' + (o.get("reward","") or "面议") + '</div>'
        opps_html += '<button class="btn btn-secondary" onclick="apply_opp(\'' + o["id"] + '\')">📩 申请</button>'
        opps_html += '</div></div>'
    if not opps_html:
        opps_html = '<div class="empty">暂无这类机会，<a href="/post_opportunity">发布一个</a>吧！</div>'
    cats = [("all","全部"),("工作","工作"),("项目","项目"),("合作","合作"),("培训","培训"),("志愿者","志愿者"),("其他","其他")]
    cat_btns = "".join([
        '<a href="/opportunities?category=' + k + '" class="tag ' + ("active" if (k=="all" and cat=="all") or k==cat else "") + '" style="padding:5px 14px">' + v + '</a>'
        for k, v in cats
    ])
    c = ('<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">'
         '<div style="font-size:16px;font-weight:800">💼 机会大厅</div>'
         '<a href="/post_opportunity" class="btn btn-primary">+ 发布机会</a>'
         '</div>'
         '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px">' + cat_btns + '</div>'
         + opps_html + '''
<script>
function apply_opp(id) {
  var msg = prompt('给发布方留言（可选）：') || '';
  fetch('/api/apply', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ opportunity_id: id, message: msg }) })
    .then(function(r) { return r.json(); })
    .then(function(d) { if (d.success) alert('✅ 申请成功！'); else alert(d.error || '请先登录'); });
}
</script>''')
    return page(c, user, "op")

@app.route("/post_opportunity", methods=["GET","POST"])
def post_opportunity():
    uid = session.get("user_id")
    if not uid: return '<script>location.href="/register"</script>'
    if request.method == "GET":
        c = '''<div style="max-width:560px;margin:0 auto;padding-top:24px"><div class="card"><div class="card-title">💼 发布新机会</div>
<form action="/post_opportunity" method="post">
<input name="title" class="input" placeholder="标题（如：招募Python兼职开发者）" required maxlength="60" style="margin-top:8px">
<textarea name="description" class="input" placeholder="详细描述：要求、方式、截止时间..." required style="min-height:100px"></textarea>
<select name="category" class="input"><option value="工作">💼 工作</option><option value="项目">📁 项目</option><option value="合作">🤝 合作</option><option value="培训">🎓 培训</option><option value="志愿者">❤️ 志愿者</option><option value="其他">📌 其他</option></select>
<input name="reward" class="input" placeholder="报酬（如：¥500-2000 · 面议）" style="margin-top:8px">
<input name="location" class="input" placeholder="地点" value="线上">
<input name="contact" class="input" placeholder="联系方式（微信/TG/邮箱）" required>
<button type="submit" class="btn btn-primary" style="width:100%;padding:13px;margin-top:8px">🚀 发布机会</button>
</form></div></div>'''
        return page(c, get_user(uid))
    user = get_user(uid)
    oid = str(uuid.uuid4())[:12]
    now = datetime.now().isoformat()
    d = sqlite3.connect(DB)
    d.execute("""INSERT INTO opportunities (id,user_id,user_name,user_avatar,title,description,category,reward,location,contact,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (oid, uid, user.get("display_name", user.get("username","匿名")),
         user.get("avatar_emoji",""),
         request.form.get("title",""), request.form.get("description",""),
         request.form.get("category","其他"), request.form.get("reward",""),
         request.form.get("location","线上"), request.form.get("contact",""), now))
    d.commit()
    d.close()
    return '<script>alert("✅ 机会发布成功！");location.href="/opportunities"</script>'

@app.route("/api/opportunities")
def api_opportunities():
    limit = int(request.args.get("limit", 20))
    d = sqlite3.connect(DB)
    d.execute("PRAGMA encoding='UTF-8'")
    cur = d.execute(
        "SELECT id,title,description,category,reward,location,user_name,user_avatar,created_at "
        "FROM opportunities WHERE status='open' ORDER BY created_at DESC LIMIT ?", (limit,))
    cols = [x[0] for x in cur.description]
    rows = cur.fetchall()
    d.close()
    return jsonify([dict(zip(cols, r)) for r in rows])

@app.route("/api/apply", methods=["POST"])
def api_apply():
    uid = session.get("user_id")
    if not uid: return jsonify({"success":False,"error":"请先登录"})
    data = request.json
    oid = data.get("opportunity_id","")
    msg = data.get("message","")
    user = get_user(uid)
    aid = str(uuid.uuid4())[:12]
    now = datetime.now().isoformat()
    d = sqlite3.connect(DB)
    d.execute("INSERT INTO applications VALUES (?,?,?,?,?,?,?)",
        (aid, oid, uid, user.get("display_name",""), user.get("avatar_emoji",""), msg, now))
    d.execute("UPDATE opportunities SET apply_count=apply_count+1 WHERE id=?", (oid,))
    d.commit()
    d.close()
    return jsonify({"success":True})

# ── COMMUNITY ─────────────────────────────────────────────────────────────────
@app.route("/community")
def community():
    uid = session.get("user_id")
    user = get_user(uid)
    _, r = sql("SELECT COUNT(*) FROM users")
    total = r[0][0] if r else 0
    _, member_rows = sql("SELECT avatar_emoji,display_name,username,daily_streak FROM users ORDER BY daily_streak DESC LIMIT 15")
    members = "".join([
        '<div class="member-item"><span class="emoji">' + r[0] + '</span><div><div class="name">' + (r[1] or r[2] or "") + '</div><div class="streak">🔥 连续' + str(r[3]) + '天签到</div></div></div>'
        for r in member_rows
    ])
    c = ('<div class="grid-2" style="gap:16px">'
         '<div class="card"><div class="card-title">👥 活跃公民 ⭐</div>'
         '<p style="color:var(--text3);font-size:11px;margin-bottom:14px">已有 ' + str(total) + ' 位公民入驻共生境</p>'
         + members + '</div>'
         '<div class="card"><div class="card-title">🤝 帮助大厅</div>'
         '<p style="color:var(--text2);font-size:12px;line-height:1.9;margin-bottom:14px">在「机会大厅」发布求助或合作需求，让社区成员来帮你。这里是真实互助的起点。</p>'
         '<div style="text-align:center"><a href="/opportunities" class="btn btn-primary">💼 去看看机会</a></div>'
         '</div></div>')
    return page(c, user, "comm")

# ── PROFILE ───────────────────────────────────────────────────────────────────
@app.route("/profile")
def profile():
    uid = session.get("user_id")
    if not uid: return '<script>location.href="/register"</script>'
    user = get_user(uid)
    _, mc = sql("SELECT COUNT(*) FROM ai_messages WHERE user_id=?", uid)
    _, oc = sql("SELECT COUNT(*) FROM opportunities WHERE user_id=?", uid)
    _, ac = sql("SELECT COUNT(*) FROM applications WHERE user_id=?", uid)
    chat_count = mc[0][0] if mc else 0
    my_op = oc[0][0] if oc else 0
    my_apply = ac[0][0] if ac else 0
    mood_em = {"happy":"😊","neutral":"😐","sad":"😢","anxious":"😰","bored":"😑"}.get(user.get("mood",""),"😐")
    comp_names = {"luna":"🌙 Luna","kai":"🌊 Kai","nova":"⭐ Nova","milo":"🌿 Milo","sage":"📚 Sage"}
    my_comp = comp_names.get(user.get("ai_companion",""),"🌙 Luna")
    vip_chip = "<span class='vip-chip'>⭐ VIP会员</span>" if user.get("is_vip") else ""
    c = ('<div class="profile-header">'
         '<div class="profile-avatar">' + user.get("avatar_emoji","") + '</div>'
         '<div class="profile-name">' + (user.get("display_name") or user.get("username","")) + '</div>'
         '<div class="profile-username">@' + user.get("username","") + '</div>'
         '<div class="profile-bio">' + (user.get("bio","") or "") + '</div>'
         '<div style="margin-top:12px;display:flex;gap:8px;justify-content:center;flex-wrap:wrap">'
         '<span class="tag">' + mood_em + ' ' + user.get("mood","neutral") + '</span>'
         '<span class="tag">🔥 连续签到 ' + str(user.get("daily_streak",0)) + ' 天</span>'
         + vip_chip + '</div></div>'
         '<div class="stats-row">'
         '<div class="stat-card"><div class="num">' + str(chat_count) + '</div><div class="label">AI对话数</div></div>'
         '<div class="stat-card"><div class="num">' + str(my_op) + '</div><div class="label">发布机会</div></div>'
         '<div class="stat-card"><div class="num">' + str(my_apply) + '</div><div class="label">申请次数</div></div>'
         '<div class="stat-card"><div class="num">' + "{:.0f}".format(user.get("coin_balance",0)) + '</div><div class="label">共币余额</div></div>'
         '</div>'
         '<div class="section-head"><div class="section-num">🌙</div><div><div class="section-title">我的AI伙伴</div></div></div>'
         '<div class="card"><div style="display:flex;align-items:center;gap:14px"><span style="font-size:28px">' + my_comp[:2] + '</span><div><div style="font-size:14px;font-weight:700">' + my_comp[2:] + '</div><a href="/chat" style="font-size:12px">去和TA聊天 →</a></div></div></div>'
         '<div class="section-head"><div class="section-num">📋</div><div><div class="section-title">快捷操作</div></div></div>'
         '<div class="card">'
         '<a href="/opportunities" style="display:block;padding:12px 0;border-bottom:1px solid var(--border);color:var(--text)">💼 查看机会大厅</a>'
         '<a href="/post_opportunity" style="display:block;padding:12px 0;border-bottom:1px solid var(--border);color:var(--text)">🚀 发布新机会</a>'
         '<a href="/community" style="display:block;padding:12px 0;color:var(--text)">👥 互助社区</a>'
         '</div>')
    return page(c, user, "profile")

@app.route("/checkin", methods=["POST"])
def checkin():
    uid = session.get("user_id")
    if not uid: return '<script>location.href="/register"</script>'
    mood = request.form.get("mood","neutral")
    d = sqlite3.connect(DB)
    today = datetime.now().strftime("%Y-%m-%d")
    cur = d.execute("SELECT id FROM checkins WHERE user_id=? AND date=?", (uid, today))
    if cur.fetchone():
        d.close()
        return '<script>alert("今天已签到！");location.href="/"</script>'
    d.execute("INSERT INTO checkins VALUES (?,?,?,?,?,?)",
              (str(uuid.uuid4())[:12], uid, today, mood, "", datetime.now().isoformat()))
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    prev = d.execute("SELECT id FROM checkins WHERE user_id=? AND date=?", (uid, yesterday)).fetchone()
    streak = 1
    if prev:
        u = get_user(uid)
        streak = (u.get("daily_streak",0) + 1) if u else 1
    d.execute("UPDATE users SET daily_streak=?,last_checkin=?,coin_balance=coin_balance+10 WHERE id=?",
              (streak, today, uid))
    d.commit()
    d.close()
    return '<script>alert("✅ 签到成功！获得10共币 🪙\\n连续签到' + str(streak) + '天！");location.href="/"</script>'

@app.route("/logout")
def logout():
    session.clear()
    return '<script>location.href="/"</script>'

# ── INIT DB ──────────────────────────────────────────────────────────────────
def init_db():
    d = sqlite3.connect(DB)
    d.execute("PRAGMA encoding='UTF-8'")
    c = d.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, username TEXT UNIQUE, display_name TEXT,
            avatar_emoji TEXT DEFAULT '😊', bio TEXT DEFAULT '', mood TEXT DEFAULT 'neutral',
            skill_tags TEXT DEFAULT '', is_vip INTEGER DEFAULT 0, coin_balance REAL DEFAULT 0.0,
            daily_streak INTEGER DEFAULT 0, last_checkin TEXT, created_at TEXT, last_active TEXT, ai_companion TEXT DEFAULT 'luna');
        CREATE TABLE IF NOT EXISTS companions (id TEXT PRIMARY KEY, companion_id TEXT, companion_name TEXT,
            companion_emoji TEXT, personality TEXT, memory TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS ai_messages (id TEXT PRIMARY KEY, user_id TEXT, companion_id TEXT, role TEXT,
            content TEXT, mood_tag TEXT DEFAULT '', created_at TEXT);
        CREATE TABLE IF NOT EXISTS opportunities (id TEXT PRIMARY KEY, user_id TEXT, user_name TEXT, user_avatar TEXT,
            title TEXT, description TEXT, category TEXT DEFAULT '其他', reward TEXT DEFAULT '',
            location TEXT DEFAULT '线上', contact TEXT, status TEXT DEFAULT 'open', view_count INTEGER DEFAULT 0,
            apply_count INTEGER DEFAULT 0, tags TEXT DEFAULT '', urgency TEXT DEFAULT 'normal', created_at TEXT);
        CREATE TABLE IF NOT EXISTS applications (id TEXT PRIMARY KEY, opportunity_id TEXT, user_id TEXT,
            user_name TEXT, user_avatar TEXT, message TEXT, status TEXT DEFAULT 'pending', created_at TEXT);
        CREATE TABLE IF NOT EXISTS daily_messages (id TEXT PRIMARY KEY, content TEXT, author TEXT, category TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS checkins (id TEXT PRIMARY KEY, user_id TEXT, date TEXT, mood TEXT, note TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS tips (id INTEGER PRIMARY KEY, mood TEXT, content TEXT, emoji TEXT);
    """)
    companions = [
        ("luna","🌙","Luna","温柔倾听型","我在这里陪你，无论开心还是难过。记住，你不是一个人。","情感陪伴"),
        ("kai","🌊","Kai","冷静理性型","我擅长帮你理清思路，找到职业方向。","职业规划"),
        ("nova","⭐","Nova","积极激励型","我相信你的潜力！每个人都有独特的价值。","生活激励"),
        ("milo","🌿","Milo","平和佛系型","慢下来，深呼吸，不必焦虑。","放松减压"),
        ("sage","📚","Sage","智慧导师型","知识就是力量，我可以教你各种技能。","技能培训"),
    ]
    for cid, emo, name, personality, greeting, specialty in companions:
        c.execute("""INSERT OR IGNORE INTO companions VALUES (?,?,?,?,?,?)""",
            ("global_" + cid, cid, name, emo, personality, "专业：" + specialty + "\n开场白：" + greeting))
    tips = [
        (None,"sad","难过的时候，允许自己哭一下，然后抱抱自己 🤗","🌊"),
        (None,"sad","找人倾诉很重要，不要一个人扛着 💬","🤝"),
        (None,"anxious","焦虑时，试试4-7-8呼吸法：吸气4秒，屏气7秒，呼气8秒 🌬️","🌿"),
        (None,"anxious","把焦虑的事情写下来，往往写着写着就有了答案 ✍️","📝"),
        (None,"bored","无聊是探索的好时机，今天想学点什么呢？ 📚","⭐"),
        (None,"happy","你的好心情会传染给别人，分享你的快乐吧！ 🎉","☀️"),
        (None,"happy","记录今天让你开心的事，以后回头看会很温暖 📖","🌸"),
        (None,"neutral","每天喝够8杯水，身体好心情也会好 💧","🌿"),
        (None,"neutral","散散步，晒晒太阳，自然是最好的治愈 🌞","🌳"),
    ]
    c.executemany("INSERT OR IGNORE INTO tips VALUES (?,?,?,?)", tips)
    daily = [
        ("🌅","今天的不开心就止于此吧，明天依然光芒万丈 ✨"),
        ("💪","你不需要很厉害才能开始，你需要开始才能很厉害 🚀"),
        ("🌱","生活总会给你另一个机会，另一个开始 🌱"),
        ("🧠","照顾好自己的心灵，它决定了你是谁 🧠"),
        ("🤝","你不是一个人，我们都在这里陪着你 🤝"),
        ("🌙","今天辛苦了，明天又是新的一天 🌙"),
        ("💎","你的价值不取决于别人的认可，你本来就值得 💎"),
        ("🌸","累了就休息，没人是完美的 🌸"),
        ("🎯","每天进步一点点，一年就是巨大的跨越 🎯"),
        ("☀️","阳光总在风雨后，你比你想象的更坚强 ☀️"),
    ]
    for e, content in daily:
        c.execute("INSERT OR IGNORE INTO daily_messages VALUES (?,?,?,?,?)",
                  (str(uuid.uuid4())[:8], content, "共生境", "encouragement", datetime.now().isoformat()))
    d.commit()
    d.close()
    print("OK init " + DB)

if __name__ == "__main__":
    init_db()
    print("🌙 共生境 2D Warm Edition 启动")
    print("📍 http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
