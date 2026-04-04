"""
共生境 - 5个高质量房间 Blender 脚本
用法: /snap/bin/blender --background --python gen_5_rooms_v2.py
输出: /static/3droom/assets/rooms_v2/
"""
import bpy, os, math, random

OUT_DIR = os.path.dirname(os.path.abspath(__file__)) + "/assets/rooms_v2/"
os.makedirs(OUT_DIR, exist_ok=True)

# ── 清理 ──────────────────────────────────────────────────────────
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.materials): bpy.data.materials.remove(m)

# ── 材质库 ────────────────────────────────────────────────────────
def mat(name, hex_c, rough=0.5, metallic=0.0, alpha_val=1.0, trans_val=0.0):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name=name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        r = int(hex_c[0:2],16)/255
        g = int(hex_c[2:4],16)/255
        b = int(hex_c[4:6],16)/255
        bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metallic
        if alpha_val < 1.0:
            m.blend_method = 'BLEND'
            bsdf.inputs["Alpha"].default_value = alpha_val
        if trans_val > 0:
            bsdf.inputs["Transmission Weight"].default_value = trans_val
    return m

def am(obj, mn, hc, rough=0.5, metallic=0.0, alpha_val=1.0, trans_val=0.0):
    m = mat(mn, hc, rough, metallic, alpha_val, trans_val)
    if obj.data.materials: obj.data.materials[0] = m
    else: obj.data.materials.append(m)
    return m

# ── 几何部件 ──────────────────────────────────────────────────────
def box(name, sx, sy, sz, lx, ly, lz, mn, hc, rough=0.6, metallic=0.0, alpha_val=1.0, trans_val=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(lx,ly,lz))
    o = bpy.context.active_object; o.name = name
    o.scale = (sx, sy, sz); bpy.ops.object.transform_apply()
    am(o, mn, hc, rough, metallic, alpha_val, trans_val); return o

def cyl(name, r, h, lx, ly, lz, rx=0, ry=0, rz=0, mn='m', hc='999999', rough=0.6, metallic=0.0, alpha_val=1.0, trans_val=0.0):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=(lx,ly,lz), rotation=(rx,ry,rz))
    o = bpy.context.active_object; o.name = name; bpy.ops.object.transform_apply()
    am(o, mn, hc, rough, metallic, alpha_val, trans_val); return o

def sph(name, r, lx, ly, lz, mn='m', hc='999999', rough=0.6, alpha_val=1.0, trans_val=0.0):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(lx,ly,lz))
    o = bpy.context.active_object; o.name = name; bpy.ops.object.transform_apply()
    am(o, mn, hc, rough); return o

def cone(name, r1, r2, h, lx, ly, lz, rx=0, ry=0, rz=0, mn='m', hc='cccccc', rough=0.6):
    bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=h, location=(lx,ly,lz), rotation=(rx,ry,rz))
    o = bpy.context.active_object; o.name = name; bpy.ops.object.transform_apply()
    am(o, mn, hc, rough); return o

def plane(name, sx, sy, lx, ly, lz, mn, hc, rough=0.6):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(lx,ly,lz))
    o = bpy.context.active_object; o.name = name
    o.scale = (sx, sy, 1); bpy.ops.object.transform_apply()
    am(o, mn, hc, rough); return o

# ─────────────────────────────────────────────────────────────────
# 通用基础房间
# ─────────────────────────────────────────────────────────────────
def create_base_room(W=1200, D=1000, H=400, wall_col='e8e0d5', ceil_col='f5f0e8', floor_col='c8a87a', floor_rough=0.7):
    """地板 + 天花板 + 4面墙"""
    box('Floor', W/2, D/2, 10, 0, 0, -5, 'mFloor', floor_col, floor_rough)
    box('Ceiling', W/2, D/2, 10, 0, 0, H+5, 'mCeil', ceil_col, 0.9)
    box('BackWall', W/2, 10, H/2, 0, -D/2, H/2, 'mWall', wall_col, 0.85)
    box('LeftWall', 10, D/2, H/2, -W/2, 0, H/2, 'mWall2', wall_col, 0.85)
    box('RightWall', 10, D/2, H/2, W/2, 0, H/2, 'mWall3', wall_col, 0.85)
    # 前墙（留门洞）
    box('FrontWall_L', 10, D/2, H/2, -W/2, 0, H/2, 'mWall4', wall_col, 0.85)
    box('FrontWall_R', 10, D/2, H/2, W/2, 0, H/2, 'mWall5', wall_col, 0.85)
    box('FrontWall_T', W/2, 10, H*0.7, 0, D/2, H*0.7, 'mWall6', wall_col, 0.85)

def hex_to_rgb(h):
    return (int(h[0:2],16)/255, int(h[2:4],16)/255, int(h[4:6],16)/255)

def add_point_light(name, lx, ly, lz, energy=100, color='ffffff'):
    bpy.ops.object.light_add(type='POINT', location=(lx, ly, lz))
    light = bpy.context.active_object
    light.name = name
    light.data.energy = energy
    light.data.color = hex_to_rgb(color)
    return light

def add_spot_light(name, lx, ly, lz, energy=100, color='ffffff', angle=0.5):
    bpy.ops.object.light_add(type='SPOT', location=(lx, ly, lz))
    light = bpy.context.active_object
    light.name = name
    light.data.energy = energy
    light.data.color = hex_to_rgb(color)
    light.data.spot_size = angle
    return light

