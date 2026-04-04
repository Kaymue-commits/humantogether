"""
共生境 - 5个AI房间 Blender 自动化建模脚本
用法: /snap/bin/blender --background --python gen_5_rooms.py
"""
import bpy
import math
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__)) + "/assets/rooms/"
os.makedirs(OUT_DIR, exist_ok=True)

# ── 清理场景 ──────────────────────────────────────────────────────
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for m in bpy.data.meshes:
    bpy.data.meshes.remove(m)
for m in bpy.data.materials:
    bpy.data.materials.remove(m)

# ── 材质工厂 ───────────────────────────────────────────────────────
def mat(name, hex_color, roughness=0.5, metallic=0.0):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = tuple(
            int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4)) + (1,)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
    return mat

def assign_mat(obj, mat_name, hex_color, roughness=0.5, metallic=0.0):
    m = mat(mat_name, hex_color, roughness, metallic)
    if obj.data.materials:
        obj.data.materials[0] = m
    else:
        obj.data.materials.append(m)

# ── 基础房间 ───────────────────────────────────────────────────────
def create_room(width=1200, depth=900, height=500):
    """创建基础房间骨架：地板 + 4面墙 + 天花板"""
    # Floor
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    floor = bpy.context.active_object
    floor.name = "Floor"
    floor.scale = (width/2, depth/2, 10)
    floor.location = (0, 0, -5)
    bpy.ops.object.transform_apply()
    assign_mat(floor, "mat_floor", "8B7355", roughness=0.8)

    # Ceiling
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    ceil = bpy.context.active_object
    ceil.name = "Ceiling"
    ceil.scale = (width/2, depth/2, 10)
    ceil.location = (0, 0, height + 5)
    bpy.ops.object.transform_apply()
    assign_mat(ceil, "mat_ceiling", "f5f0e8", roughness=0.9)

    # Back wall
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    bw = bpy.context.active_object
    bw.name = "BackWall"
    bw.scale = (width/2, 10, height/2)
    bw.location = (0, -depth/2, height/2)
    bpy.ops.object.transform_apply()
    assign_mat(bw, "mat_wall", "e8e0d5", roughness=0.9)

    # Left wall
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    lw = bpy.context.active_object
    lw.name = "LeftWall"
    lw.scale = (10, depth/2, height/2)
    lw.location = (-width/2, 0, height/2)
    bpy.ops.object.transform_apply()
    assign_mat(lw, "mat_wall_l", "ddd5c5", roughness=0.9)

    # Right wall
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    rw = bpy.context.active_object
    rw.name = "RightWall"
    rw.scale = (10, depth/2, height/2)
    rw.location = (width/2, 0, height/2)
    bpy.ops.object.transform_apply()
    assign_mat(rw, "mat_wall_r", "ddd5c5", roughness=0.9)

    return [floor, ceil, bw, lw, rw]

