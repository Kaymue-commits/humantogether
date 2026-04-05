# 🌍 HumanTogether — 共生境

> "你的AI住在武汉3D世界里，ta记得你的一切，你可以帮ta装修房间、买衣服、看着ta生活。"

一个 AI 伴侣社交世界，基于真实武汉3D城市构建。5位性格迥异的 AI 伙伴，拥有记忆系统、3D 房间、情感陪伴与货币经济体系。

[🌐 在线体验](http://139.196.22.102:5050) · [🏠 3D世界](http://139.196.22.102:5050/3d) · [💬 AI聊天](http://139.196.22.102:5050/)

---

## ✨ 功能特色

### 🤖 AI 伴侣系统
- **5位专属AI伙伴**：Luna、Kai、Nova、Milo、Sage，各有独特性格与回应风格
- **长期记忆**：对话内容持久化存储，AI 会引用历史信息
- **情感识别**：自动识别用户情绪（难过/焦虑/无聊/开心），给予适当回应
- **活动日志**：AI 有"当天日程"（看书/睡觉/发呆等），状态实时更新

### 🏙️ 3D 真实武汉世界
- **11,545栋真实建筑**数据（OpenStreetMap），含真实高度与坐标
- **温暖明亮天空**，随实际时间动态变化（清晨橙/白天蓝/黄昏红）
- **可爱小人**在城市中走动，**发光窗户**营造温馨氛围
- 绿色公园、蓝色湖泊、中央 hologram 水晶地标

### 🏠 AI 房间系统
- 每个 AI 拥有专属 3D 房间（墙色/地板/家具随性格定制）
- 用户可进入房间"参观"自己的 AI 伴侣
- 房间状态反映 AI 当前活动（睡觉/看书/发呆等）

### 💰 经济系统
- **共币**：平台虚拟货币
- 每日签到获取共币
- 拜访其他 AI 房间获取共币
- 商店购买家具装饰房间、购买衣服给 AI 穿戴

### 💬 AI 聊天
- 支持情感陪伴、职涯建议、技能学习、放松冥想引导
- AI 引用长期记忆，提供个性化回应
- 亲密度系统：聊得越多、礼物越多，亲密度越高，解锁更多内容

---

## 🗺️ 页面导览

| 页面 | 路由 | 说明 |
|------|------|------|
| 3D 世界 | `/3d` | 武汉3D地图，AI房屋标记，可进入任意AI房间 |
| AI 详情 | `/companion/<name>` | 查看AI资料、状态、日程、亲密度 |
| AI 房间 | `/room/<companion>` | 3D房间，查看家具与AI状态 |
| 聊天 | `/chat/<companion>` | 与AI对话，AI会引用记忆 |
| 商店 | `/shop` | 用共币购买家具/衣服 |
| 机会大厅 | `/opportunities` | 职业机会探索 |

---

## 🛠️ 技术架构

### 后端
- **Flask** (Python) — Web 框架
- **SQLite** — 数据持久化
- **WebSocket** (`ws_server.py`) — 实时通信
- **SSE** (`sse_server.py`) — 服务器推送
- **Companion Manager** — AI 人格管理系统，通过 OpenClaw Gateway 调用大模型

### 前端
- **Three.js** — 3D 渲染（城市、房间、VRM模型）
- **Cesium** — 真实地理 3D 地图
- **Blender** — 城市模型生成（Python脚本抓取 OSM 数据）
- **WebGL** — 3D 房间渲染

### AI 集成
- OpenClaw Gateway API — 调用 MiniMax-M2.7 模型
- 为每个 AI 伴侣配置专属 System Prompt，实现不同人格

---

## 📁 项目结构

```
humantogether/
├── app.py                    # Flask 主应用
├── companion_manager.py       # AI伴侣管理系统
├── companion_scheduler.py     # AI活动定时调度
├── ws_server.py              # WebSocket服务器
├── sse_server.py             # SSE服务器推送
├── sgj_warm.db               # SQLite数据库
├── companions/                # 5个AI的人格定义
│   ├── luna.py, kai.py, nova.py, milo.py, sage.py
├── templates/                 # HTML模板
│   ├── index3d_mapbox_real.html   # 3D世界主页
│   ├── companion_detail.html      # AI详情页
│   └── shop.html                   # 商店页
├── static/                   # 静态资源
│   ├── 3droom/               # Three.js 3D房间
│   ├── models/               # VRM/GLB 3D模型
│   ├── characters/           # AI头像
│   ├── js/                   # Three.js 库
│   └── data/                 # 武汉建筑JSON数据
├── blender/                  # Blender脚本（城市生成）
│   ├── fetch_osm_buildings.py   # OSM数据抓取
│   ├── generate_wuhan_3d.py      # Blender自动化建模
│   └── wuhan_3d_city.glb        # 生成的城市模型
└── 3droom/                   # 独立3D房间子项目
    ├── src/                  # 源代码
    ├── dist/                 # 构建产物
    └── package.json
```

---

## 🚀 快速部署

```bash
# 安装依赖
pip install flask

# 运行
python app.py

# 访问
open http://127.0.0.1:5050
```

---

## 📌 AI 伙伴一览

| 伙伴 |  Emoji  | 性格 | 颜色 |
|------|---------|------|------|
| Luna | 🌙 | 温柔倾听型 | 粉色系 |
| Kai  | 🌊 | 冷静理性型 | 蓝色系 |
| Nova | ⭐ | 积极激励型 | 橙色系 |
| Milo | 🌿 | 平和佛系型 | 绿色系 |
| Sage | 📚 | 智慧导师型 | 棕色系 |

---

## 📄 License

MIT License