# ─────────────────────────────────────────────────────────────────
# Room 1: OFFICE - 深灰现代风格
# ─────────────────────────────────────────────────────────────────
def build_office():
    W, D, H = 1200, 1000, 400
    create_base_room(W, D, H,
        wall_col='2a2e35', ceil_col='1e2025', floor_col='1a1510', floor_rough=0.4)

    # 升降桌（深灰金属）
    box('DeskTop', 240, 110, 6, 0, 100, 160, 'mDesk', '1a1a1a', 0.3, 0.1)
    for (lx, ly) in [(-105, 100), (105, 100)]:
        box(f'DeskLeg_{lx}', 6, 6, 160, lx, ly, 80, 'mMetal', '2a2a2a', 0.2, 0.9)
    box('DeskFB', 240, 6, 6, 0, 155, 160, 'mMetal', '333333', 0.2, 0.8)

    # 双屏显示器
    for i, sx in enumerate([-90, 90]):
        box(f'Mon_{i}', 85, 5, 58, sx, 60, 215, 'mMon', '111111', 0.2, 0.4)
        box(f'MonScr_{i}', 76, 2, 50, sx, 56, 215, 'mScr', '0a2040', 0.1, 0.0)
        mat(f'mScr{i}', '0066cc', 0.05)  # 蓝色屏幕
        o = bpy.data.objects.get(f'MonScr_{i}')
        if o: am(o, f'mScr{i}', '0066cc', 0.05)
        cyl(f'MonSt_{i}', 4, 45, sx, 80, 188, 0,0,0, 'mMetal2', '444444', 0.2, 0.9)
        box(f'MonBa_{i}', 40, 5, 18, sx, 80, 182, 'mMetal2', '444444', 0.2, 0.9)
    # 副屏（竖）
    box('Mon_2', 50, 5, 80, 0, 60, 210, 'mMon2', '111111', 0.2, 0.4)
    mat('mScr2', '1a3a1a', 0.05)
    o = bpy.data.objects.get('Mon_2')
    if o and o.data.materials: o.data.materials[0] = mat('mScr2', '1a3a1a', 0.05)

    # 机械键盘
    box('KB', 110, 35, 8, 0, 70, 168, 'mKB', '1a1a1a', 0.6)
    mat('mKey', '333333', 0.8)
    o = bpy.data.objects.get('KB')
    if o and o.data.materials: o.data.materials[0] = mat('mKey', '333333', 0.8)

    # 人体工学椅（深色）
    box('CSeat', 100, 90, 10, 0, 0, 100, 'mChair', '1a1a1a', 0.8)
    box('CBack', 100, 10, 130, 0, -40, 165, 'mChair2', '1a1a1a', 0.8)
    box('CArmL', 10, 80, 50, -55, 0, 120, 'mChair3', '222222', 0.7)
    box('CArmR', 10, 80, 50, 55, 0, 120, 'mChair4', '222222', 0.7)
    cyl('CPis', 5, 80, 0, 0, 50, 0,0,0, 'mMetal3', '333333', 0.2, 0.9)
    for i, a in enumerate(range(5)):
        ang = a * 2 * math.pi / 5
        cyl(f'CLeg{i}', 4, 5, 55*math.cos(ang), 55*math.sin(ang), 15, 0,0,0, 'mMetal3', '333333', 0.2, 0.9)
        box(f'CLegB{i}', 50, 5, 5, 55*math.cos(ang), 55*math.sin(ang), 5, 'mMetal3', '333333', 0.2, 0.9)
    box('CHead', 70, 10, 35, 0, -55, 235, 'mChair5', '1a1a1a', 0.8)

    # 桌上摆件 - 地球仪
    cyl('GlobeBase', 20, 5, 0, 135, 163, 0,0,0, 'mMetal4', 'b8860b', 0.3, 0.8)
    cyl('GlobePole', 4, 50, 0, 135, 188, 0,0,0, 'mMetal4', 'b8860b', 0.3, 0.8)
    sph('Globe', 22, 0, 135, 215, 'mGlobe', '1e5a8a', 0.4)
    # 经纬线用不同颜色
    mat('mLand', '2e8b57', 0.6)
    o = bpy.data.objects.get('Globe')
    if o and o.data.materials: o.data.materials[0] = mat('mLand', '2e8b57', 0.6)

    # 台灯（宜家风格）
    cyl('LampBase2', 18, 4, 120, 170, 163, 0,0,0, 'mMetal5', 'cccccc', 0.3, 0.8)
    cyl('LampArm', 3, 100, 120, 170, 168, 0,0,math.pi/4, 'mMetal5', 'cccccc', 0.3, 0.8)
    cone('LampShade2', 30, 8, 35, 145, 190, 215, 0,0,0, 'mShade', 'f5f5dc', 0.95)
    add_point_light('DeskLamp', 145, 190, 200, energy=80, color='fff5d0')

    # 开放书架（整面侧墙）
    for i in range(6):
        bh = i * 60 + 5
        box(f'BSH{i}', 180, 25, 6, -500, 200, bh, 'mWood', '3d2b1f', 0.6)
    box('BSHBack', 180, 6, 380, -500, 212, 180, 'mWood2', '2d1a0a', 0.6)
    box('BSHSideL', 6, 25, 380, -590, 200, 180, 'mWood3', '3d2b1f', 0.6)
    box('BSHSideR', 6, 25, 380, -410, 200, 180, 'mWood3', '3d2b1f', 0.6)
    # 书脊
    book_cols = ['196aff','cc2222','22aa22','daa520','8b008b','cd853f','2f4f4f','b8860b','483d8b','006400']
    for i in range(28):
        bx = -575 + (i % 4) * 42 + (i // 4) * 3
        bh = 10 + (i // 4) * 60
        bhr = 35 + (i % 3) * 12
        bc = book_cols[i % len(book_cols)]
        box(f'OB{i}', 35, 20, bhr, bx, 208, bh + bhr//2, f'mOB{i}', bc, 0.8)

    # 墙面装饰 - 极简时钟
    cyl('Clock', 30, 3, -500, -480, 280, 0,0,0, 'mClock', 'ffffff', 0.3)
    mat('mClockFace', 'f0f0f0', 0.2)
    o = bpy.data.objects.get('Clock')
    if o and o.data.materials: o.data.materials[0] = mat('mClockFace', 'f0f0f0', 0.2)
    for i in range(12):
        ang = i * math.pi / 6
        bx = -500 + 20 * math.cos(ang)
        bz = 280 + 20 * math.sin(ang)
        sph(f'Tick{i}', 2, bx, -480, bz, 'mTick', '333333', 0.5)

    # 咖啡机
    box('CoffeeMach', 55, 45, 80, 420, 200, 40, 'mCoffee', '2a2a2a', 0.4, 0.2)
    box('CoffeeDrip', 40, 30, 5, 420, 180, 5, 'mCoffee2', '333333', 0.5)
    add_point_light('CoffeeL', 420, 180, 85, energy=15, color='ff6600')

    # 脚凳
    box('Footrest', 80, 60, 20, 0, -80, 10, 'mFoot', '2a2a2a', 0.8)

    # 落地灯
    cyl('FLeg', 4, 180, 400, 200, 0, 0,0,0, 'mMetal6', 'c0c0c0', 0.2, 0.9)
    cyl('FLamp', 35, 30, 400, 200, 190, 0,0,0, 'mShade2', 'f5f5dc', 0.95)
    add_point_light('FloorLamp', 400, 200, 175, energy=50, color='fff0d0')

    # 门
    box('DoorFrame', 100, 8, 240, 550, 500, 120, 'mDoorF', '3d2b1f', 0.6)
    box('DoorPanel', 90, 6, 230, 550, 505, 120, 'mDoor', '4a3728', 0.7)
    box('DoorHandle', 6, 6, 20, 505, 505, 120, 'mMetal7', 'b8860b', 0.2, 0.9)

    print("✅ Office 完成")
    return W, D, H

# ─────────────────────────────────────────────────────────────────
# Room 2: BEDROOM - 温馨卧室
# ─────────────────────────────────────────────────────────────────
def build_bedroom():
    W, D, H = 1200, 1000, 400
    create_base_room(W, D, H,
        wall_col='e8ddd0', ceil_col='f8f0e8', floor_col='c8a87a', floor_rough=0.75)

    # 双人床（靠墙）
    box('BedFrame', 260, 200, 30, 0, -250, 15, 'mBF', '8b7355', 0.7)
    box('BedBase2', 250, 190, 20, 0, -250, 40, 'mBM', 'd4c4a0', 0.9)
    box('Mattress', 240, 185, 25, 0, -250, 62, 'mMat', 'f0f0f0', 0.95)
    # 被子
    box('Comforter', 235, 160, 18, 0, -240, 85, 'mComf', 'e8d4c8', 0.95)
    # 枕头
    for px in [-65, 65]:
        box(f'Pil_{px}', 80, 40, 18, px, -255, 90, 'mPil', 'fff8f0', 0.95)
        # 枕套纹路
        mat(f'mPilT{px}', 'fff0e8', 0.95)
        o = bpy.data.objects.get(f'Pil_{px}')
        if o and o.data.materials: o.data.materials[0] = mat(f'mPilT{px}', 'fff0e8', 0.95)
    # 床头板
    box('HeadBoard', 260, 15, 120, 0, -355, 90, 'mHB', '8b7355', 0.7)
    # 床头柜 × 2
    for sx in [-170, 170]:
        box(f'NS_{sx}', 55, 45, 50, sx, -340, 25, 'mNS', 'a08060', 0.7)
        box(f'NST_{sx}', 58, 48, 4, sx, -340, 52, 'mNST', '8b7355', 0.7)
        # 抽屉把手
        box(f'NSH_{sx}', 20, 4, 4, sx, -340, 35, 'mMetalH', 'c0c0c0', 0.2, 0.9)
    # 床头灯
    for sx in [-170, 170]:
        cyl(f'BT_{sx}', 8, 35, sx, -340, 80, 0,0,0, 'mBrass', 'b8860b', 0.3, 0.8)
        sph(f'BD_{sx}', 15, sx, -340, 95, 'mBD', 'fffacd', 0.3)
        add_point_light(f'BedL_{sx}', sx, -340, 90, energy=30, color='ffd700')

    # 衣柜
    box('Wardrobe', 200, 70, 280, -400, 250, 140, 'mWD', 'c8a87a', 0.65)
    for i in range(3):
        box(f'WDoor_{i}', 60, 5, 265, -430+i*65, 250, 140, 'mWD2', 'd4b896', 0.65)
        box(f'WHandle_{i}', 4, 4, 30, -410+i*65, 250, 180, 'mMetW', 'c0c0c0', 0.2, 0.9)
    # 衣柜顶装饰
    box('WDTop', 205, 75, 8, -400, 250, 285, 'mWD3', 'b8977a', 0.6)

    # 梳妆台
    box('Dresser', 120, 45, 80, 350, 200, 40, 'mDR', 'c8a87a', 0.65)
    box('DresserTop', 125, 50, 4, 350, 200, 82, 'mDRT', 'd4b896', 0.6)
    # 镜子
    box('Mirror', 80, 4, 100, 350, 160, 180, 'mMir', 'e8f4f8', 0.05, 0.0)
    mat('mMirF', 'c0d8e8', 0.05, 0.0, 1.0, 0.3)
    o = bpy.data.objects.get('Mirror')
    if o and o.data.materials: o.data.materials[0] = mat('mMirF', 'c0d8e8', 0.05, 0.0, 1.0, 0.3)
    # 化妆品
    for ci, (cx, cz) in enumerate([(320, 90), (335, 88), (350, 91), (370, 89)]):
        cyl(f'Bot_{ci}', 6, 15, cx, 200, cz, 0,0,0, 'mBot', 'ff69b4', 0.4)
        sph(f'Cap_{ci}', 5, cx, 200, cz+10, 'mCap', 'ff1493', 0.4)

    # 窗帘
    for si, sx in enumerate([-350, 350]):
        box(f'Curtain_{si}', 8, 150, 250, sx, -350, 180, 'mCur', 'e8d4f0', 0.9)
    # 窗帘杆
    cyl('CurtainRod', 4, 750, 0, -350, 310, 0, math.pi/2, 0, 'mRod', 'c0c0c0', 0.2, 0.9)
    # 窗
    box('Window', 150, 5, 180, 0, -492, 200, 'mWin', 'aaccdd', 0.1, 0.0, 0.4)
    mat('mWinF', 'aaccdd', 0.05, 0.0, 1.0, 0.4)
    o = bpy.data.objects.get('Window')
    if o and o.data.materials: o.data.materials[0] = mat('mWinF', 'aaccdd', 0.05, 0.0, 1.0, 0.4)

    # 墙画
    for i, (hx, hy, hw, hh, hc) in enumerate([
        (-300, 280, 120, 80, 'e8c8a0'),
        (-130, 280, 80, 100, 'c8a0e8'),
        (50, 280, 100, 70, 'a0e8c8'),
    ]):
        box(f'Frame_{i}', hw, 5, hh, hx, -485, hy, 'mFra', '5c4033', 0.6)
        box(f'Painting_{i}', hw-8, 2, hh-8, hx, -490, hy, f'mPai_{i}', hc, 0.9)

    # 脏衣篓
    cyl('Laundy', 30, 40, 420, 280, 20, 0,0,0, 'mLaun', 'e8e0e0', 0.9)

    # 空调
    box('AC', 140, 20, 45, 0, -480, 360, 'mAC', 'f0f0f0', 0.8)
    add_point_light('ACL', 0, -480, 340, energy=20, color='cceeff')

    print("✅ Bedroom 完成")
    return W, D, H

# ─────────────────────────────────────────────────────────────────
# Room 3: TEA ROOM - 日式茶室
# ─────────────────────────────────────────────────────────────────
def build_tea_room():
    W, D, H = 1200, 1000, 400
    create_base_room(W, D, H,
        wall_col='f5f0e0', ceil_col='fff8e8', floor_col='c8b87a', floor_rough=0.8)

    # 榻榻米地板
    for xi in range(4):
        for yi in range(5):
            bx = -600 + xi * 300 + 150
            by = -500 + yi * 200 + 100
            box(f'Tatami_{xi}_{yi}', 295, 195, 8, bx, by, -4, 'mTat', 'd4c896', 0.85)

    # 矮茶几
    box('TTop', 160, 90, 6, 0, 50, 80, 'mTeaW', 'a08060', 0.65)
    for (lx, ly) in [(-65, 15), (-65, 85), (65, 15), (65, 85)]:
        box(f'TLeg_{lx}', 8, 8, 75, lx, ly, 37, 'mTeaW2', '8b7355', 0.7)
    # 茶具
    cyl('Teapot', 18, 25, -20, 50, 95, 0,0,0, 'mTea', 'd2691e', 0.5)
    cyl('Teacup1', 9, 12, 20, 45, 92, 0,0,0, 'mTea2', 'f5f5dc', 0.6)
    cyl('Teacup2', 9, 12, 35, 60, 92, 0,0,0, 'mTea3', 'f5f5dc', 0.6)
    # 茶盘
    box('Tray', 80, 50, 4, 10, 60, 88, 'mTray', '8b7355', 0.6)
    # 茶巾
    box('Chakin', 40, 20, 2, -50, 55, 87, 'mChakin', 'f5f5f0', 0.9)
    # 茶杓
    cyl('Chasaku', 2, 40, -40, 50, 88, 0,0,0.3, 'mCha', '8b7355', 0.6)

    # 蒲团坐垫 × 4
    for (qx, qy) in [(-180, 100), (0, 100), (180, 100), (0, -50)]:
        cyl(f'Zabuton_{qx}', 55, 15, qx, qy, 15, 0,0,0, 'mZab', '5a7a5a', 0.95)
        mat(f'mZabF{qx}', '6a8a6a', 0.95)
        o = bpy.data.objects.get(f'Zabuton_{qx}')
        if o and o.data.materials: o.data.materials[0] = mat(f'mZabF{qx}', '6a8a6a', 0.95)

    # 竹屏风（隔断）
    for pi in range(4):
        for hi in range(4):
            cyl(f'PaneL_{pi}_{hi}', 3, 200, -520+pi*25, 100+hi*3, 180, 0, 0, 0, 'mBamb', '8fbc8f', 0.8)
    box('PaneF', 110, 4, 200, -490, 100, 180, 'mPane', 'f5f0e0', 0.9)

    # 竹子装饰
    for i in range(10):
        bx = -570 + i * 40 + (i % 2) * 20
        by = -420 + (i % 3) * 25
        h = 300 + (i % 4) * 40
        cyl(f'Bamboo_{i}', 6, h, bx, by, h/2, 0,0,0, 'mBam2', '8fbc8f', 0.75)
        for li in range(4):
            box(f'BamNode_{i}_{li}', 14, 14, 4, bx, by, 50+li*70, 'mBam3', '7aab7a', 0.8)

    # 枯山水（角落）
    box('ZenBox', 200, 120, 8, 400, -350, 4, 'mZen', '8b8370', 0.9)
    # 白砂
    for si in range(25):
        sx = 330 + (si % 5) * 30 + random.randint(-5,5)
        sz = -380 + (si // 5) * 30 + random.randint(-5,5)
        sph(f'Sand_{si}', 10, sx, -350, sz, 'mSand', 'f5f0dc', 0.95)
    # 枯山石
    for ri, (rx, rz) in enumerate([(380, -360), (420, -340), (360, -320)]):
        sph(f'Rock_{ri}', 25+ri*10, rx, -350, rz, 'mRk', '696969', 0.9)
    # 松树（小）
    cyl(f'PineT{ri}', 4, 60, 440, -340, 30, 0,0,0, 'mPin', '5c3317', 0.7)
    sph(f'PineC{ri}', 30, 440, -340, 80, 'mPin2', '228b22', 0.85)

    # 壁龛（Tokonoma）
    box('TokoBack', 180, 15, 280, 450, -485, 140, 'mToko', 'f5f0e0', 0.9)
    box('TokoFloor', 180, 40, 8, 450, -455, 4, 'mTokoF', 'c8b87a', 0.8)
    box('TokoPole', 8, 8, 280, 365, -485, 140, 'mTPole', '8b7355', 0.7)
    # 挂画
    box('Kake', 80, 4, 120, 450, -475, 200, 'mKake', '2a2015', 0.7)
    box('KakeMat', 72, 2, 108, 450, -480, 200, 'mKM', 'f5f0dc', 0.9)
    # 水墨山水模拟
    box('KImg1', 50, 2, 60, 445, -481, 190, 'mKI1', '3a3a3a', 0.95)
    box('KImg2', 60, 2, 40, 450, -481, 160, 'mKI2', '4a4a4a', 0.95)
    box('KImg3', 40, 2, 50, 455, -481, 185, 'mKI3', '2a2a2a', 0.95)
    # 花瓶
    cyl('Vase', 15, 40, 420, -445, 20, 0,0,0, 'mVase', 'd2956a', 0.4)
    # 仿真花
    for fi, (fx, fz, fc) in enumerate([(415, 5, 'ff69b4'),(425, 8, 'ff1493'),(420, 0, 'ff69b4'),(410, 10, 'ffffff')]):
        cyl(f'Flower_{fi}', 6, 35, 420+fx, -445, 55+fz, 0,0,0, 'mFl', fc, 0.5)
        sph(f'Bloom_{fi}', 8, 420+fx, -445, 72+fz, 'mBl', fc, 0.4)

    # 纸灯笼（天花板中央）
    sph('Lantern', 60, 0, 0, 375, 'mLan', 'fff5d0', 0.95)
    add_point_light('LanternL', 0, 0, 360, energy=80, color='ffd070')
    cyl('LanternCord', 2, 80, 0, 0, 320, 0,0,0, 'mCord', 'd4c4a0', 0.9)

    # 线香
    cyl('Incense', 1.5, 45, 80, 50, 87, 0,0,0, 'mInc', '8b4513', 0.8)
    sph('IncTip', 3, 80, 50, 115, 'mIncT', 'ff4500', 0.3)
    add_point_light('IncL', 80, 50, 110, energy=8, color='ff6633')

    print("✅ Tea Room 完成")
    return W, D, H

# ─────────────────────────────────────────────────────────────────
# Room 4: LIVING ROOM - 现代客厅
# ─────────────────────────────────────────────────────────────────
def build_living_room():
    W, D, H = 1200, 1000, 400
    create_base_room(W, D, H,
        wall_col='f0ebe0', ceil_col='ffffff', floor_col='d4b896', floor_rough=0.6)

    # L型沙发
    box('SofaBase', 240, 120, 40, -100, 0, 20, 'mSofa', '4a7a9a', 0.85)
    box('SofaBack', 240, 15, 90, -100, -55, 85, 'mSofa2', '4a7a9a', 0.85)
    box('SofaArmL', 15, 120, 60, -225, 0, 50, 'mSofa3', '3a6a8a', 0.85)
    box('SofaArmR', 15, 80, 60, 20, 40, 50, 'mSofa4', '3a6a8a', 0.85)
    # 沙发坐垫
    for si, (sx, sy) in enumerate([(-170, 20), (-100, 20), (-30, 20), (-170, -20), (-100, -20)]):
        box(f'SC_{si}', 55, 55, 15, sx, sy, 55, 'mSC', '5a8aaa', 0.9)
    # 抱枕
    for pi, (px, py, pc) in enumerate([(-180, 10, 'ff6b6b'), (-120, 15, 'ffd93d'), (-60, 10, '6bcb77'), (10, 20, '4d96ff')]):
        box(f'Pillow_{pi}', 40, 15, 40, px, py, 65, f'mPil_{pi}', pc, 0.9)

    # 茶几（玻璃+金属）
    box('CTop', 140, 80, 4, 150, 0, 75, 'mGlass', 'aaccdd', 0.05, 0.0, 0.6)
    mat('mGT', '88aacc', 0.05, 0.0, 1.0, 0.5)
    o = bpy.data.objects.get('CTop')
    if o and o.data.materials: o.data.materials[0] = mat('mGT', '88aacc', 0.05, 0.0, 1.0, 0.5)
    for (lx, ly) in [(-60, -30), (-60, 30), (60, -30), (60, 30)]:
        cyl(f'CMetal_{lx}', 4, 70, 150+lx, ly, 35, 0,0,0, 'mCM', 'c0c0c0', 0.2, 0.9)
    # 茶几上的物品
    box('Magazine', 50, 35, 4, 140, 10, 79, 'mMag', 'f0f0f0', 0.9)
    cyl('Vase2', 12, 30, 170, 0, 87, 0,0,0, 'mVase2', '2d6a4f', 0.3)
    sph('VFlower', 12, 170, 0, 100, 'mVF', 'ff69b4', 0.4)

    # 电视柜 + 电视
    box('TVStand', 200, 45, 60, 0, -350, 30, 'mTVS', '2a2a2a', 0.4, 0.1)
    box('TVTop', 205, 48, 4, 0, -350, 62, 'mTVT', '333333', 0.4, 0.1)
    box('TV', 200, 8, 115, 0, -350, 175, 'mTV', '0a0a0a', 0.2)
    mat('mTVScr', '0a0a1a', 0.05)
    o = bpy.data.objects.get('TV')
    if o and o.data.materials: o.data.materials[0] = mat('mTVScr', '0a0a1a', 0.05)
    add_point_light('TVL', 0, -350, 170, energy=30, color='4080ff')

    # 音响（Soundbar）
    box('Soundbar', 150, 15, 12, 0, -350, 70, 'mSB', '1a1a1a', 0.5)
    # 电视柜抽屉
    for i in range(3):
        box(f'TVDr{i}', 58, 5, 40, -65+i*65, -340, 35, 'mTVD', '333333', 0.5)
        box(f'TVDH{i}', 15, 3, 3, -65+i*65, -340, 45, 'mTVH', '666666', 0.3, 0.7)

    # 角落绿植
    cyl('Pot1', 30, 40, -520, 280, 20, 0,0,0, 'mPot', '8b4513', 0.8)
    sph('Plant1', 55, -520, 280, 90, 'mPl1', '228b22', 0.9)
    cyl('Trunk1', 8, 50, -520, 280, 25, 0,0,0, 'mTrunk', '5c3317', 0.7)
    # 第二棵绿植
    cyl('Pot2', 22, 30, -520, 180, 15, 0,0,0, 'mPot2', '8b4513', 0.8)
    sph('Plant2', 35, -520, 180, 70, 'mPl2', '2e8b57', 0.9)

    # 落地灯
    cyl('FLeg2', 4, 160, 450, 280, 0, 0,0,0, 'mFLeg', 'c0c0c0', 0.2, 0.9)
    cone('FShade', 40, 15, 40, 450, 280, 180, 0,0,0, 'mFShd', 'f5f5dc', 0.95)
    add_point_light('FL2', 450, 280, 165, energy=60, color='fff0d0')

    # 墙面装饰 - 抽象画
    box('ArtFrame', 180, 5, 100, -400, -485, 250, 'mAF', '1a1a1a', 0.5)
    box('ArtCanvas', 170, 2, 90, -400, -490, 250, 'mACan', 'e8e0d0', 0.9)
    # 抽象色块
    for ci, (cx, cz, cc) in enumerate([(-450, 280, 'ff6b6b'), (-420, 270, '4d96ff'), (-390, 285, 'ffd93d'), (-450, 240, '6bcb77'), (-410, 235, 'ff9f43')]):
        box(f'ArtB{ci}', 35, 2, 30, cx, -491, cz, f'mAB{ci}', cc, 0.9)

    # 边几
    box('SideT', 60, 50, 4, 350, 150, 110, 'mST', 'c8a87a', 0.65)
    for (lx, ly) in [(-25, -20), (-25, 20), (25, -20), (25, 20)]:
        cyl(f'STL_{lx}', 3, 105, 350+lx, 150+ly, 52, 0,0,0, 'mSTM', 'c0c0c0', 0.2, 0.9)
    # 边几上的台灯
    cyl('SLBase', 12, 4, 350, 150, 4, 0,0,0, 'mSLB', 'c0c0c0', 0.3, 0.8)
    cyl('SLArm', 3, 80, 350, 150, 80, 0,0,0.3, 'mSLA', 'c0c0c0', 0.3, 0.8)
    cone('SLShd', 25, 10, 30, 365, 170, 140, 0,0,0, 'mSLS', 'f5f0dc', 0.95)
    add_point_light('SLL', 365, 170, 125, energy=40, color='ffd700')

    # 地毯
    box('Rug', 400, 300, 3, 0, 0, -8, 'mRug', 'c87070', 0.95)
    mat('mRugB', 'a05050', 0.95)
    o = bpy.data.objects.get('Rug')
    if o and o.data.materials: o.data.materials[0] = mat('mRugB', 'a05050', 0.95)
    # 地毯图案
    box('RugPat', 380, 280, 1, 0, 0, -9, 'mRugP', 'd09090', 0.95)

    print("✅ Living Room 完成")
    return W, D, H

# ─────────────────────────────────────────────────────────────────
# Room 5: READING ROOM - 古典书房
# ─────────────────────────────────────────────────────────────────
def build_reading_room():
    W, D, H = 1200, 1000, 400
    create_base_room(W, D, H,
        wall_col='e8dcc8', ceil_col='f8f4e8', floor_col='5c3317', floor_rough=0.45)

    # 地板 - 深木
    o = bpy.data.objects.get('Floor')
    if o and o.data.materials: o.data.materials[0] = mat('mFloor2', '5c3317', 0.4)

    # 墙面护墙板（下半部）
    box('WP_B', W/2, 8, 180, 0, -492, 90, 'mWP', '3d2210', 0.6)
    box('WP_L', 8, D/2, 180, -W/2+4, 0, 90, 'mWP2', '3d2210', 0.6)
    box('WP_R', 8, D/2, 180, W/2-4, 0, 90, 'mWP3', '3d2210', 0.6)

    # 墙线（腰线）
    box('ChairRail', W/2+10, 8, 4, 0, -492, 185, 'mCR', '5c4033', 0.6)
    box('CRL', 8, D/2+10, 4, -W/2+4, 0, 185, 'mCR2', '5c4033', 0.6)
    box('CRR', 8, D/2+10, 4, W/2-4, 0, 185, 'mCR3', '5c4033', 0.6)

    # 整面书墙
    box('BWallBack', 580, 10, 380, -340, -480, 190, 'mBW', '2d1a0a', 0.6)
    for sx in [-650, -30]:
        box(f'BWSide_{sx}', 8, 30, 380, sx, -480, 190, 'mBW2', '3d2210', 0.6)
    for i in range(7):
        bh = i * 55 + 5
        box(f'BSH_{i}', 620, 30, 6, -340, -480, bh, 'mBSH', '2d1a0a', 0.6)

    # 书（古典藏书风格）
    book_cols_sage = ['8b0000','00008b','006400','800000','191970','4b0082','8b4513','2f4f4f','556b2f','b8860b']
    for i in range(45):
        bx = -635 + (i % 6) * 98 + (i // 6) * 4
        bh = 8 + (i // 6) * 55
        bhr = 38 + (i % 4) * 8
        bc = book_cols_sage[i % len(book_cols_sage)]
        box(f'RB{i}', 85, 22, bhr, bx, -482, bh + bhr//2, f'mRB{i}', bc, 0.8)
        # 烫金装饰（用黄色细条模拟）
        if i % 3 == 0:
            box(f'RBS_{i}', 3, 22, bhr-10, bx+35, -484, bh + bhr//2, f'mRBS{i}', 'daa520', 0.8)

    # 阅读椅（皮革）
    box('RChairS', 130, 120, 15, 200, 100, 85, 'mLth', '5c3317', 0.7)
    box('RChairB', 130, 15, 130, 200, 50, 160, 'mLth2', '5c3317', 0.7)
    box('RChairAL', 15, 100, 70, 135, 100, 115, 'mLth3', '4a2810', 0.7)
    box('RChairAR', 15, 100, 70, 265, 100, 115, 'mLth4', '4a2810', 0.7)
    cyl('RCL_Fl', 5, 75, 150, 170, 35, 0,0,0, 'mBrass', 'b8860b', 0.3, 0.8)
    cyl('RCL_Fr', 5, 75, 250, 170, 35, 0,0,0, 'mBrass', 'b8860b', 0.3, 0.8)
    cyl('RCL_Bl', 5, 75, 150, 170, 35, 0,0,0, 'mBrass', 'b8860b', 0.3, 0.8)
    cyl('RCL_Br', 5, 75, 250, 170, 35, 0,0,0, 'mBrass', 'b8860b', 0.3, 0.8)
    # 脚凳
    box('FOttoman', 100, 80, 20, 200, 200, 10, 'mOtt', '5c3317', 0.7)
    cyl('OCL_1', 4, 50, 165, 235, 5, 0,0,0, 'mBrass2', 'b8860b', 0.3, 0.8)
    cyl('OCL_2', 4, 50, 235, 235, 5, 0,0,0, 'mBrass2', 'b8860b', 0.3, 0.8)
    cyl('OCL_3', 4, 50, 165, 165, 5, 0,0,0, 'mBrass2', 'b8860b', 0.3, 0.8)
    cyl('OCL_4', 4, 50, 235, 165, 5, 0,0,0, 'mBrass2', 'b8860b', 0.3, 0.8)

    # 古典书桌
    box('RDesk', 200, 90, 6, -100, 200, 165, 'mDeskW', '5c3317', 0.6)
    for (lx, ly) in [(-185, 160), (-185, 240), (-15, 160), (-15, 240)]:
        box(f'RDL_{lx}', 8, 8, 160, lx, ly, 80, 'mDeskW2', '4a2810', 0.65)
    # 桌垫（皮革）
    box('RDeskPad', 180, 75, 3, -100, 200, 171, 'mRDP', '3d2210', 0.7)
    # 台灯（黄铜古典）
    cyl('RLBase', 22, 5, -180, 200, 5, 0,0,0, 'mBrass3', 'b8860b', 0.3, 0.8)
    cyl('RLPole', 5, 110, -180, 200, 60, 0,0,0, 'mBrass3', 'b8860b', 0.3, 0.8)
    cyl('RLBase2', 12, 30, -180, 200, 130, 0,0,0, 'mBrass3', 'b8860b', 0.3, 0.8)
    cone('RLShade', 35, 15, 45, -180, 200, 165, 0,0,0, 'mRShd', 'f5deb3', 0.95)
    sph('RLBulb', 8, -180, 200, 150, 'mRBulb', 'fffacd', 0.1)
    add_point_light('RLL', -180, 200, 145, energy=90, color='ffd700')

    # 地球仪
    cyl('RGlobeS', 5, 70, 80, 200, 0, 0,0,0, 'mRGb', 'b8860b', 0.3, 0.8)
    sph('RGlobe', 50, 80, 200, 70, 'mRGl', '1e4a6a', 0.4)
    mat('mRGLa', '2e8b57', 0.5)
    o = bpy.data.objects.get('RGlobe')
    if o and o.data.materials: o.data.materials[0] = mat('mRGLa', '2e8b57', 0.5)
    box('RGlobeB', 70, 70, 5, 80, 200, -30, 'mRGb2', 'b8860b', 0.3, 0.8)

    # 墙上地图（古典风格）
    box('MapFrame', 160, 5, 110, 400, -485, 260, 'mMF', '5c4033', 0.6)
    box('MapC', 148, 2, 98, 400, -490, 260, 'mMC', 'e8dcc8', 0.9)
    # 地图色块（海洋/陆地）
    mat('mOcean', 'c8d8e8', 0.8)
    o = bpy.data.objects.get('MapC')
    if o and o.data.materials: o.data.materials[0] = mat('mOcean', 'c8d8e8', 0.8)
    for li, (lx, lz, lw, lh, lc) in enumerate([(370, 290, 30, 25, '8b7355'), (400, 280, 40, 30, '6a8a6a'), (420, 265, 20, 20, '8b7355'), (385, 260, 25, 18, '6a8a6a')]):
        box(f'ML{li}', lw, 2, lh, lx, -491, lz, f'mML{li}', lc, 0.9)

    # 书架上的地球仪（小）
    cyl('BGlobeS', 3, 35, -550, 280, 17, 0,0,0, 'mBGlS', 'b8860b', 0.3, 0.8)
    sph('BGlobe', 20, -550, 280, 52, 'mBGl', '1e4a6a', 0.4)
    mat('mBGLand', '228b22', 0.5)
    o = bpy.data.objects.get('BGlobe')
    if o and o.data.materials: o.data.materials[0] = mat('mBGLand', '228b22', 0.5)

    # 望远镜
    cyl('TelTube', 10, 90, 450, -250, 130, 0.3, 0.5, 0, 'mTel', 'b8860b', 0.3, 0.8)
    cyl('TelLeg1', 3, 70, 430, -200, 0, 0, 0, 0.3, 'mTelW', '3d2210', 0.6)
    cyl('TelLeg2', 3, 70, 470, -200, 0, 0, 0, -0.3, 'mTelW2', '3d2210', 0.6)

    # 盆栽（琴叶榕）
    cyl('FPot', 35, 45, -350, 200, 22, 0,0,0, 'mFPot', '8b4513', 0.8)
    sph('FPlant', 55, -350, 200, 100, 'mFPl', '228b22', 0.85)

    # 落地窗 + 窗帘
    box('WinFrame', 160, 6, 200, 0, -492, 200, 'mWF', '5c4033', 0.6)
    box('WinGlass', 150, 3, 190, 0, -495, 200, 'mWG', 'aaccdd', 0.05, 0.0, 0.4)
    mat('mWGF', '88bbcc', 0.05, 0.0, 1.0, 0.35)
    o = bpy.data.objects.get('WinGlass')
    if o and o.data.materials: o.data.materials[0] = mat('mWGF', '88bbcc', 0.05, 0.0, 1.0, 0.35)
    # 窗帘
    for si, sx in enumerate([-100, 100]):
        box(f'RCur_{si}', 6, 120, 220, sx, -370, 190, 'mRCur', '8b0000', 0.9)
    cyl('RCurRod', 3, 220, 0, -370, 305, 0, math.pi/2, 0, 'mRRod', 'b8860b', 0.3, 0.8)

    # 壁炉时钟
    box('CClock', 80, 8, 80, -450, -480, 300, 'mCC', '5c4033', 0.6)
    cyl('CCFace', 35, 4, -450, -480, 300, 0,0,0, 'mCCF', 'f5f0dc', 0.2)
    mat('mCCFF', 'f5f0dc', 0.2)
    o = bpy.data.objects.get('CCFace')
    if o and o.data.materials: o.data.materials[0] = mat('mCCFF', 'f5f0dc', 0.2)
    for i in range(12):
        ang = i * math.pi / 6
        bx = -450 + 25 * math.cos(ang)
        bz = 300 + 25 * math.sin(ang)
        sph(f'CT{i}', 3, bx, -480, bz, 'mCTT', '333333', 0.5)

    print("✅ Reading Room 完成")
    return W, D, H

# ─────────────────────────────────────────────────────────────────
# 导出
# ─────────────────────────────────────────────────────────────────
def export_gbl(name, fname):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(
        filepath=OUT_DIR + fname,
        export_format='GLB',
        use_selection=False,
        export_materials='EXPORT'
    )
    print(f"  → 导出 {fname}")

# ─────────────────────────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    rooms = [
        ("office",    "room_office.glb",     build_office),
        ("bedroom",   "room_bedroom.glb",    build_bedroom),
        ("tea_room",  "room_tea.glb",        build_tea_room),
        ("living",    "room_living.glb",     build_living_room),
        ("reading",   "room_reading.glb",    build_reading_room),
    ]

    for name, fname, builder in rooms:
        print(f"\n{'='*50}")
        print(f"Building {name}...")
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        for m in list(bpy.data.materials): bpy.data.materials.remove(m)
        builder()
        export_gbl(name, fname)
        print(f"✅ {name} 完成!")

    print(f"\n🎉 全部完成！文件在: {OUT_DIR}")
