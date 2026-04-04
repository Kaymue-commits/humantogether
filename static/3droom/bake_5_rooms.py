"""
共生境 - 5房间烘焙纹理生成脚本
为每个房间生成: bakedNeutral(中性) + lightMap(光影分布图)
用法: /snap/bin/blender --background --python bake_5_rooms.py
"""
import bpy, os, math, sys

OUT_DIR = os.path.dirname(os.path.abspath(__file__)) + "/assets/rooms_v2/"
os.makedirs(OUT_DIR, exist_ok=True)

# ── 清理 ──────────────────────────────────────────────────────────
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.materials): bpy.data.materials.remove(m)
for t in list(bpy.data.textures): bpy.data.textures.remove(t)
for i in list(bpy.data.images): bpy.data.images.remove(i)

# ── 材质 ──────────────────────────────────────────────────────────
def mat(name, hex_c, rough=0.5, metallic=0.0, emission=None):
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
        if emission:
            bsdf.inputs["Emission"].default_value = (*emission, 1.0)
            bsdf.inputs["Emission Strength"].default_value = emission[3] if len(emission) > 3 else 1.0
    return m

def am(obj, mn, hc, rough=0.5, metallic=0.0, emission=None):
    m = mat(mn, hc, rough, metallic, emission)
    if obj.data.materials: obj.data.materials[0] = m
    else: obj.data.materials.append(m)

def box(name, sx, sy, sz, lx, ly, lz, mn, hc, rough=0.6, metallic=0.0, emission=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(lx,ly,lz))
    o = bpy.context.active_object; o.name = name
    o.scale = (sx, sy, sz); bpy.ops.object.transform_apply()
    am(o, mn, hc, rough, metallic, emission); return o

def cyl(name, r, h, lx, ly, lz, rx=0, ry=0, rz=0, mn='m', hc='999999', rough=0.6, metallic=0.0, emission=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=(lx,ly,lz), rotation=(rx,ry,rz))
    o = bpy.context.active_object; o.name = name; bpy.ops.object.transform_apply()
    am(o, mn, hc, rough, metallic, emission); return o

def sph(name, r, lx, ly, lz, mn='m', hc='999999', rough=0.6, metallic=0.0, emission=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(lx,ly,lz))
    o = bpy.context.active_object; o.name = name; bpy.ops.object.transform_apply()
    am(o, mn, hc, rough, metallic, emission); return o

def cone(name, r1, r2, h, lx, ly, lz, rx=0, ry=0, rz=0, mn='m', hc='cccccc', rough=0.6, metallic=0.0, emission=None):
    bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=h, location=(lx,ly,lz), rotation=(rx,ry,rz))
    o = bpy.context.active_object; o.name = name; bpy.ops.object.transform_apply()
    am(o, mn, hc, rough, metallic, emission); return o