# ── 家具部件 ──────────────────────────────────────────────────────
def box(name, size, loc, rot=(0,0,0), col_name="mat_default", hex_c="cccccc", rough=0.6, metallic=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    obj.rotation_euler = rot
    bpy.ops.object.transform_apply()
    assign_mat(obj, col_name, hex_c, roughness=rough, metallic=metallic)
    return obj

def cylinder(name, r, depth, loc, rot=(0,0,0), col_name="mat_default", hex_c="cccccc", rough=0.6, metallic=0.0):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.transform_apply()
    assign_mat(obj, col_name, hex_c, roughness=rough, metallic=metallic)
    return obj

def sphere(name, r, loc, col_name="mat_default", hex_c="cccccc", rough=0.6, metallic=0.0):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.transform_apply()
    assign_mat(obj, col_name, hex_c, roughness=rough, metallic=metallic)
    return obj

# ─────────────────────────────────────────────────────────────────
# 🌙 LUNA — 月光小屋：软萌、薰衣草、星星灯、圆形吊椅
# ─────────────────────────────────────────────────────────────────
def build_luna_room():
    create_room()
    W, D, H = 1200, 900, 500

    # 地板换成奶油色地毯
    fl = bpy.data.objects["Floor"]
    assign_mat(fl, "mat_carpet", "ffe4e1", roughness=0.95)

    # 墙面 — 浅薰衣草色
    for wall_name in ["BackWall", "LeftWall", "RightWall"]:
        w = bpy.data.objects[wall_name]
        assign_mat(w, "mat_luna_wall", "e8d4f0", roughness=0.9)

    # 天花板
    assign_mat(bpy.data.objects["Ceiling"], "mat_ceiling_luna", "faf5ff", roughness=0.9)

    # 圆形吊椅 (hoop chair) — 用两个圆环组成
    bpy.ops.mesh.primitive_torus_add(
        major_radius=90, minor_radius=8,
        location=(0, -100, 280), rotation=(math.pi/2, 0, 0)
    )
    chair_ring = bpy.context.active_object
    chair_ring.name = "ChairRing"
    assign_mat(chair_ring, "mat_white", "ffffff", roughness=0.3, metallic=0.1)
    # 垂下的绳索
    for i in range(4):
        angle = i * math.pi / 2
        x = 0 + 90 * math.cos(angle)
        y = -100 + 90 * math.sin(angle)
        cylinder(f"Rope_{i}", 2, 200, (x, y, 380), col_name="mat_rope", hex_c="d4c4a0", rough=0.9)

    # 吊椅坐垫
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -100, 200))
    cushion = bpy.context.active_object
    cushion.name = "ChairCushion"
    cushion.scale = (70, 70, 15)
    bpy.ops.object.transform_apply()
    assign_mat(cushion, "mat_cushion_luna", "ffb6c1", roughness=0.9)

    # 白纱幔（用半透明薄板模拟）
    for i, angle in enumerate([0, math.pi/3, 2*math.pi/3]):
        bx = 150 * math.cos(angle) - 50
        bz = 280 + 80 * math.sin(angle)
        box(f"Curtain_{i}", (8, 200, 250), (bx, -180, 150), col_name="mat_curtain", hex_c="fff5fa", rough=0.95)

    # 月亮抱枕
    sphere("MoonPillow", 30, (250, -200, 50), col_name="mat_moon", hex_c="ffd700", rough=0.9)

    # 星星灯串（天花板位置一串小圆球）
    import random
    random.seed(42)
    for i in range(20):
        x = random.randint(-500, 500)
        y = random.randint(-350, 200)
        z = H - 10
        sphere(f"Star_{i}", 5, (x, y, z), col_name="mat_star", hex_c="ffd700", rough=0.2)
    # 灯串连接线
    for i in range(19):
        x1 = random.randint(-500, 500) if i == 0 else 0
        # 简化：用小圆柱代替电线的效果

    # 书桌 + 书架
    box("Desk_Luna", (200, 80, 5), (-350, 250, 180), col_name="mat_wood_light", hex_c="c8a87a", rough=0.7)
    box("DeskLeg_L", (5, 5, 180), (-450, 250, 90), col_name="mat_wood_light", hex_c="c8a87a", rough=0.7)
    box("DeskLeg_R", (5, 5, 180), (-250, 250, 90), col_name="mat_wood_light", hex_c="c8a87a", rough=0.7)
    # 书架
    for i in range(4):
        box(f"Shelf_{i}", (80, 20, 5), (-380, 280, 200 + i*50), col_name="mat_wood_light", hex_c="d4b896", rough=0.7)
        # 书架侧板
        if i == 0:
            box("ShelfSide_L", (5, 25, 220), (-420, 280, 200), col_name="mat_wood_light", hex_c="c8a87a", rough=0.7)
            box("ShelfSide_R", (5, 25, 220), (-340, 280, 200), col_name="mat_wood_light", hex_c="c8a87a", rough=0.7)

    # 床上用品（窗边休息区）
    box("BedBase", (250, 180, 30), (350, -200, 15), col_name="mat_bed", hex_c="e8d4f0", rough=0.9)
    box("BedPillow", (60, 40, 15), (250, -150, 45), col_name="mat_pillow", hex_c="fff0f5", rough=0.95)
    box("BedBlanket", (230, 150, 10), (350, -200, 50), col_name="mat_blanket", hex_c="ffb6c1", rough=0.95)

    # 窗台 — 永生花盒
    box("WindowSeat", (200, 30, 20), (0, -430, 200), col_name="mat_wood_light", hex_c="e8d4f0", rough=0.7)
    box("FlowerBox", (120, 25, 30), (0, -445, 230), col_name="mat_wood_light", hex_c="c8a87a", rough=0.7)
    # 假花（彩色小球）
    for fx, fz, fc in [(-30, 0, "ff69b4"), (0, 5, "ff1493"), (30, 0, "ff69b4"), (-15, 8, "ffffff"), (15, 8, "ff1493")]:
        sphere(f"Flower_{fx}", 10, (fx, -455, fz+250), col_name="mat_flower", hex_c=fc, rough=0.5)

    # 月球小夜灯
    sphere("MoonLamp", 25, (-450, -250, 50), col_name="mat_moonlamp", hex_c="fffacd", rough=0.3)

    print("✅ Luna 月光小屋 完成")

