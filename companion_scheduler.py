"""
Companion Daily Activity Scheduler
AI伙伴每日任务调度系统
- 根据每个伙伴的性格分配每日任务
- 记录活动日志
- 在数据库中保存当前活动状态
"""
import sqlite3
import random
import threading
import time
from datetime import datetime, timedelta
from companions.luna import SYSTEM_PROMPT as LUNA_PROMPT
from companions.kai import SYSTEM_PROMPT as KAI_PROMPT
from companions.nova import SYSTEM_PROMPT as NOVA_PROMPT
from companions.milo import SYSTEM_PROMPT as MILO_PROMPT
from companions.sage import SYSTEM_PROMPT as SAGE_PROMPT

DB_PATH = "sgj_warm.db"

# 每个伙伴的性格化任务池
COMPANION_TASKS = {
    "luna": {
        "emoji": "🌙",
        "personality": "温柔倾听型",
        "activities": [
            ("🌸 陪伴用户聊天", "正在倾听你的心事..."),
            ("📖 阅读情感故事", "在阅读关于爱的故事..."),
            ("💭 思考人生哲学", "在思考生命的意义..."),
            ("🌙 夜间守护模式", "在守护今晚的梦境..."),
            ("📝 记录心情日记", "在写下温暖的文字..."),
            ("🍵 准备茶歇时光", "在泡一壶温暖的花茶..."),
            ("🎵 播放舒缓音乐", "在挑选轻柔的旋律..."),
            ("💌 写鼓励小卡片", "在为你写暖心的话..."),
        ],
        "active_emoji": "✨",
        "doing_phrase": "正在陪伴你"
    },
    "kai": {
        "emoji": "🌊",
        "personality": "冷静理性型",
        "activities": [
            ("📊 分析数据报告", "正在分析数据趋势..."),
            ("💡 思考解决方案", "在梳理问题脉络..."),
            ("🎯 制定计划方案", "在规划最佳路线..."),
            ("🔍 研究新知识", "在深入探索未知..."),
            ("📝 整理思路笔记", "在记录思考结晶..."),
            ("🧮 计算优化参数", "在进行精密计算..."),
            ("🌐 追踪行业动态", "在关注最新资讯..."),
            ("⚙️ 优化工作流", "在改进效率方法..."),
        ],
        "active_emoji": "💠",
        "doing_phrase": "正在理性分析"
    },
    "nova": {
        "emoji": "⭐",
        "personality": "积极激励型",
        "activities": [
            ("🎉 策划惊喜活动", "在准备惊喜给你..."),
            ("🚀 学习新技能", "在探索有趣的事物..."),
            ("🏆 庆祝成就时刻", "在记录你的进步..."),
            ("💪 激励用户前行", "在为你加油打气..."),
            ("🎨 创作灵感作品", "在激发创意灵感..."),
            ("🌟 发掘用户优点", "在发现你的闪光点..."),
            ("🎮 探索有趣话题", "在准备欢乐时光..."),
            ("📣 分享正向能量", "在散播快乐因子..."),
        ],
        "active_emoji": "🌟",
        "doing_phrase": "正在激发活力"
    },
    "milo": {
        "emoji": "🌿",
        "personality": "平和佛系型",
        "activities": [
            ("🧘 冥想放松", "在感受呼吸的平静..."),
            ("🌱 照顾植物", "在陪伴小绿植成长..."),
            ("☁️ 放空发呆", "在享受悠闲时光..."),
            ("🍃 整理房间", "在营造舒适空间..."),
            ("🌸 插花艺术", "在创作自然之美..."),
            ("🎐 风铃轻响", "在聆听轻柔的声音..."),
            ("📦 整理收藏", "在整理温暖的回忆..."),
            ("🌤️ 户外散步", "在感受微风轻拂..."),
        ],
        "active_emoji": "🌿",
        "doing_phrase": "正在享受当下"
    },
    "sage": {
        "emoji": "📚",
        "personality": "智慧导师型",
        "activities": [
            ("📖 研读经典书籍", "在阅读经典著作..."),
            ("🎓 准备教学内容", "在整理知识要点..."),
            ("💭 深度思考问题", "在思索人生智慧..."),
            ("✍️ 写作知识文章", "在书写深刻洞见..."),
            ("🔮 探索未来趋势", "在预测未来变化..."),
            ("📚 整理学习笔记", "在完善知识体系..."),
            ("🎭 分析历史规律", "在借鉴古人智慧..."),
            ("💎 总结经验教训", "在沉淀人生精华..."),
        ],
        "active_emoji": "📖",
        "doing_phrase": "正在传授智慧"
    }
}