# ─────────────────────────────────────────────────────────────────
# Office Room
# ─────────────────────────────────────────────────────────────────
def build_office():
    W, D, H = 1200, 1000, 400
    mat('mFloor', '2a2015', 0.4, 0.0)
    mat('mCeil', '1e2025', 0.9, 0.0)
    mat('mWall', '1e222a', 0.85, 0.0)
    mat('mWall2', '1e222a', 0.85, 0.0)
    mat('mDesk', '1a1a1a', 0.3, 0.1)
    mat('mMetal', '2a2a2a', 0.2, 0.9)
    mat('mScr', '0066cc', 0.05, 0.0, (0.0, 0.4, 1.0, 2.0))  # PC屏幕发光
    mat('mKB', '333333', 0.6, 0.0)
    mat('mChair', '1a1a1a', 0.8, 0.0)
    mat('mChair2', '222222', 0.8, 0.0)
    mat('mGlobe', '1e5a8a', 0.4, 0.0)
    mat('mGlobeLa', '2e8b57', 0.6, 0.0)
    mat('mMetal4', 'b8860b', 0.3, 0.8)
    mat('mLamp', 'f5f5dc', 0.95, 0.0)
    mat('mLampG', 'fff5d0', 0.3, 0.0, (1.0, 0.95, 0.8, 3.0))  # 台灯发光
    mat('mWood', '3d2b1f', 0.6, 0.0)
    mat('mBook', '8b0000', 0.8, 0.0)
    mat('mClock', '333333', 0.3, 0.0)
    mat('mCoffee', '2a2a2a', 0.4, 0.2)
    mat('mShade2', 'f5f5dc', 0.95, 0.0, (1.0, 0.95, 0.8, 1.5))

    box('Floor', W/2, D/2, 10, 0, 0, -5, 'mFloor', '2a2015')
    box('Ceiling', W/2, D/2, 10, 0, 0, H+5, 'mCeil', '1e2025')
    box('BW', W/2, 10, H/2, 0, -D/2, H/2, 'mWall', '1e222a')
    box('LW', 10, D/2, H/2, -W/2, 0, H/2, 'mWall2', '1e222a')
    box('RW', 10, D/2, H/2, W/2, 0, H/2, 'mWall2', '1e222a')
    box('FWT', W/2, 10, H*0.7, 0, D/2, H*0.7, 'mWall', '1e222a')

    # 升降桌
    box('DeskTop', 240, 110, 6, 0, 100, 160, 'mDesk', '1a1a1a', 0.3, 0.1)
    for (lx, ly) in [(-105, 100), (105, 100)]:
        cyl(f'DL{lx}', 3, 160, lx, ly, 80, 0,0,0, 'mMetal', '2a2a2a', 0.2, 0.9)

    # 双屏显示器（屏幕发光）
    for sx in [-90, 90]:
        box(f'Mon{sx}', 85, 5, 58, sx, 60, 215, 'mScr', '0066cc', 0.05, 0.0, (0.0, 0.4, 1.0, 2.0))
        cyl(f'MSt{sx}', 3, 40, sx, 80, 188, 0,0,0, 'mMetal', '444444', 0.2, 0.9)
        box(f'MBa{sx}', 40, 5, 15, sx, 80, 182, 'mMetal', '444444', 0.2, 0.9)
    box('KB', 110, 30, 6, 0, 70, 168, 'mKB', '333333', 0.6)

    # 人体工学椅
    box('CSeat', 100, 90, 10, 0, 0, 100, 'mChair', '1a1a1a', 0.8)
    box('CBack', 100, 10, 130, 0, -40, 165, 'mChair2', '222222', 0.8)
    box('CArmL', 10, 80, 50, -55, 0, 120, 'mChair2', '222222', 0.7)
    box('CArmR', 10, 80, 50, 55, 0, 120, 'mChair2', '222222', 0.7)
    cyl('CPis', 4, 80, 0, 0, 50, 0,0,0, 'mMetal', '333333', 0.2, 0.9)
    for i, a in enumerate(range(5)):
        ang = i * 2 * math.pi / 5
        cyl(f'CL{i}', 3, 5, 50*math.cos(ang), 50*math.sin(ang), 15, 0,0,0, 'mMetal', '333333', 0.2, 0.9)

    # 台灯（发光）
    cyl('LBse', 15, 4, 120, 170, 163, 0,0,0, 'mMetal4', 'b8860b', 0.3, 0.8)
    cyl('LBPo', 3, 100, 120, 170, 168, 0,0,math.pi/4, 'mMetal4', 'b8860b', 0.3, 0.8)
    cone('LSh', 28, 8, 35, 145, 190, 215, 0,0,0, 'mLamp', 'f5f5dc', 0.95)
    sph('LBu', 8, 145, 190, 200, 'mLampG', 'fff5d0', 0.3, 0.0, (1.0, 0.95, 0.8, 3.0))

    # 开放书架 + 书
    for i in range(6):
        bh = i * 60 + 5
        box(f'SH{i}', 180, 25, 6, -500, 200, bh, 'mWood', '3d2b1f', 0.6)
    box('SBB', 180, 6, 380, -500, 210, 180, 'mWood', '2d1a0a', 0.6)
    bc = ['196aff','cc2222','22aa22','daa520','8b008b','cd853f','2f4f4f','b8860b','483d8b','006400']
    for i in range(28):
        bx = -575 + (i % 4) * 42 + (i // 4) * 3
        bh = 10 + (i // 4) * 60
        bhr = 35 + (i % 3) * 12
        box(f'OB{i}', 35, 20, bhr, bx, 208, bh + bhr//2, f'mOB{i}', bc[i % len(bc)], 0.8)

    # 极简时钟
    cyl('Clk', 28, 3, -500, -480, 280, 0,0,0, 'mClock', '333333', 0.3)
    for i in range(12):
        ang = i * math.pi / 6
        bx = -500 + 20 * math.cos(ang)
        bz = 280 + 20 * math.sin(ang)
        sph(f'T{i}', 2, bx, -480, bz, 'mClock', 'cccccc', 0.5)

    # 咖啡机
    box('CM', 50, 40, 70, 420, 200, 35, 'mCoffee', '2a2a2a', 0.4, 0.2)
    # 咖啡机指示灯（发光）
    sph('CML', 5, 420, 200, 80, 'mLampG', 'ff6600', 0.3, 0.0, (1.0, 0.4, 0.0, 2.0))

    # 落地灯
    cyl('FLeg', 3, 160, 380, 200, 0, 0,0,0, 'mMetal', 'c0c0c0', 0.2, 0.9)
    cone('FSh', 35, 12, 30, 380, 200, 175, 0,0,0, 'mShade2', 'f5f5dc', 0.95, 0.0, (1.0, 0.95, 0.8, 1.5))
    sph('FLG', 6, 380, 200, 165, 'mLampG', 'fff0d0', 0.2, 0.0, (1.0, 0.95, 0.8, 2.0))

    # 脚凳
    box('FR', 80, 60, 18, 0, -80, 9, 'mChair', '2a2a2a', 0.8)

# ─────────────────────────────────────────────────────────────────
# Bedroom Room
# ─────────────────────────────────────────────────────────────────
def build_bedroom():
    W, D, H = 1200, 1000, 400
    mat('mFloor', 'c8a87a', 0.75, 0.0)
    mat('mCeil', 'f8f0e8', 0.9, 0.0)
    mat('mWall', 'e8ddd0', 0.85, 0.0)
    mat('mBF', '8b7355', 0.7, 0.0)
    mat('mBM', 'd4c4a0', 0.9, 0.0)
    mat('mMat', 'f0f0f0', 0.95, 0.0)
    mat('mComf', 'e8d4c8', 0.95, 0.0)
    mat('mPil', 'fff8f0', 0.95, 0.0)
    mat('mHB', '8b7355', 0.7, 0.0)
    mat('mNS', 'a08060', 0.7, 0.0)
    mat('mBrass', 'b8860b', 0.3, 0.8)
    mat('mBD', 'fffacd', 0.3, 0.0, (1.0, 0.95, 0.5, 2.5))  # 床头灯发光
    mat('mWD', 'c8a87a', 0.65, 0.0)
    mat('mMirF', 'c0d8e8', 0.05, 0.0, 0.0, 0.3)  # 镜面
    mat('mBot', 'ff69b4', 0.4, 0.0)
    mat('mCur', 'e8d4f0', 0.9, 0.0)
    mat('mWinG', 'aaccdd', 0.1, 0.0, 0.5, 0.4)  # 窗户透光
    mat('mAC', 'f0f0f0', 0.8, 0.0)

    box('Floor', W/2, D/2, 10, 0, 0, -5, 'mFloor', 'c8a87a', 0.75)
    box('Ceiling', W/2, D/2, 10, 0, 0, H+5, 'mCeil', 'f8f0e8', 0.9)
    box('BW', W/2, 10, H/2, 0, -D/2, H/2, 'mWall', 'e8ddd0', 0.85)
    box('LW', 10, D/2, H/2, -W/2, 0, H/2, 'mWall', 'e8ddd0', 0.85)
    box('RW', 10, D/2, H/2, W/2, 0, H/2, 'mWall', 'e8ddd0', 0.85)
    box('FWT', W/2, 10, H*0.7, 0, D/2, H*0.7, 'mWall', 'e8ddd0', 0.85)

    # 双人床
    box('BFr', 260, 200, 30, 0, -250, 15, 'mBF', '8b7355', 0.7)
    box('BM', 250, 190, 20, 0, -250, 40, 'mBM', 'd4c4a0', 0.9)
    box('Mat', 240, 185, 25, 0, -250, 62, 'mMat', 'f0f0f0', 0.95)
    box('Comf', 235, 160, 18, 0, -240, 85, 'mComf', 'e8d4c8', 0.95)
    for px in [-65, 65]:
        box(f'Pil{px}', 80, 40, 18, px, -255, 90, 'mPil', 'fff8f0', 0.95)
    box('HB', 260, 15, 120, 0, -355, 90, 'mHB', '8b7355', 0.7)

    # 床头柜 + 床头灯
    for sx in [-170, 170]:
        box(f'NS{sx}', 55, 45, 50, sx, -340, 25, 'mNS', 'a08060', 0.7)
        box(f'NST{sx}', 58, 48, 4, sx, -340, 52, 'mNS', '8b7355', 0.7)
        cyl(f'BT{sx}', 6, 35, sx, -340, 80, 0,0,0, 'mBrass', 'b8860b', 0.3, 0.8)
        sph(f'BD{sx}', 12, sx, -340, 95, 'mBD', 'fffacd', 0.3, 0.0, (1.0, 0.95, 0.5, 2.5))

    # 衣柜
    box('WD', 200, 70, 280, -400, 250, 140, 'mWD', 'c8a87a', 0.65)
    for i in range(3):
        box(f'WD{i}', 60, 5, 265, -430+i*65, 250, 140, 'mWD', 'd4b896', 0.65)
        box(f'WDH{i}', 4, 4, 30, -410+i*65, 250, 180, 'mBrass', 'c0c0c0', 0.2, 0.9)
    box('WDT', 205, 75, 8, -400, 250, 285, 'mWD', 'b8977a', 0.6)

    # 梳妆台 + 镜子
    box('DR', 120, 45, 80, 350, 200, 40, 'mWD', 'c8a87a', 0.65)
    box('DRT', 125, 50, 4, 350, 200, 82, 'mWD', 'd4b896', 0.6)
    box('Mir', 80, 4, 100, 350, 160, 180, 'mMirF', 'c0d8e8', 0.05, 0.0, 0.0, 0.3)
    for ci, (cx, cz) in enumerate([(320, 90), (335, 88), (350, 91), (370, 89)]):
        cyl(f'Bot{ci}', 5, 15, cx, 200, cz, 0,0,0, 'mBot', 'ff69b4', 0.4)

    # 窗帘 + 窗
    for si, sx in enumerate([-350, 350]):
        box(f'Cur{si}', 8, 150, 250, sx, -350, 180, 'mCur', 'e8d4f0', 0.9)
    cyl('CRo', 3, 700, 0, -350, 305, 0, math.pi/2, 0, 'mBrass', 'c0c0c0', 0.2, 0.9)
    box('Win', 150, 3, 180, 0, -492, 200, 'mWinG', 'aaccdd', 0.1, 0.0, (0.7, 0.85, 1.0, 0.8))

    # 墙画
    for i, (hx, hy, hw, hh, hc) in enumerate([(-300, 280, 120, 80, 'e8c8a0'),(-130, 280, 80, 100, 'c8a0e8'),(50, 280, 100, 70, 'a0e8c8')]):
        box(f'Fr{i}', hw, 5, hh, hx, -485, hy, 'mWD', '5c4033', 0.6)
        box(f'Pa{i}', hw-8, 2, hh-8, hx, -490, hy, f'mPai{i}', hc, 0.9)

    # 空调（出风口发光）
    box('AC', 140, 20, 45, 0, -480, 360, 'mAC', 'f0f0f0', 0.8)
    box('ACL', 120, 3, 5, 0, -478, 355, 'mBD', 'cceeff', 0.3, 0.0, (0.8, 0.9, 1.0, 1.0))

# ─────────────────────────────────────────────────────────────────
# Tea Room
# ─────────────────────────────────────────────────────────────────
def build_tea_room():
    W, D, H = 1200, 1000, 400
    mat('mFloor', 'c8b87a', 0.8, 0.0)
    mat('mCeil', 'fff8e8', 0.95, 0.0)
    mat('mWall', 'f5f0e0', 0.9, 0.0)
    mat('mTat', 'd4c896', 0.85, 0.0)
    mat('mTeaW', 'a08060', 0.65, 0.0)
    mat('mTea', 'd2691e', 0.5, 0.0)
    mat('mTea2', 'f5f5dc', 0.6, 0.0)
    mat('mZab', '5a7a5a', 0.95, 0.0)
    mat('mBamb', '8fbc8f', 0.75, 0.0)
    mat('mSand', 'f5f0dc', 0.95, 0.0)
    mat('mRk', '696969', 0.9, 0.0)
    mat('mToko', 'f5f0e0', 0.9, 0.0)
    mat('mLanG', 'fff5d0', 0.95, 0.0, (1.0, 0.95, 0.7, 4.0))  # 纸灯笼强发光
    mat('mIncG', 'ff4500', 0.3, 0.0, (1.0, 0.3, 0.0, 0.8))  # 线香发光
    mat('mFl', 'ff69b4', 0.4, 0.0)
    mat('mVase', 'd2956a', 0.4, 0.0)

    box('Floor', W/2, D/2, 10, 0, 0, -5, 'mFloor', 'c8b87a', 0.8)
    box('Ceiling', W/2, D/2, 10, 0, 0, H+5, 'mCeil', 'fff8e8', 0.95)
    box('BW', W/2, 10, H/2, 0, -D/2, H/2, 'mWall', 'f5f0e0', 0.9)
    box('LW', 10, D/2, H/2, -W/2, 0, H/2, 'mWall', 'f5f0e0', 0.9)
    box('RW', 10, D/2, H/2, W/2, 0, H/2, 'mWall', 'f5f0e0', 0.9)
    box('FWT', W/2, 10, H*0.7, 0, D/2, H*0.7, 'mWall', 'f5f0e0', 0.9)

    # 榻榻米
    for xi in range(4):
        for yi in range(5):
            bx = -600 + xi * 300 + 150
            by = -500 + yi * 200 + 100
            box(f'T{xi}_{yi}', 295, 195, 8, bx, by, -4, 'mTat', 'd4c896', 0.85)

    # 矮茶几 + 茶具
    box('TT', 160, 90, 6, 0, 50, 80, 'mTeaW', 'a08060', 0.65)
    for (lx, ly) in [(-65, 15), (-65, 85), (65, 15), (65, 85)]:
        box(f'TL{lx}', 8, 8, 75, lx, ly, 37, 'mTeaW', '8b7355', 0.7)
    cyl('Teapot', 16, 22, -20, 50, 95, 0,0,0, 'mTea', 'd2691e', 0.5)
    cyl('TC1', 8, 10, 20, 45, 92, 0,0,0, 'mTea2', 'f5f5dc', 0.6)
    cyl('TC2', 8, 10, 35, 60, 92, 0,0,0, 'mTea2', 'f5f5dc', 0.6)
    box('Tray', 80, 50, 4, 10, 60, 88, 'mTeaW', '8b7355', 0.6)

    # 蒲团 × 4
    for (qx, qy) in [(-180, 100), (0, 100), (180, 100), (0, -50)]:
        cyl(f'Z{qx}', 50, 15, qx, qy, 15, 0,0,0, 'mZab', '5a7a5a', 0.95)

    # 竹屏风
    for pi in range(4):
        for hi in range(4):
            cyl(f'PL{pi}_{hi}', 3, 200, -520+pi*25, 100+hi*3, 180, 0,0,0, 'mBamb', '8fbc8f', 0.75)
    box('PF', 110, 4, 200, -490, 100, 180, 'mWall', 'f5f0e0', 0.9)

    # 竹子装饰
    for i in range(8):
        bx = -560 + i * 35 + (i % 2) * 15
        by = -400 + (i % 3) * 20
        h = 280 + (i % 4) * 40
        cyl(f'Bam{i}', 5, h, bx, by, h/2, 0,0,0, 'mBamb', '8fbc8f', 0.75)

    # 枯山水
    box('Zen', 200, 120, 8, 400, -350, 4, 'mRk', '8b8370', 0.9)
    for si in range(20):
        sx = 330 + (si % 5) * 28 + (si % 3) * 5
        sz = -380 + (si // 5) * 28
        sph(f'S{sx}', 9, sx, -350, sz, 'mSand', 'f5f0dc', 0.95)
    for ri, (rx, rz) in enumerate([(375, -360), (410, -340), (355, -325)]):
        sph(f'Rk{ri}', 20+ri*8, rx, -350, rz, 'mRk', '696969', 0.9)
    cyl(f'PT{ri}', 4, 55, 440, -340, 27, 0,0,0, 'mBamb', '5c3317', 0.7)
    sph(f'PC{ri}', 28, 440, -340, 75, 'mBamb', '228b22', 0.85)

    # 壁龛 + 花
    box('TokoB', 180, 15, 280, 450, -485, 140, 'mToko', 'f5f0e0', 0.9)
    box('TokoF', 180, 40, 8, 450, -455, 4, 'mTeaW', 'c8b87a', 0.8)
    box('KP', 80, 4, 120, 450, -475, 200, 'mToko', '2a2015', 0.7)
    box('KM', 72, 2, 108, 450, -480, 200, 'mTea2', 'f5f0dc', 0.9)
    for ci, (fx, fz, fc) in enumerate([(413, 5, 'ff69b4'),(423, 8, 'ff1493'),(418, 0, 'ff69b4'),(408, 10, 'ffffff')]):
        cyl(f'Fl{ci}', 5, 30, 418+fx, -445, 50+fz, 0,0,0, 'mFl', fc, 0.4)
        sph(f'Bl{ci}', 7, 418+fx, -445, 65+fz, 'mFl', fc, 0.4)
    cyl('Vase', 14, 38, 420, -445, 19, 0,0,0, 'mVase', 'd2956a', 0.4)

    # 纸灯笼（强发光！）
    sph('Lan', 55, 0, 0, 375, 'mLanG', 'fff5d0', 0.95, 0.0, (1.0, 0.95, 0.7, 4.0))
    cyl('LCo', 2, 70, 0, 0, 320, 0,0,0, 'mTeaW', 'd4c4a0', 0.9)

    # 线香（发光）
    cyl('Inc', 1.5, 40, 80, 50, 87, 0,0,0, 'mTea2', '8b4513', 0.8)
    sph('IncT', 3, 80, 50, 113, 'mIncG', 'ff4500', 0.3, 0.0, (1.0, 0.3, 0.0, 0.8))

# ─────────────────────────────────────────────────────────────────
# Living Room
# ─────────────────────────────────────────────────────────────────
def build_living_room():
    W, D, H = 1200, 1000, 400
    mat('mFloor', 'd4b896', 0.6, 0.0)
    mat('mCeil', 'ffffff', 0.9, 0.0)
    mat('mWall', 'f0ebe0', 0.85, 0.0)
    mat('mSofa', '4a7a9a', 0.85, 0.0)
    mat('mSofa2', '3a6a8a', 0.85, 0.0)
    mat('mPil', 'ff6b6b', 0.9, 0.0)
    mat('mGT', 'aaccdd', 0.05, 0.0, 0.5, 0.5)  # 玻璃
    mat('mTV', '0a0a1a', 0.05, 0.0, (0.05, 0.1, 0.3, 1.5))  # 电视屏幕发光
    mat('mMetal', 'c0c0c0', 0.2, 0.9)
    mat('mPlant', '228b22', 0.9, 0.0)
    mat('mPot', '8b4513', 0.8, 0.0)
    mat('mFLG', 'fff0d0', 0.95, 0.0, (1.0, 0.95, 0.8, 2.0))  # 落地灯发光
    mat('mArt', 'e8e0d0', 0.9, 0.0)
    mat('mRug', 'c87070', 0.95, 0.0)
    mat('mShade', 'f5f5dc', 0.95, 0.0)

    box('Floor', W/2, D/2, 10, 0, 0, -5, 'mFloor', 'd4b896', 0.6)
    box('Ceiling', W/2, D/2, 10, 0, 0, H+5, 'mCeil', 'ffffff', 0.9)
    box('BW', W/2, 10, H/2, 0, -D/2, H/2, 'mWall', 'f0ebe0', 0.85)
    box('LW', 10, D/2, H/2, -W/2, 0, H/2, 'mWall', 'f0ebe0', 0.85)
    box('RW', 10, D/2, H/2, W/2, 0, H/2, 'mWall', 'f0ebe0', 0.85)
    box('FWT', W/2, 10, H*0.7, 0, D/2, H*0.7, 'mWall', 'f0ebe0', 0.85)

    # L型沙发
    box('Sof', 240, 120, 40, -100, 0, 20, 'mSofa', '4a7a9a', 0.85)
    box('SofB', 240, 15, 90, -100, -55, 85, 'mSofa2', '3a6a8a', 0.85)
    box('SofAL', 15, 120, 60, -225, 0, 50, 'mSofa2', '3a6a8a', 0.85)
    box('SofAR', 15, 80, 60, 20, 40, 50, 'mSofa2', '3a6a8a', 0.85)
    for si, (sx, sy) in enumerate([(-170, 20), (-100, 20), (-30, 20), (-170, -20), (-100, -20)]):
        box(f'SC{si}', 55, 55, 15, sx, sy, 55, 'mSofa', '5a8aaa', 0.9)
    for pi, (px, py, pc) in enumerate([(-180, 10, 'ff6b6b'), (-120, 15, 'ffd93d'), (-60, 10, '6bcb77'), (10, 20, '4d96ff')]):
        box(f'Pl{pi}', 40, 15, 40, px, py, 65, f'mPl{pi}', pc, 0.9)

    # 玻璃茶几
    box('CT', 140, 80, 4, 150, 0, 75, 'mGT', 'aaccdd', 0.05, 0.0, 0.5, 0.5)
    for (lx, ly) in [(-58, -28), (-58, 28), (58, -28), (58, 28)]:
        cyl(f'CM{lx}', 3, 70, 150+lx, ly, 35, 0,0,0, 'mMetal', 'c0c0c0', 0.2, 0.9)
    box('Mag', 50, 35, 4, 140, 10, 79, 'mArt', 'f0f0f0', 0.9)
    cyl('Va', 10, 28, 168, 0, 85, 0,0,0, 'mPlant', '2d6a4f', 0.3)
    sph('VF', 10, 168, 0, 97, 'mPlant', 'ff69b4', 0.4)

    # 电视墙
    box('TVS', 200, 45, 60, 0, -350, 30, 'mMetal', '2a2a2a', 0.4, 0.1)
    box('TVT', 205, 48, 4, 0, -350, 62, 'mMetal', '333333', 0.4, 0.1)
    box('TV', 200, 8, 115, 0, -350, 175, 'mTV', '0a0a1a', 0.05, 0.0, (0.05, 0.1, 0.3, 1.5))
    box('SB', 150, 15, 12, 0, -350, 70, 'mMetal', '1a1a1a', 0.5)

    # 绿植
    cyl('Pot1', 28, 38, -520, 280, 19, 0,0,0, 'mPot', '8b4513', 0.8)
    sph('Pl1', 52, -520, 280, 85, 'mPlant', '228b22', 0.9)
    cyl('Tr1', 8, 48, -520, 280, 24, 0,0,0, 'mPot', '5c3317', 0.7)
    cyl('Pot2', 20, 28, -520, 180, 14, 0,0,0, 'mPot', '8b4513', 0.8)
    sph('Pl2', 32, -520, 180, 65, 'mPlant', '2e8b57', 0.9)

    # 落地灯
    cyl('FLeg', 3, 155, 440, 280, 0, 0,0,0, 'mMetal', 'c0c0c0', 0.2, 0.9)
    cone('FSh', 38, 14, 38, 440, 280, 168, 0,0,0, 'mShade', 'f5f5dc', 0.95)
    sph('FLG', 6, 440, 280, 152, 'mFLG', 'fff0d0', 0.2, 0.0, (1.0, 0.95, 0.8, 2.0))

    # 抽象艺术墙
    box('AF', 180, 5, 100, -400, -485, 250, 'mMetal', '1a1a1a', 0.5)
    box('ACan', 170, 2, 90, -400, -490, 250, 'mArt', 'e8e0d0', 0.9)
    for ci, (cx, cz, cc) in enumerate([(-450, 280, 'ff6b6b'), (-420, 270, '4d96ff'), (-390, 285, 'ffd93d'), (-450, 240, '6bcb77'), (-410, 235, 'ff9f43')]):
        box(f'AB{ci}', 35, 2, 30, cx, -491, cz, f'mAB{ci}', cc, 0.9)

    # 边几台灯
    cyl('SLB', 10, 4, 345, 150, 4, 0,0,0, 'mMetal', 'c0c0c0', 0.3, 0.8)
    cyl('SLA', 3, 75, 345, 150, 78, 0,0,0.3, 'mMetal', 'c0c0c0', 0.3, 0.8)
    cone('SLS', 24, 10, 28, 358, 168, 138, 0,0,0, 'mShade', 'f5f5dc', 0.95)
    sph('SLG', 5, 358, 168, 124, 'mFLG', 'ffd700', 0.2, 0.0, (1.0, 0.95, 0.5, 2.0))

    # 地毯
    box('Rug', 400, 300, 3, 0, 0, -8, 'mRug', 'c87070', 0.95)

# ─────────────────────────────────────────────────────────────────
# Reading Room
# ─────────────────────────────────────────────────────────────────
def build_reading_room():
    W, D, H = 1200, 1000, 400
    mat('mFloor', '5c3317', 0.4, 0.0)
    mat('mCeil', 'f8f4e8', 0.9, 0.0)
    mat('mWall', 'e8dcc8', 0.85, 0.0)
    mat('mWP', '3d2210', 0.6, 0.0)
    mat('mBW', '2d1a0a', 0.6, 0.0)
    mat('mLth', '5c3317', 0.7, 0.0)
    mat('mLth2', '4a2810', 0.7, 0.0)
    mat('mBrass', 'b8860b', 0.3, 0.8)
    mat('mDsk', '5c3317', 0.6, 0.0)
    mat('mRDP', '3d2210', 0.7, 0.0)
    mat('mRShG', 'ffd700', 0.95, 0.0, (1.0, 0.95, 0.5, 3.5))  # 台灯强发光
    mat('mGl', '1e4a6a', 0.4, 0.0)
    mat('mGlL', '2e8b57', 0.5, 0.0)
    mat('mMF', '5c4033', 0.6, 0.0)
    mat('mMC', 'c8d8e8', 0.8, 0.0)
    mat('mOcean', 'c8d8e8', 0.8, 0.0)
    mat('mWlG', '88bbcc', 0.05, 0.0, 0.5, 0.35)  # 窗户透光
    mat('mCur', '8b0000', 0.9, 0.0)
    mat('mFP', '228b22', 0.85, 0.0)
    mat('mFPO', '8b4513', 0.8, 0.0)
    mat('mCC', '5c4033', 0.6, 0.0)
    mat('mCCF', 'f5f0dc', 0.2, 0.0)

    box('Floor', W/2, D/2, 10, 0, 0, -5, 'mFloor', '5c3317', 0.4)
    box('Ceiling', W/2, D/2, 10, 0, 0, H+5, 'mCeil', 'f8f4e8', 0.9)
    box('BW', W/2, 10, H/2, 0, -D/2, H/2, 'mWall', 'e8dcc8', 0.85)
    box('LW', 10, D/2, H/2, -W/2, 0, H/2, 'mWall', 'e8dcc8', 0.85)
    box('RW', 10, D/2, H/2, W/2, 0, H/2, 'mWall', 'e8dcc8', 0.85)
    box('FWT', W/2, 10, H*0.7, 0, D/2, H*0.7, 'mWall', 'e8dcc8', 0.85)
    box('WPB', W/2, 8, 180, 0, -492, 90, 'mWP', '3d2210', 0.6)
    box('WPL', 8, D/2, 180, -W/2+4, 0, 90, 'mWP', '3d2210', 0.6)
    box('CR', W/2+10, 8, 4, 0, -492, 185, 'mWP', '5c4033', 0.6)

    # 书墙
    box('BWB', 580, 10, 380, -340, -480, 190, 'mBW', '2d1a0a', 0.6)
    for sx in [-650, -30]:
        box(f'BWS{sx}', 8, 30, 380, sx, -480, 190, 'mWP', '3d2210', 0.6)
    for i in range(7):
        bh = i * 55 + 5
        box(f'BSH{i}', 620, 30, 6, -340, -480, bh, 'mBW', '2d1a0a', 0.6)
    bc = ['8b0000','00008b','006400','800000','191970','4b0082','8b4513','2f4f4f','556b2f','b8860b']
    for i in range(45):
        bx = -635 + (i % 6) * 98 + (i // 6) * 4
        bh = 8 + (i // 6) * 55
        bhr = 38 + (i % 4) * 8
        box(f'RB{i}', 85, 22, bhr, bx, -482, bh + bhr//2, f'mRB{i}', bc[i % len(bc)], 0.8)
        if i % 3 == 0:
            box(f'RBS{i}', 3, 22, bhr-10, bx+35, -484, bh + bhr//2, 'mBrass', 'daa520', 0.8)

    # 皮沙发
    box('RCS', 130, 120, 15, 200, 100, 85, 'mLth', '5c3317', 0.7)
    box('RCB', 130, 15, 130, 200, 50, 160, 'mLth2', '4a2810', 0.7)
    box('RCAL', 15, 100, 70, 135, 100, 115, 'mLth2', '4a2810', 0.7)
    box('RCAR', 15, 100, 70, 265, 100, 115, 'mLth2', '4a2810', 0.7)
    for (lx, ly) in [(150,170),(250,170),(150,30),(250,30)]:
        cyl(f'RCL{lx}', 4, 75, lx, ly, 35, 0,0,0, 'mBrass', 'b8860b', 0.3, 0.8)
    box('Ott', 100, 80, 20, 200, 200, 10, 'mLth', '5c3317', 0.7)
    for (lx, ly) in [(165,235),(235,235),(165,165),(235,165)]:
        cyl(f'OCL{lx}', 3, 50, lx, ly, 5, 0,0,0, 'mBrass', 'b8860b', 0.3, 0.8)

    # 书桌 + 台灯
    box('RDSK', 200, 90, 6, -100, 200, 165, 'mDsk', '5c3317', 0.6)
    for (lx, ly) in [(-185,160),(-185,240),(-15,160),(-15,240)]:
        box(f'RDL{lx}', 8, 8, 160, lx, ly, 80, 'mDsk', '4a2810', 0.65)
    box('RDP', 180, 75, 3, -100, 200, 171, 'mRDP', '3d2210', 0.7)
    cyl('RLB', 20, 5, -180, 200, 5, 0,0,0, 'mBrass', 'b8860b', 0.3, 0.8)
    cyl('RLP', 5, 110, -180, 200, 60, 0,0,0, 'mBrass', 'b8860b', 0.3, 0.8)
    cyl('RLB2', 12, 28, -180, 200, 128, 0,0,0, 'mBrass', 'b8860b', 0.3, 0.8)
    cone('RLS', 33, 14, 43, -180, 200, 163, 0,0,0, 'mRShG', 'f5deb3', 0.95)
    sph('RLG', 8, -180, 200, 148, 'mRShG', 'ffd700', 0.1, 0.0, (1.0, 0.95, 0.5, 3.5))

    # 地球仪
    cyl('RGS', 5, 65, 80, 200, 0, 0,0,0, 'mBrass', 'b8860b', 0.3, 0.8)
    sph('RG', 48, 80, 200, 65, 'mGl', '1e4a6a', 0.4)
    box('RGB', 68, 68, 5, 80, 200, -28, 'mBrass', 'b8860b', 0.3, 0.8)

    # 古典地图
    box('MF', 160, 5, 110, 400, -485, 260, 'mMF', '5c4033', 0.6)
    box('MC', 148, 2, 98, 400, -490, 260, 'mOcean', 'c8d8e8', 0.8)
    for li, (lx, lz, lw, lh, lc) in enumerate([(370,290,30,25,'8b7355'),(400,280,40,30,'6a8a6a'),(420,265,20,20,'8b7355'),(385,260,25,18,'6a8a6a')]):
        box(f'ML{li}', lw, 2, lh, lx, -491, lz, f'mML{li}', lc, 0.9)

    # 落地窗 + 窗帘
    box('WF', 160, 6, 200, 0, -492, 200, 'mMF', '5c4033', 0.6)
    box('WG', 150, 3, 190, 0, -495, 200, 'mWlG', '88bbcc', 0.05, 0.0, (0.6, 0.8, 1.0, 0.6))
    for si, sx in enumerate([-100, 100]):
        box(f'RC{si}', 6, 120, 220, sx, -370, 190, 'mCur', '8b0000', 0.9)
    cyl('RCR', 3, 220, 0, -370, 305, 0, math.pi/2, 0, 'mBrass', 'b8860b', 0.3, 0.8)

    # 琴叶榕
    cyl('FPO', 33, 43, -350, 200, 21, 0,0,0, 'mFPO', '8b4513', 0.8)
    sph('FP', 53, -350, 200, 95, 'mFP', '228b22', 0.85)

    # 书架地球仪
    cyl('BGS', 3, 33, -550, 280, 16, 0,0,0, 'mBrass', 'b8860b', 0.3, 0.8)
    sph('BG', 18, -550, 280, 48, 'mGl', '1e4a6a', 0.4)

    # 壁炉时钟
    box('CC', 80, 8, 80, -450, -480, 300, 'mCC', '5c4033', 0.6)
    cyl('CCF', 33, 4, -450, -480, 300, 0,0,0, 'mCCF', 'f5f0dc', 0.2)
    for i in range(12):
        ang = i * math.pi / 6
        bx = -450 + 24 * math.cos(ang)
        bz = 300 + 24 * math.sin(ang)
        sph(f'CT{i}', 2.5, bx, -480, bz, 'mWP', '333333', 0.5)

# ─────────────────────────────────────────────────────────────────
# 烘焙纹理
# ─────────────────────────────────────────────────────────────────
def setup_bake(scene_name, bake_res=2048):
    """切换到 Cycles，配置烘焙"""
    bpy.context.scene.cycles.device = 'GPU'
    bpy.context.scene.cycles.samples = 64
    bpy.context.scene.world = bpy.data.worlds.new("BakeWorld")
    bpy.context.scene.world.use_nodes = True
    bg = bpy.context.scene.world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (0.9, 0.9, 0.9, 1.0)
    bg.inputs[1].default_value = 0.8

def bake_neutral(room_name, out_path):
    """烘焙中性光照纹理"""
    img = bpy.data.images.new(f'neutral_{room_name}', bake_res, bake_res)
    img.file_format = 'JPEG'
    img.colorspace_settings.name = 'sRGB'
    nodes = bpy.context.scene.world.node_tree.nodes
    bg = nodes.get("Background")
    bg.inputs[0].default_value = (0.9, 0.9, 0.9, 1.0)
    bg.inputs[1].default_value = 0.7
    bpy.ops.object.bake(type='COMBINED', save_mode='EXTERNAL', filepath=out_path)
    return out_path

def bake_lightmap(room_name, out_path):
    """烘焙光照图（发光体发光强度）"""
    img = bpy.data.images.new(f'lightmap_{room_name}', 1024, 1024)
    img.file_format = 'JPEG'
    img.colorspace_settings.name = 'sRGB'
    nodes = bpy.context.scene.world.node_tree.nodes
    bg = nodes.get("Background")
    bg.inputs[0].default_value = (0.0, 0.0, 0.0, 1.0)
    bg.inputs[1].default_value = 0.0
    bpy.ops.object.bake(type='EMIT', save_mode='EXTERNAL', filepath=out_path)
    return out_path

# ─────────────────────────────────────────────────────────────────
# 主流程：渲染每个房间并截图作为烘焙纹理
# ─────────────────────────────────────────────────────────────────
def render_room_to_image(room_name, output_path, bake_res=2048):
    """用 Blender 渲染房间并保存图片"""
    # 配置 Cycles 渲染
    scene = bpy.context.scene
    scene.cycles.device = 'GPU'
    scene.cycles.samples = 64
    scene.render.resolution_x = bake_res
    scene.render.resolution_y = bake_res
    scene.render.film_transparent = False
    scene.view_layers[0].use_pass_combined = True

    # 设置相机
    cam_x, cam_y, cam_z = 0, 800, 600
    cam_angle = math.pi / 6  # 30度俯视
    for c in bpy.data.cameras:
        bpy.data.cameras.remove(c)
    bpy.ops.object.camera_add(location=(cam_x, cam_y, cam_z))
    cam = bpy.context.active_object
    cam.name = 'BakeCam'
    cam.data.type = 'PERSP'
    cam.data.lens = 35
    cam.rotation_euler = (math.pi/2 + cam_angle, 0, 0)
    bpy.context.scene.camera = cam

    # 渲染到图片
    img_name = f'baked_{room_name}'
    if img_name in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[img_name])
    img = bpy.data.images.new(img_name, bake_res, bake_res)
    img.file_format = 'JPEG'
    img.colorspace_settings.name = 'sRGB'

    # 使用普通渲染（而非烘焙）
    scene.render.filepath = output_path
    scene.render.image_settings.file_format = 'JPEG'
    scene.render.image_settings.quality = 95
    bpy.ops.render.render(write_still=True)
    return output_path

# ─────────────────────────────────────────────────────────────────
# 渲染所有房间
# ─────────────────────────────────────────────────────────────────
rooms = [
    ("office",    build_office,       "room_office"),
    ("bedroom",   build_bedroom,      "room_bedroom"),
    ("tea_room",  build_tea_room,     "room_tea"),
    ("living",    build_living_room,  "room_living"),
    ("reading",   build_reading_room, "room_reading"),
]

for name, builder, glb_name in rooms:
    print(f"\n{'='*50}")
    print(f"Building & rendering {name}...")
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for m in list(bpy.data.materials): bpy.data.materials.remove(m)

    builder()

    out_neutral = OUT_DIR + f"baked_{name}_neutral.jpg"
    out_lightmap = OUT_DIR + f"lightmap_{name}.jpg"

    print(f"  Rendering neutral texture...")
    render_room_to_image(name, out_neutral, bake_res=2048)
    print(f"  → {out_neutral}")

    # 清理发光体，重新烘焙光影图
    print(f"  Rendering lightmap...")
    bake_lightmap(name, out_lightmap)
    print(f"  → {out_lightmap}")

    print(f"✅ {name} textures done!")

print(f"\n🎉 全部完成！文件在: {OUT_DIR}")
