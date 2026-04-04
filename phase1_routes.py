# Phase 1 Routes for 共生境

def register_phase1_routes(app, session, get_user, get_companion, sql, sqlite3, DB, jsonify, request, datetime, APP_START, max, uuid):
    from flask import render_template

    @app.route("/companion/<name>")
    def companion_detail(name):
        uid = session.get("user_id")
        user = get_user(uid)
        comp = get_companion(name)
        if not comp:
            comp = get_companion("luna")
            name = "luna"
        return render_template("companion_detail.html",
            companion_name=comp["companion_name"],
            companion_emoji=comp["companion_emoji"],
            companion_personality=comp["personality"])

    @app.route("/room/<name>")
    def companion_room(name):
        uid = session.get("user_id") or "guest"
        user = get_user(uid)
        comp = get_companion(name)
        if not comp:
            comp = get_companion("luna")
            name = "luna"
        return render_template("companion_room.html",
            companion_name=comp["companion_name"],
            companion_emoji=comp["companion_emoji"],
            companion_id=name,
            user_id=uid or "guest")

    @app.route("/room3d/<name>")
    def companion_3d_room(name):
        uid = session.get("user_id") or "guest"
        user = get_user(uid)
        comp = get_companion(name)
        if not comp:
            comp = get_companion("luna")
            name = "luna"
        # Get color config from companion_manager
        try:
            from companion_manager import COMPANION_INFO
            info = COMPANION_INFO.get(name, COMPANION_INFO["luna"])
            room_bg = '#{:06x}'.format(info.get("room_color", 0xFFF5F0))
            accent_color = '#{:06x}'.format(info.get("accent", 0xFFB6C1))
            wall_color = '#{:06x}'.format(info.get("wall", 0xFFE4E1))
            floor_color = '#{:06x}'.format(info.get("floor", 0xE8D5C4))
            companion_greeting = {
                "luna": "欢迎来我的房间～ 坐吧，想聊什么？🌙",
                "kai":  "这里很舒服，进来坐吧。🌊",
                "nova": "嘿！正好一起做点有趣的事～ ⭐",
                "milo": "来啦，随便坐，当自己家 🌿",
                "sage": "欢迎，书架上有喜欢的可以拿来看。📚",
            }.get(name, "欢迎！")
        except Exception:
            room_bg = "#FFF5F0"; accent_color = "#FFB6C1"; wall_color = "#FFE4E1"; floor_color = "#E8D5C4"; companion_greeting = "欢迎！"
        return render_template("companion_3d_room.html",
            companion_name=comp["companion_name"],
            companion_emoji=comp["companion_emoji"],
            companion_id=name,
            user_id=uid or "guest",
            room_bg=room_bg,
            accent_color=accent_color,
            wall_color=wall_color,
            floor_color=floor_color,
            companion_greeting=companion_greeting)

    @app.route("/shop")
    def shop_page():
        uid = session.get("user_id")
        if not uid:
            return '<script>location.href="/register"</script>'
        user = get_user(uid)
        return render_template("shop.html", user=user)

    @app.route("/api/buy", methods=["POST"])
    def api_buy():
        uid = session.get("user_id")
        if not uid:
            return jsonify({"success": False, "error": "请先登录"})
        data = request.json
        item_id = data.get("item_id")
        companion = data.get("companion", "luna")
        user = get_user(uid)
        coins = user.get("coin_balance", 0) if user else 0
        _, items = sql("SELECT id, name, price, item_type FROM shop_items WHERE id=?", item_id)
        if not items:
            return jsonify({"success": False, "error": "物品不存在"})
        item = items[0]
        price = item[2]
        if coins < price:
            return jsonify({"success": False, "error": "共币不足！需要 " + str(price) + " 共币"})
        d = sqlite3.connect(DB)
        d.execute("UPDATE users SET coin_balance = coin_balance - ? WHERE id=?", (price, uid))
        if item[3] == "furniture":
            d.execute("INSERT INTO user_room_items (user_id, companion_id, shop_item_id) VALUES (?,?,?)", (uid, companion, item_id))
        else:
            d.execute("INSERT INTO user_companion_outfits (user_id, companion_id, shop_item_id, equipped) VALUES (?,?,?,1)", (uid, companion, item_id))
        intimacy_gain = max(5, int(price / 5))
        d.execute("UPDATE user_companion_stats SET gifts_given=gifts_given+1, intimacy=intimacy+? WHERE user_id=? AND companion_id=?", (intimacy_gain, uid, companion))
        d.commit()
        d.close()
        _, cr = sql("SELECT companion_name FROM companions WHERE companion_id=?", companion)
        cname = cr[0][0].capitalize() if cr else companion.capitalize()
        return jsonify({"success": True, "companion": companion, "companion_name": cname, "intimacy_gain": intimacy_gain})

    @app.route("/api/memories/<companion>")
    def api_memories(companion):
        uid = session.get("user_id")
        if not uid:
            return jsonify({"items": []})
        from phase1_helpers import get_memories as gm
        return jsonify({"items": gm(uid, companion, 10)})

    @app.route("/api/activities/<companion>")
    def api_activities(companion):
        _, rows = sql("SELECT activity, detail, started_at FROM ai_activities WHERE companion_id=? ORDER BY started_at DESC LIMIT 10", companion)
        return jsonify({"items": [{"activity": r[0], "detail": r[1], "started_at": r[2]} for r in rows]})

    @app.route("/api/intimacy/<companion>")
    def api_intimacy(companion):
        uid = session.get("user_id")
        if not uid:
            return jsonify({"intimacy": 0, "total_chats": 0, "total_messages": 0, "gifts_given": 0})
        _, rows = sql("SELECT intimacy, total_chats, total_messages, gifts_given FROM user_companion_stats WHERE user_id=? AND companion_id=?", uid, companion)
        if rows:
            return jsonify({"companion_id": companion, "intimacy": rows[0][0], "total_chats": rows[0][1], "total_messages": rows[0][2], "gifts_given": rows[0][3]})
        return jsonify({"companion_id": companion, "intimacy": 0, "total_chats": 0, "total_messages": 0, "gifts_given": 0})

    @app.route("/api/shop")
    def api_shop():
        uid = session.get("user_id")
        intimacy = {}
        if uid:
            for cid in ["luna", "kai", "nova", "milo", "sage"]:
                _, ir = sql("SELECT intimacy FROM user_companion_stats WHERE user_id=? AND companion_id=?", uid, cid)
                intimacy[cid] = ir[0][0] if ir else 0
        _, items = sql("SELECT id, name, emoji, item_type, price, description, unlocks_at_intimacy, for_companion FROM shop_items ORDER BY item_type, price")
        result = []
        for i in items:
            target = i[7] or "luna"
            cur_int = intimacy.get(target, 0)
            result.append({
                "id": i[0], "name": i[1], "emoji": i[2], "item_type": i[3],
                "price": i[4], "description": i[5], "unlocks_at_intimacy": i[6],
                "for_companion": i[7], "locked": cur_int < i[6], "current_intimacy": cur_int
            })
        return jsonify({"items": result})

    @app.route("/api/stats")
    def api_stats():
        uid = session.get("user_id")
        user = get_user(uid)
        _, users = sql("SELECT COUNT(*) FROM users")
        _, opps = sql("SELECT COUNT(*) FROM opportunities WHERE status='open'")
        _, msgs = sql("SELECT COUNT(*) FROM ai_messages")
        _, checks = sql("SELECT COUNT(*) FROM checkins")
        _, act = sql("SELECT COUNT(DISTINCT user_id) FROM checkins WHERE date=date('now')")
        coins = user.get("coin_balance", 0) if user else 0
        uptime = int((datetime.now() - APP_START).total_seconds())
        days = uptime // 86400
        hours = (uptime % 86400) // 3600
        mins = (uptime % 3600) // 60
        return jsonify({
            "total_users": users[0][0] if users else 0,
            "total_opportunities": opps[0][0] if opps else 0,
            "total_messages": msgs[0][0] if msgs else 0,
            "total_checkins": checks[0][0] if checks else 0,
            "active_today": act[0][0] if act else 0,
            "total_buildings": 11545,
            "uptime_seconds": uptime,
            "uptime_formatted": str(days) + "天" + str(hours) + "小时" + str(mins) + "分",
            "user_coin_balance": int(coins),
        })

    print("[Phase1] Routes registered")