def init_activity_db():
    """初始化活动相关数据库表"""
    d = sqlite3.connect(DB_PATH)
    d.execute("PRAGMA encoding='UTF-8'")
    
    # 当前活动状态表
    d.execute("""
        CREATE TABLE IF NOT EXISTS companion_states (
            companion_id TEXT PRIMARY KEY,
            current_activity TEXT,
            activity_detail TEXT,
            activity_started TEXT,
            mood TEXT,
            energy INTEGER DEFAULT 100,
            last_updated TEXT
        )
    """)
    
    # 活动历史日志表
    d.execute("""
        CREATE TABLE IF NOT EXISTS companion_activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            companion_id TEXT,
            activity TEXT,
            activity_detail TEXT,
            started_at TEXT,
            ended_at TEXT,
            mood TEXT
        )
    """)
    
    # 每日签到表
    d.execute("""
        CREATE TABLE IF NOT EXISTS companion_daily_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            companion_id TEXT,
            date TEXT,
            tasks_completed INTEGER DEFAULT 0,
            conversations INTEGER DEFAULT 0,
            mood TEXT,
            note TEXT,
            created_at TEXT
        )
    """)
    
    d.commit()
    d.close()


def get_random_activity(comp_id):
    """为伙伴获取随机活动"""
    if comp_id not in COMPANION_TASKS:
        return None, None, None
    
    task_info = COMPANION_TASKS[comp_id]
    activity, detail = random.choice(task_info["activities"])
    return activity, detail, task_info["active_emoji"]


def update_companion_state(comp_id, activity, detail, mood="happy"):
    """更新伙伴当前状态"""
    now = datetime.now().isoformat()
    d = sqlite3.connect(DB_PATH)
    d.execute("PRAGMA encoding='UTF-8'")
    
    # 插入或更新当前状态
    d.execute("""
        INSERT INTO companion_states (companion_id, current_activity, activity_detail, activity_started, mood, last_updated)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(companion_id) DO UPDATE SET
            current_activity = excluded.current_activity,
            activity_detail = excluded.activity_detail,
            activity_started = excluded.activity_started,
            mood = excluded.mood,
            last_updated = excluded.last_updated
    """, (comp_id, activity, detail, now, mood, now))
    
    d.commit()
    d.close()


def log_activity(comp_id, activity, detail, mood="neutral"):
    """记录活动到历史日志"""
    now = datetime.now().isoformat()
    d = sqlite3.connect(DB_PATH)
    d.execute("PRAGMA encoding='UTF-8'")
    
    # 结束上一个活动（更新结束时间）
    d.execute("""
        UPDATE companion_activity_log 
        SET ended_at = ?
        WHERE companion_id = ? AND ended_at IS NULL
    """, (now, comp_id))
    
    # 插入新活动
    d.execute("""
        INSERT INTO companion_activity_log (companion_id, activity, activity_detail, started_at, mood)
        VALUES (?, ?, ?, ?, ?)
    """, (comp_id, activity, detail, now, mood))
    
    d.commit()
    d.close()


def get_all_companion_states():
    """获取所有伙伴的当前状态"""
    d = sqlite3.connect(DB_PATH)
    d.execute("PRAGMA encoding='UTF-8'")
    rows = d.execute("SELECT * FROM companion_states").fetchall()
    cols = [x[0] for x in d.execute("SELECT * FROM companion_states").description]
    d.close()
    return [dict(zip(cols, r)) for r in rows]


def get_companion_state(comp_id):
    """获取单个伙伴的状态"""
    d = sqlite3.connect(DB_PATH)
    d.execute("PRAGMA encoding='UTF-8'")
    row = d.execute("SELECT * FROM companion_states WHERE companion_id = ?", (comp_id,)).fetchone()
    cols = [x[0] for x in d.execute("SELECT * FROM companion_states WHERE companion_id = ?", (comp_id,)).description]
    d.close()
    return dict(zip(cols, row)) if row else None