# ─────────────────────────────────────────────────────────────────
# 🌊 KAI — 深海静舍：深灰蓝、极简、双屏显示器、人体工学椅
# ─────────────────────────────────────────────────────────────────
def build_kai_room():
    create_room()
    W, D, H = 1200, 900, 500

    # 地板 — 深木色
    fl = bpy.data.objects["Floor"]
    assign_mat(fl, "mat_floor_kai", "3d3020", roughness=0.6)

    # 墙面 — 深灰蓝
    for wall_name in ["BackWall", "LeftWall", "RightWall"]:
        w = bpy.data.objects[wall_name]
        assign_mat(w, "mat_wall_kai", "1e2a3a", roughness=0.8)

    # 天花板
    assign_mat(bpy.data.objects["Ceiling"], "mat_ceiling_kai", "2a3a4a", roughness=0.8)

    # 极简升降桌
    box("Desk_Kai", (300, 120, 5), (0, 200, 180), col_name="mat_desk_kai", hex_c="1a1a1a", rough=0.4, metallic=0.1)
    box("DeskLeg_KL", (5, 5, 180), (-140, 200, 90), col_name="mat_metal", hex_c="2a2a2a", rough=0.3, metallic=0.8)
    box("DeskLeg_KR", (5, 5, 180), (140, 200, 90), col_name="mat_metal", hex_c="2a2a2a", rough=0.3, metallic=0.8)
    box("DeskTopBar", (300, 5, 5), (0, 200, 185), col_name="mat_metal", hex_c="333333", rough=0.3, metallic=0.7)

    # 双屏显示器
    for sx, ox in [(-80, 0), (80, 0)]:
        box(f"Monitor_{ox}", (90, 5, 60), (sx, 160, 220), col_name="mat_monitor", hex_c="0a0a0a", rough=0.2, metallic=0.3)
        box(f"MonitorScreen_{ox}", (80, 2, 52), (sx, 155, 220), col_name="mat_screen", hex_c="196aff", rough=0.1, metallic=0.0)
        # 显示器支架
        cylinder(f"MonitorStand_{ox}", 4, 50, (sx, 175, 195), col_name="mat_metal", hex_c="333333", rough=0.3, metallic=0.8)
        box(f"MonitorBase_{ox}", (40, 5, 20), (sx, 175, 183), col_name="mat_metal", hex_c="333333", rough=0.3, metallic=0.8)

    # 键盘
    box("Keyboard", (100, 30, 5), (0, 160, 186), col_name="mat_keyboard", hex_c="1a1a1a", rough=0.5)

    # 人体工学椅
    # 椅座
    box("ChairSeat", (90, 80, 10), (0, 50, 110), col_name="mat_chair", hex_c="1a1a1a", rough=0.8)
    # 椅背
    box("ChairBack", (90, 10, 120), (0, 0, 160), col_name="mat_chair", hex_c="1a1a1a", rough=0.8)
    # 气压柱
    cylinder("ChairPiston", 5, 80, (0, 50, 55), col_name="mat_metal", hex_c="444444", rough=0.3, metallic=0.9)
    # 五星脚
    for a in range(5):
        angle = a * 2 * math.pi / 5
        bx = 50 * math.cos(angle)
        by = 50 * math.sin(angle) + 50
        box(f"ChairLeg_{a}", (8, 30, 5), (bx, by, 15), col_name="mat_metal", hex_c="333333", rough=0.3, metallic=0.9)
    # 头枕
    box("Headrest", (60, 10, 30), (0, -5, 230), col_name="mat_chair", hex_c="1a1a1a", rough=0.8)

    # 开放书架（书籍按颜色排列）
    for i in range(5):
        bx = -500 + i * 30
        book_h = 60 + (i % 3) * 20
        book_colors = ["196aff", "ff4444", "44ff44", "ffffff", "ff8c00"]
        box(f"Book_{i}", (20, 80, book_h), (bx, 280, 80 + book_h/2), col_name=f"mat_book_{i}", hex_c=book_colors[i % 5], rough=0.8)

    # 世界地图海报（墙上）
    box("MapFrame", (150, 5, 100), (-450, -430, 250), col_name="mat_frame", hex_c="2a3a4a", rough=0.5)
    box("MapContent", (140, 2, 90), (-450, -435, 250), col_name="mat_map", hex_c="1e4a6a", rough=0.9)

    # 地球仪
    sphere("Globe", 40, (450, -250, 40), col_name="mat_globe", hex_c="1e5a8a", rough=0.4)
    cylinder("GlobeStand", 5, 60, (450, -250, 0), col_name="mat_metal", hex_c="333333", rough=0.3, metallic=0.8)
    box("GlobeBase", (60, 60, 5), (450, -250, -30), col_name="mat_metal", hex_c="333333", rough=0.3, metallic=0.8)

    # 咖啡机
    box("CoffeeMachine", (50, 40, 70), (400, 260, 35), col_name="mat_coffee", hex_c="2a2a2a", rough=0.4, metallic=0.2)
    box("CoffeeBase", (60, 50, 10), (400, 260, 0), col_name="mat_metal", hex_c="333333", rough=0.3, metallic=0.6)

    print("✅ Kai 深海静舍 完成")

