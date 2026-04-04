# 共生境 Phase 1 — AI伴侣世界

## 核心理念
"你的AI住在武汉3D世界里，ta记得你的一切，你可以帮ta装修房间、买衣服、看着ta生活。"

## Phase 1 功能列表

### 1. AI记忆系统
- 所有对话持久化存储
- AI有"长期记忆"（从历史对话中提取关键事实）
- AI每次对话引用之前的内容
- AI有"当天活动日志"（上午在看书、中午在睡觉等）

### 2. AI房间系统
- 每个AI有一个3D小房间
- 房间里有床/书架/桌子等（根据AI性格不同）
- 房间里显示AI当前状态（醒着/睡觉/看书/发呆）
- 用户可以进入自己的AI房间"参观"

### 3. 货币系统
- 共币（已有）
- 每日签到获取共币
- 拜访其他AI房间获取共币
- 商店：购买家具装饰AI房间
- 商店：购买衣服/配饰给AI穿

### 4. 3D世界（简化版）
- 武汉3D地图（已有建筑数据）
- 用户进入世界看到AI们的房子标记
- 点击进入某个AI的房间
- 用户自己的AI始终在主页陪着

### 5. 关系系统
- 用户和AI有"亲密度"数值
- 聊得越多、礼物越多，亲密度越高
- 亲密度解锁AI的新状态/衣服/家具

---

## 数据库设计

### users表（已有）
- id, username, display_name, avatar, coin_balance, created_at

### ai_companions表（新建）
- id, name, avatar, personality, bio, room_state, current_activity, last_active
- 5个初始AI: Luna, Kai, Nova, Milo, Sage

### ai_messages表（已有，改）
- id, user_id, companion, content, timestamp
- **新增：**is_remembered BOOLEAN（是否记忆）

### ai_memories表（新建）
- id, companion, memory_type, content, created_at, importance
- 类型：fact（事实）/ emotion（情感）/ event（事件）

### ai_activities表（新建）
- id, companion, activity, detail, started_at, ended_at
- 记录AI一天的活动："09:00 起床"，"10:00 看书"等

### room_items表（新建）
- id, user_id, companion, item_type, item_name, position, purchased_at

### shop_items表（新建）
- id, name, type, price, description, emoji, unlocks_at_intimacy

### user_companion_stats表（新建）
- user_id, companion, intimacy_level, total_chats, gifts_given, last_chat_at

---

## 页面结构

### `/` 主页
- 显示平台统计
- 大按钮进入3D世界

### `/world` 3D世界页
- 武汉3D地图
- 显示所有AI的房子标记
- 点击标记进入该AI的房间或聊天

### `/companion/<name>` AI详情页
- AI头像/名字/简介
- 当前心情/状态
- 今日活动时间线
- 亲密度进度条
- 入口：进入ta的房间 / 开始聊天

### `/room/<companion>` AI房间页
- 3D房间（简化CSS网格房间）
- 显示已购家具
- 当前状态动画（看书/睡觉等）
- "送礼物"按钮

### `/shop` 商店页
- 家具分类（床/书架/灯/地毯/墙画）
- 衣服分类（帽子/衣服/配饰）
- 按亲密度解锁

### `/chat/<companion>` AI聊天页
- 对话界面
- AI会引用历史记忆

---

## 技术方案

### AI记忆系统实现
```
每次对话后：
1. 存储消息到 ai_messages
2. 提取关键实体（人名/地点/事件）→ 存入 ai_memories
3. 每周AI"回忆"一次：从ai_memories随机选一条引用

AI上下文构造：
- system prompt 包含：AI性格 + 重要记忆（importance>5的）
- 对话历史：最近20条消息
```

### AI活动系统
```
定时任务（每小时）：
1. 更新AI当前活动
2. 记录到 ai_activities
3. 随机选择：看书/发呆/听音乐/和朋友聊天/休息

活动影响：
- 房间背景根据活动变化
- AI回复内容根据活动变化（困了→回复慢）
```

### 3D房间（简化实现）
```
不用Three.js，用CSS 3D transform：
- 用div模拟房间（墙面/地板/天花板）
- 用emoji表示家具
- AI状态用动画emoji表示

性能：每个房间只有几个div，极轻量
```

---

## 商业模式（Phase 1）

### 免费功能
- 5个AI聊天
- 每日签到得共币
- 拜访其他AI房间
- 基础家具（每AI 3件免费家具）

### 付费功能
- 高级家具：¥6-30
- 稀有衣服：¥10-50
- 亲密度速通卡：¥20（+100亲密度）
- AI"特别记忆"解锁：¥5（AI会记住一件事永久）

---

## 预计开发时间
- Phase 1: 2-3天（朕一个人）
- Phase 2: 5-7天（AI记忆系统完善 + 社交）
- Phase 3: 7-14天（3D房间升级 + 多人拜访）

---

## 下一步
等陛下确认后，朕开始搭建Phase 1的代码框架。