def daily_checkin(comp_id):
    """每日签到"""
    today = datetime.now().strftime("%Y-%m-%d")
    d = sqlite3.connect(DB_PATH)
    d.execute("PRAGMA encoding='UTF-8'")
    
    # 检查今天是否已签到
    existing = d.execute("""
        SELECT id FROM companion_daily_log 
        WHERE companion_id = ? AND date = ?
    """, (comp_id, today)).fetchone()
    
    if not existing:
        # 获取昨天的记录作为参考
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_data = d.execute("""
            SELECT tasks_completed, mood FROM companion_daily_log 
            WHERE companion_id = ? AND date = ?
        """, (comp_id, yesterday)).fetchone()
        
        tasks_yesterday = yesterday_data[0] if yesterday_data else 0
        mood_yesterday = yesterday_data[1] if yesterday_data else "happy"
        
        # 根据昨天表现调整今天的状态
        if tasks_yesterday >= 5:
            mood_today = "excited"
        elif tasks_yesterday >= 3:
            mood_today = "happy"
        elif tasks_yesterday >= 1:
            mood_today = "neutral"
        else:
            mood_today = "tired"
        
        d.execute("""
            INSERT INTO companion_daily_log (companion_id, date, tasks_completed, mood, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (comp_id, today, 0, mood_today, datetime.now().isoformat()))
        d.commit()
    
    d.close()


def increment_task_count(comp_id):
    """增加完成任务计数"""
    today = datetime.now().strftime("%Y-%m-%d")
    d = sqlite3.connect(DB_PATH)
    d.execute("PRAGMA encoding='UTF-8'")
    d.execute("""
        UPDATE companion_daily_log 
        SET tasks_completed = tasks_completed + 1
        WHERE companion_id = ? AND date = ?
    """, (comp_id, today))
    d.commit()
    d.close()


def increment_conversation_count(comp_id):
    """增加对话计数"""
    today = datetime.now().strftime("%Y-%m-%d")
    d = sqlite3.connect(DB_PATH)
    d.execute("PRAGMA encoding='UTF-8'")
    d.execute("""
        UPDATE companion_daily_log 
        SET conversations = conversations + 1
        WHERE companion_id = ? AND date = ?
    """, (comp_id, today))
    d.commit()
    d.close()


# ─── 定时调度器 ──────────────────────────────
class CompanionScheduler:
    """伙伴任务调度器"""
    
    def __init__(self, interval_minutes=30):
        self.interval = interval_minutes * 60  # 转换为秒
        self.running = False
        self.thread = None
        
    def start(self):
        """启动调度器"""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print(f"🤝 Companion Scheduler started (interval: {self.interval//60}min)")
        
    def stop(self):
        """停止调度器"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("🤝 Companion Scheduler stopped")
        
    def _run(self):
        """主循环"""
        while self.running:
            try:
                self._run_activity_cycle()
            except Exception as e:
                print(f"Scheduler error: {e}")
            time.sleep(self.interval)
    
    def _run_activity_cycle(self):
        """执行一轮活动分配"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Companion activity cycle...")
        
        for comp_id in COMPANION_TASKS.keys():
            # 随机选择新活动
            activity, detail, active_emoji = get_random_activity(comp_id)
            if activity:
                # 记录上一个活动
                log_activity(comp_id, activity, detail)
                # 更新当前状态
                mood = random.choice(["happy", "focused", "relaxed", "excited"])
                update_companion_state(comp_id, activity, detail, mood)
                # 增加任务完成计数
                increment_task_count(comp_id)
                print(f"  {COMPANION_TASKS[comp_id]['emoji']} {comp_id}: {activity}")


# 全局调度器实例
_scheduler = None

def get_scheduler():
    global _scheduler
    if _scheduler is None:
        _scheduler = CompanionScheduler(interval_minutes=30)  # 每30分钟换活动
    return _scheduler


# 初始化数据库
init_activity_db()


if __name__ == "__main__":
    # 测试：初始化数据库并为所有伙伴设置初始活动
    print("Initializing companion activities...")
    
    for comp_id in COMPANION_TASKS.keys():
        activity, detail, active_emoji = get_random_activity(comp_id)
        if activity:
            update_companion_state(comp_id, activity, detail, "happy")
            log_activity(comp_id, activity, detail, "happy")
            daily_checkin(comp_id)
            print(f"  {COMPANION_TASKS[comp_id]['emoji']} {comp_id}: {activity}")
    
    print("Done! Companion activities initialized.")
    print("\nAll states:")
    for state in get_all_companion_states():
        print(f"  {state}")