# ─────────────────────────────────────────────────────────────────
# ⭐ NOVA — 星光工作室：渐变粉橙、霓虹字、站立桌、手办、彩色绿植
# ─────────────────────────────────────────────────────────────────
def build_nova_room():
    create_room()
    W, D, H = 1200, 900, 500

    # 地板 — 彩色渐变地毯
    fl = bpy.data.objects["Floor"]
    assign_mat(fl, "mat_floor_nova", "ff8c00", roughness=0.9)

    # 墙面 — 渐变粉橙
    for wall_name in ["BackWall", "LeftWall", "RightWall"]:
        w = bpy.data.objects[wall_name]
        assign_mat(w, "mat_wall_nova", "ff6b35", roughness=0.8)

    # 天花板 — 亮黄色
    assign_mat(bpy.data.objects["Ceiling"], "mat_ceiling_nova", "fff060", roughness=0.8)

    # 站立办公桌
    box("DeskNova", (250, 100, 5), (0, 150, 200), col_name="mat_desk_nova", hex_c="ff4500", rough=0.5)
    box("DeskLegNL", (5, 5, 200), (-115, 150, 100), col_name="mat_metal", hex_c="ff4500", rough=0.4, metallic=0.6)
    box("DeskLegNR", (5, 5, 200), (115, 150, 100), col_name="mat_metal", hex_c="ff4500", rough=0.4, metallic=0.6)

    # 手办展示架
    for row in range(3):
        for col in range(4):
            bx = -400 + col * 60
            bz = 50 + row * 60
            sphere(f"Figure_{row}_{col}", 15, (bx, 280, bz), col_name="mat_figure", hex_c="ff1493", rough=0.4)

    # 便利贴墙（墙上贴满彩色方块）
    import random
    random.seed(123)
    for i in range(30):
        nx = random.randint(-500, -200)
        ny = -430
        nz = random.randint(100, 400)
        colors = ["ffff00", "ff69b4", "00ffff", "ff4500", "7fff00"]
        box(f"Note_{i}", (25, 3, 25), (nx, ny, nz), col_name=f"mat_note_{i}", hex_c=random.choice(colors), rough=0.95)

    # 霓虹字 "YOU GOT THIS"（用一排彩色方块模拟）
    neon_colors = ["ff1493", "ffff00", "00ffff", "ff4500", "7fff00", "ff1493", "ffff00", "00ffff", "ff4500", "7fff00"]
    for i, c in enumerate(neon_colors):
        box(f"Neon_{i}", (20, 5, 30), (-100 + i * 25, -435, 380), col_name=f"mat_neon_{i}", hex_c=c, rough=0.2)

    # 亮黄色懒人沙发
    box("SofaBase", (180, 100, 40), (300, 0, 20), col_name="mat_sofa_nova", hex_c="ffff00", rough=0.9)
    box("SofaBack", (180, 20, 80), (300, -40, 80), col_name="mat_sofa_nova", hex_c="ffcc00", rough=0.9)
    box("SofaArmL", (20, 100, 60), (215, 0, 50), col_name="mat_sofa_nova", hex_c="ffcc00", rough=0.9)
    box("SofaArmR", (20, 100, 60), (385, 0, 50), col_name="mat_sofa_nova", hex_c="ffcc00", rough=0.9)

    # 彩色绿植
    plant_colors = ["ff4500", "7fff00", "00ced1", "ff1493", "ffd700"]
    plant_x = [-450, -350, 350, 450, 400]
    plant_z = [0, 0, 0, 0, 0]
    for i, (px, pz, pc) in enumerate(zip(plant_x, plant_z, plant_colors)):
        cylinder(f"PlantPot_{i}", 20, 30, (px, 280, 15), col_name="mat_pot", hex_c="8b4513", rough=0.8)
        sphere(f"Plant_{i}", 25, (px, 280, 60), col_name="mat_plant", hex_c=pc, rough=0.9)

    # JBL蓝牙音箱
    box("Speaker", (60, 40, 80), (-200, 260, 40), col_name="mat_speaker", hex_c="1a1a1a", rough=0.5)
    box("SpeakerFront", (50, 2, 60), (-200, 238, 40), col_name="mat_speaker_grid", hex_c="333333", rough=0.6)

    print("✅ Nova 星光工作室 完成")

# ─────────────────────────────────────────────────────────────────
# 🌿 MILO — 竹林茶室：禅意、榻榻米、竹子、枯山水、纸灯笼
# ─────────────────────────────────────────────────────────────────
def build_milo_room():
    create_room()
    W, D, H = 1200, 900, 500

    # 地板 — 榻榻米
    fl = bpy.data.objects["Floor"]
    assign_mat(fl, "mat_tatami", "c8b87a", roughness=0.85)

    # 墙面 — 淡米色
    for wall_name in ["BackWall", "LeftWall", "RightWall"]:
        w = bpy.data.objects[wall_name]
        assign_mat(w, "mat_wall_milo", "f5f0e0", roughness=0.9)

    # 天花板 — 纸灯笼暖黄
    assign_mat(bpy.data.objects["Ceiling"], "mat_ceiling_milo", "fff5d0", roughness=0.95)

    # 移除原地板，换成榻榻米垫
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    tatami = bpy.context.active_object
    tatami.name = "Tatami"
    tatami.scale = (600, 450, 8)
    tatami.location = (0, 0, -4)
    bpy.ops.object.transform_apply()
    assign_mat(tatami, "mat_tatami2", "d4c896", roughness=0.85)

    # 蒲团坐垫 × 3
    for dx, dy in [(-100, 50), (0, 50), (100, 50)]:
        cylinder(f"Cushion_{dx}", 45, 15, (dx, dy, 15), col_name="mat_cushion_milo", hex_c="8fbc8f", rough=0.95)

    # 矮茶几
    box("TeaTable", (150, 80, 5), (0, 50, 80), col_name="mat_bamboo", hex_c="a08060", rough=0.7)
    # 茶几腿（矮）
    for lx, ly in [(-60, 20), (-60, 80), (60, 20), (60, 80)]:
        box(f"TableLeg_{lx}", (8, 8, 75), (lx, ly, 37), col_name="mat_bamboo", hex_c="8b7355", rough=0.7)

    # 茶具
    cylinder("Teapot", 15, 20, (-20, 60, 95), col_name="mat_tea", hex_c="d2691e", rough=0.6)
    cylinder("Teacup1", 8, 10, (10, 45, 92), col_name="mat_tea", hex_c="f5f5dc", rough=0.6)
    cylinder("Teacup2", 8, 10, (25, 55, 92), col_name="mat_tea", hex_c="f5f5dc", rough=0.6)

    # 竹子装饰（竖条）
    for i in range(8):
        bx = -550 + i * 30 + (i % 2) * 15
        by = -400 + (i % 3) * 20
        h = 350 + (i % 4) * 50
        cylinder(f"Bamboo_{i}", 6, h, (bx, by, h/2), col_name="mat_bamboo", hex_c="8fbc8f", rough=0.8)

    # 枯山水盆景（角落）
    box("ZenBase", (180, 100, 10), (-350, -300, 5), col_name="mat_stone", hex_c="8b8370", rough=0.9)
    # 白色砂石
    for sx, sy in [(-380, -320), (-360, -300), (-340, -310), (-380, -280), (-360, -270)]:
        sphere(f"Sand_{sx}", 12, (sx, sy, 15), col_name="mat_sand", hex_c="f5f5dc", rough=0.95)
    # 枯山石
    for rx, rz in [(-370, -300), (-330, -290)]:
        sphere(f"Rock_{rx}", 20, (rx, rz, 20), col_name="mat_rock", hex_c="696969", rough=0.9)
    # 小棵盆栽
    sphere("Bonsai", 25, (-300, -300, 25), col_name="mat_bonsai", hex_c="228b22", rough=0.9)
    cylinder("BonsaiTrunk", 5, 30, (-300, -300, 15), col_name="mat_wood", hex_c="8b4513", rough=0.8)

    # 水墨山水画
    box("PaintingFrame", (200, 5, 150), (-450, -435, 280), col_name="mat_frame_wood", hex_c="5c4033", rough=0.7)
    box("PaintingCanvas", (185, 2, 135), (-450, -440, 280), col_name="mat_painting", hex_c="e8e0d0", rough=0.95)
    # 山水轮廓（几个深色块模拟）
    box("Mountain1", (80, 2, 60), (-480, -441, 260), col_name="mat_mountain", hex_c="4a4a4a", rough=0.95)
    box("Mountain2", (100, 2, 80), (-440, -441, 240), col_name="mat_mountain2", hex_c="3a3a3a", rough=0.95)

    # 纸灯笼（悬天花板）
    sphere("Lantern", 50, (0, 0, 450), col_name="mat_lantern", hex_c="fff5d0", rough=0.95)
    # 灯笼吊线
    cylinder("LanternCord", 2, 100, (0, 0, 400), col_name="mat_rope", hex_c="d4c4a0", rough=0.9)

    # 线香（用细圆柱模拟）
    cylinder("Incense", 1, 40, (80, 50, 87), col_name="mat_incense", hex_c="8b4513", rough=0.8)
    sphere("IncenseTip", 3, (80, 50, 112), col_name="mat_incense_tip", hex_c="ff4500", rough=0.3)

    print("✅ Milo 竹林茶室 完成")

# ─────────────────────────────────────────────────────────────────
# 📚 SAGE — 智慧书房：深胡桃木、皮质沙发、到顶书架、老式台灯
# ─────────────────────────────────────────────────────────────────
def build_sage_room():
    create_room()
    W, D, H = 1200, 900, 500

    # 地板 — 深红色实木
    fl = bpy.data.objects["Floor"]
    assign_mat(fl, "mat_floor_sage", "5c3317", roughness=0.5)

    # 墙面下半 — 深胡桃木护墙板
    box("WallPanel_Back", (610, 10, 200), (0, -440, 100), col_name="mat_wood_dark", hex_c="3d2210", rough=0.6)
    box("WallPanel_L", (10, 460, 200), (-600, 0, 100), col_name="mat_wood_dark", hex_c="3d2210", rough=0.6)
    # 墙面上半 — 暖白
    for wall_name in ["BackWall", "LeftWall", "RightWall"]:
        w = bpy.data.objects[wall_name]
        assign_mat(w, "mat_wall_sage_up", "f5f0e8", roughness=0.9)

    # 天花板
    assign_mat(bpy.data.objects["Ceiling"], "mat_ceiling_sage", "faf8f0", roughness=0.9)

    # 到顶大书架（整面墙）
    # 书架背板
    box("BookcaseBack", (600, 10, 500), (-350, -420, 250), col_name="mat_wood_dark", hex_c="2d1a0a", rough=0.6)
    # 书架侧板
    for sx in [-680, -20]:
        box(f"BookcaseSide_{sx}", (10, 30, 500), (sx, -420, 250), col_name="mat_wood_dark", hex_c="3d2210", rough=0.6)
    # 书架层板
    for i in range(6):
        bh = i * 85 + 10
        box(f"Bookshelf_{i}", (650, 30, 8), (-350, -420, bh), col_name="mat_wood_dark", hex_c="2d1a0a", rough=0.6)
    # 书籍（各种颜色）
    book_cols = ["8b0000","00008b","006400","daa520","4b0082","8b4513","2f4f4f","800000","191970","556b2f"]
    for i in range(35):
        bx = -660 + (i % 7) * 90 + (i // 7) * 5
        bh = 10 + (i // 7) * 85
        bw = 60 + (i % 3) * 15
        bh_real = 50 + (i % 5) * 10
        bc = book_cols[i % len(book_cols)]
        box(f"SageBook_{i}", (bw, 25, bh_real), (bx, -425, bh + bh_real/2), col_name=f"mat_sb_{i}", hex_c=bc, rough=0.8)

    # 皮质复古扶手椅
    box("ArmchairSeat", (130, 120, 15), (200, 100, 90), col_name="mat_leather", hex_c="5c3317", rough=0.7)
    box("ArmchairBack", (130, 15, 130), (200, 50, 170), col_name="mat_leather", hex_c="5c3317", rough=0.7)
    box("ArmchairArmL", (15, 120, 60), (135, 100, 120), col_name="mat_leather", hex_c="4a2810", rough=0.7)
    box("ArmchairArmR", (15, 120, 60), (265, 100, 120), col_name="mat_leather", hex_c="4a2810", rough=0.7)
    cylinder("ArmchairLeg_FL", 5, 70, (145, 170, 35), col_name="mat_metal", hex_c="b8860b", rough=0.3, metallic=0.8)
    cylinder("ArmchairLeg_FR", 5, 70, (255, 170, 35), col_name="mat_metal", hex_c="b8860b", rough=0.3, metallic=0.8)
    cylinder("ArmchairLeg_BL", 5, 70, (145, 30, 35), col_name="mat_metal", hex_c="b8860b", rough=0.3, metallic=0.8)
    cylinder("ArmchairLeg_BR", 5, 70, (255, 30, 35), col_name="mat_metal", hex_c="b8860b", rough=0.3, metallic=0.8)

    # 老式黄铜台灯
    cylinder("LampBase", 20, 5, (-150, 200, 5), col_name="mat_brass", hex_c="b8860b", rough=0.3, metallic=0.8)
    cylinder("LampPole", 5, 120, (-150, 200, 65), col_name="mat_brass", hex_c="b8860b", rough=0.3, metallic=0.8)
    # 灯罩
    bpy.ops.mesh.primitive_cone_add(
        radius1=30, radius2=15, depth=40,
        location=(-150, 200, 135), rotation=(0, 0, 0)
    )
    lampshade = bpy.context.active_object
    lampshade.name = "LampShade"
    bpy.ops.object.transform_apply()
    assign_mat(lampshade, "mat_shade", hex_c="f5deb3", roughness=0.95)
    # 灯泡（发光）
    sphere("LampBulb", 8, (-150, 200, 120), col_name="mat_bulb", hex_c="fffacd", rough=0.1)

    # 皮质桌垫
    box("DeskPad", (250, 150, 3), (-150, 200, 184), col_name="mat_leather", hex_c="3d2210", rough=0.7)

    # 地球仪
    sphere("SageGlobe", 50, (400, -200, 50), col_name="mat_globe_sage", hex_c="1e4a6a", rough=0.4)
    cylinder("SageGlobeStand", 5, 70, (400, -200, 0), col_name="mat_brass", hex_c="b8860b", rough=0.3, metallic=0.8)
    box("SageGlobeBase", (70, 70, 5), (400, -200, -35), col_name="mat_brass", hex_c="b8860b", rough=0.3, metallic=0.8)

    # 望远镜
    cylinder("TelescopeTube", 10, 100, (480, -250, 150), rot=(0.3, 0.5, 0), col_name="mat_brass", hex_c="b8860b", rough=0.3, metallic=0.8)
    cylinder("TelescopeLeg1", 3, 80, (460, -200, 0), rot=(0, 0, 0.3), col_name="mat_wood_dark", hex_c="3d2210", rough=0.6)
    cylinder("TelescopeLeg2", 3, 80, (500, -200, 0), rot=(0, 0, -0.3), col_name="mat_wood_dark", hex_c="3d2210", rough=0.6)

    # 琴叶榕（大盆栽）
    cylinder("SagePot", 30, 40, (-400, 200, 20), col_name="mat_pot_sage", hex_c="8b4513", rough=0.8)
    sphere("SagePlant", 50, (-400, 200, 100), col_name="mat_plant_sage", hex_c="228b22", rough=0.9)

    # 博物馆地图（卷轴）
    box("MapScroll", (5, 5, 150), (450, -430, 300), col_name="mat_scroll", hex_c="f5f5dc", rough=0.9)

    print("✅ Sage 智慧书房 完成")

# ─────────────────────────────────────────────────────────────────
# 导出 GLB
# ─────────────────────────────────────────────────────────────────
def export_room(name, filename):
    # Select all objects
    bpy.ops.object.select_all(action='SELECT')
    # Export GLB
    bpy.ops.export_scene.gltf(
        filepath=OUT_DIR + filename,
        export_format='GLB',
        use_selection=False,
        export_materials='EXPORT'
    )
    print(f"  → 导出 {filename}")

# ─────────────────────────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    rooms = [
        ("luna",  "baked_luna_room.glb",  build_luna_room),
        ("kai",   "baked_kai_room.glb",   build_kai_room),
        ("nova",  "baked_nova_room.glb",  build_nova_room),
        ("milo",  "baked_milo_room.glb",  build_milo_room),
        ("sage",  "baked_sage_room.glb",  build_sage_room),
    ]

    for name, fname, builder in rooms:
        print(f"\n{'='*50}")
        print(f"Building {name} room...")
        # Clear scene
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        # Build
        builder()
        # Export
        export_room(name, fname)
        print(f"✅ {name} 完成!")

    print(f"\n🎉 全部完成！文件保存在: {OUT_DIR}")
