"""
共生境 - 5房间截图烘焙纹理（简化可靠版）
用法: /snap/bin/blender --background --python bake_screenshots.py
"""
import bpy, os, math

OUT_DIR = os.path.dirname(os.path.abspath(__file__)) + "/assets/rooms_v2/"
os.makedirs(OUT_DIR, exist_ok=True)

# ── 清理 ──────────────────────────────────────────────────────────
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.materials): bpy.data.materials.remove(m)
for img in list(bpy.data.images): bpy.data.images.remove(img)

def mat(name, hex_c, rough=0.5, metallic=0.0, emission_strength=0.0):
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
        if emission_strength > 0:
            bsdf.inputs["Emission Color"].default_value = (r * 0.8, g * 0.8, b * 0.6, 1.0)
            bsdf.inputs["Emission Strength"].default_value = emission_strength
    return m

def am(obj, mn, hc, rough=0.5, metallic=0.0, emission=0.0):
    m = mat(mn, hc, rough, metallic, emission)
    if obj.data.materials: obj.data.materials[0] = m
    else: obj.data.materials.append(m)

def box(name, sx, sy, sz, lx, ly, lz, mn, hc, rough=0.6, metallic=0.0, emission=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(lx,ly,lz))
    o = bpy.context.active_object; o.name = name
    o.scale = (sx, sy, sz); bpy.ops.object.transform_apply()
    am(o, mn, hc, rough, metallic, emission); return o

def cyl(name, r, h, lx, ly, lz, rx=0, ry=0, rz=0, mn='m', hc='999999', rough=0.6, metallic=0.0, emission=0.0):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=(lx,ly,lz), rotation=(rx,ry,rz))
    o = bpy.context.active_object; o.name = name; bpy.ops.object.transform_apply()
    am(o, mn, hc, rough, metallic, emission); return o

def sph(name, r, lx, ly, lz, mn='m', hc='999999', rough=0.6, emission=0.0):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(lx,ly,lz))
    o = bpy.context.active_object; o.name = name; bpy.ops.object.transform_apply()
    am(o, mn, hc, rough, 0.0, emission); return o

def cone(name, r1, r2, h, lx, ly, lz, rx=0, ry=0, rz=0, mn='m', hc='cccccc', rough=0.6, emission=0.0):
    bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=h, location=(lx,ly,lz), rotation=(rx,ry,rz))
    o = bpy.context.active_object; o.name = name; bpy.ops.object.transform_apply()
    am(o, mn, hc, rough, 0.0, emission); return o

# ─────────────────────────────────────────────────────────────────
# Office
# ─────────────────────────────────────────────────────────────────
def build_office():
    mat('mf', '1e1e22', 0.4, 0.0)
    mat('mc', '1a1a1f', 0.9, 0.0)
    mat('mw', '1a1e28', 0.85, 0.0)
    mat('md', '0f0f0f', 0.3, 0.1)
    mat('mm', '2a2a2a', 0.2, 0.9)
    mat('ms', '003366', 0.05, 0.0, 3.0)  # 蓝色屏幕发光
    mat('mk', '1a1a1a', 0.6, 0.0)
    mat('mch', '141414', 0.8, 0.0)
    mat('mgl', '1a5070', 0.4, 0.0)
    mat('mbr', 'b8860b', 0.3, 0.8)
    mat('mlg', 'fff0c0', 0.95, 0.0, 0.0)  # 灯罩
    mat('mlge', 'ffe8a0', 0.2, 0.0, 4.0)  # 灯泡发光
    mat('mwo', '2d1a0a', 0.6, 0.0)
    bc = ['1a3aff','cc2222','22aa22','daa520','8b008b','cd853f','2f4f4f','b8860b','483d8b','006400']

    box('fl', 600, 500, 10, 0, 0, -5, 'mf', '1e1e22', 0.4)
    box('ce', 600, 500, 10, 0, 0, 405, 'mc', '1a1a1f', 0.9)
    box('bw', 600, 10, 400, 0, -500, 200, 'mw', '1a1e28', 0.85)
    box('lw', 10, 500, 400, -600, 0, 200, 'mw', '1a1e28', 0.85)
    box('rw', 10, 500, 400, 600, 0, 200, 'mw', '1a1e28', 0.85)

    # 桌子
    box('dt', 240, 110, 6, 0, 100, 160, 'md', '0f0f0f', 0.3, 0.1)
    for (lx, ly) in [(-105,100),(105,100)]:
        cyl(f'dl{lx}', 3, 160, lx, ly, 80, 0,0,0, 'mm', '2a2a2a', 0.2, 0.9)
    # 双屏
    for sx in [-90, 90]:
        box(f'm{sx}', 80, 5, 55, sx, 60, 215, 'ms', '003366', 0.05, 0.0, 3.0)
        cyl(f'ms{sx}', 3, 40, sx, 80, 188, 0,0,0, 'mm', '444444', 0.2, 0.9)
        box(f'mb{sx}', 40, 5, 15, sx, 80, 182, 'mm', '444444', 0.2, 0.9)
    box('kb', 110, 30, 6, 0, 70, 168, 'mk', '1a1a1a', 0.6)
    # 人体工学椅
    box('cs', 100, 90, 10, 0, 0, 100, 'mch', '141414', 0.8)
    box('cb', 100, 10, 130, 0, -40, 165, 'mch', '141414', 0.8)
    box('cal', 10, 80, 50, -55, 0, 120, 'mch', '141414', 0.8)
    box('car', 10, 80, 50, 55, 0, 120, 'mch', '141414', 0.8)
    cyl('cp', 4, 80, 0, 0, 50, 0,0,0, 'mm', '333333', 0.2, 0.9)
    for i, a in enumerate(range(5)):
        ang = i * 2*math.pi/5
        cyl(f'cl{i}', 3, 5, 50*math.cos(ang), 50*math.sin(ang), 15, 0,0,0, 'mm', '333333', 0.2, 0.9)
    box('chd', 70, 10, 35, 0, -55, 235, 'mch', '141414', 0.8)
    # 台灯（发光）
    cyl('lbe', 15, 4, 120, 170, 163, 0,0,0, 'mbr', 'b8860b', 0.3, 0.8)
    cyl('lpo', 3, 100, 120, 170, 168, 0,0,math.pi/4, 'mbr', 'b8860b', 0.3, 0.8)
    cone('lsh', 28, 8, 35, 145, 190, 215, 0,0,0, 'mlg', 'fff0c0', 0.95)
    sph('lbu', 8, 145, 190, 200, 'mlge', 'ffe8a0', 0.2, emission=4.0)
    # 书架
    for i in range(6):
        bh = i * 60 + 5
        box(f'sh{i}', 180, 25, 6, -500, 200, bh, 'mwo', '2d1a0a', 0.6)
    box('sbb', 180, 6, 380, -500, 210, 180, 'mwo', '2d1a0a', 0.6)
    for i in range(28):
        bx = -575 + (i%4)*42 + (i//4)*3
        bh = 10 + (i//4)*60
        bhr = 35 + (i%3)*12
        box(f'ob{i}', 35, 20, bhr, bx, 208, bh+bhr//2, f'mo{i}', bc[i%len(bc)], 0.8)
    # 地球仪
    cyl('gb', 20, 5, 0, 135, 163, 0,0,0, 'mbr', 'b8860b', 0.3, 0.8)
    cyl('gp', 4, 50, 0, 135, 188, 0,0,0, 'mbr', 'b8860b', 0.3, 0.8)
    sph('gl', 22, 0, 135, 215, 'mgl', '1a5070', 0.4)
    # 落地灯
    cyl('fle', 3, 155, 380, 200, 0, 0,0,0, 'mm', 'c0c0c0', 0.2, 0.9)
    cone('fsh', 35, 12, 30, 380, 200, 175, 0,0,0, 'mlg', 'fff0c0', 0.95)
    sph('flg', 6, 380, 200, 158, 'mlge', 'ffe8a0', 0.2, emission=2.5)
    # 脚凳
    box('fr', 80, 60, 18, 0, -80, 9, 'mch', '1a1a1a', 0.8)

# ─────────────────────────────────────────────────────────────────
# Bedroom
# ─────────────────────────────────────────────────────────────────
def build_bedroom():
    mat('mf', 'c8a87a', 0.75, 0.0)
    mat('mc', 'f5f0e8', 0.9, 0.0)
    mat('mw', 'e0d4c8', 0.85, 0.0)
    mat('mbf', '8b7355', 0.7, 0.0)
    mat('mbm', 'd4c4a0', 0.9, 0.0)
    mat('mmt', 'f0f0f0', 0.95, 0.0)
    mat('mcf', 'e8d0c0', 0.95, 0.0)
    mat('mph', 'fff0e8', 0.95, 0.0)
    mat('mhb', '7a6040', 0.7, 0.0)
    mat('mns', '9a7a5a', 0.7, 0.0)
    mat('mbr', 'b8860b', 0.3, 0.8)
    mat('mle', 'ffe0a0', 0.3, 0.0, 3.5)  # 床头灯发光
    mat('mwd', 'b09070', 0.65, 0.0)
    mat('mir', 'b0c8d8', 0.05, 0.0, 0.5)
    mat('mcu', 'e8d0e8', 0.9, 0.0)
    mat('mwin', 'c0d8e8', 0.1, 0.0, 1.2)  # 窗户透光
    mat('mac', 'e8e8e8', 0.8, 0.0)

    box('fl', 600, 500, 10, 0, 0, -5, 'mf', 'c8a87a', 0.75)
    box('ce', 600, 500, 10, 0, 0, 405, 'mc', 'f5f0e8', 0.9)
    box('bw', 600, 10, 400, 0, -500, 200, 'mw', 'e0d4c8', 0.85)
    box('lw', 10, 500, 400, -600, 0, 200, 'mw', 'e0d4c8', 0.85)
    box('rw', 10, 500, 400, 600, 0, 200, 'mw', 'e0d4c8', 0.85)
    # 双人床
    box('bfr', 260, 200, 30, 0, -250, 15, 'mbf', '8b7355', 0.7)
    box('bm', 250, 190, 20, 0, -250, 40, 'mbm', 'd4c4a0', 0.9)
    box('mt', 240, 185, 25, 0, -250, 62, 'mmt', 'f0f0f0', 0.95)
    box('cf', 235, 160, 18, 0, -240, 85, 'mcf', 'e8d0c0', 0.95)
    for px in [-65, 65]:
        box(f'ph{px}', 80, 40, 18, px, -255, 90, 'mph', 'fff0e8', 0.95)
    box('hb', 260, 15, 120, 0, -355, 90, 'mhb', '7a6040', 0.7)
    # 床头柜 + 灯
    for sx in [-170, 170]:
        box(f'ns{sx}', 55, 45, 50, sx, -340, 25, 'mns', '9a7a5a', 0.7)
        cyl(f'bt{sx}', 6, 35, sx, -340, 80, 0,0,0, 'mbr', 'b8860b', 0.3, 0.8)
        sph(f'bd{sx}', 12, sx, -340, 95, 'mle', 'ffe0a0', 0.3, emission=3.5)
    # 衣柜
    box('wd', 200, 70, 280, -400, 250, 140, 'mwd', 'b09070', 0.65)
    for i in range(3):
        box(f'wdr{i}', 60, 5, 265, -430+i*65, 250, 140, 'mwd', 'c0a080', 0.65)
        box(f'wdh{i}', 4, 4, 30, -410+i*65, 250, 180, 'mbr', 'c0c0c0', 0.2, 0.9)
    # 梳妆台 + 镜子
    box('dr', 120, 45, 80, 350, 200, 40, 'mwd', 'b09070', 0.65)
    box('drt', 125, 50, 4, 350, 200, 82, 'mwd', 'c0a080', 0.6)
    box('mir', 80, 4, 100, 350, 158, 180, 'mir', 'b0c8d8', 0.05, 0.0, 0.5)
    # 窗帘 + 窗
    for si, sx in enumerate([-340, 340]):
        box(f'cu{si}', 8, 150, 250, sx, -350, 180, 'mcu', 'e8d0e8', 0.9)
    cyl('cro', 3, 680, 0, -350, 305, 0, math.pi/2, 0, 'mbr', 'c0c0c0', 0.2, 0.9)
    box('win', 150, 3, 180, 0, -492, 200, 'mwin', 'c0d8e8', 0.1, 0.0, 1.2)
    # 墙画
    for i, (hx, hy, hw, hh, hc) in enumerate([(-280, 280, 120, 80, 'e0b880'),(-110, 280, 80, 100, 'b0a0e0'),(60, 280, 100, 70, 'a0e0b0')]):
        box(f'fr{i}', hw, 5, hh, hx, -485, hy, 'mwd', '5a4030', 0.6)
        box(f'pa{i}', hw-8, 2, hh-8, hx, -490, hy, f'mpa{i}', hc, 0.9)
    # 空调
    box('ac', 140, 20, 45, 0, -480, 360, 'mac', 'e8e8e8', 0.8)

# ─────────────────────────────────────────────────────────────────
# Tea Room
# ─────────────────────────────────────────────────────────────────
def build_tea_room():
    mat('mf', 'c8b87a', 0.8, 0.0)
    mat('mc', 'fff8e8', 0.95, 0.0)
    mat('mw', 'f0e8d8', 0.9, 0.0)
    mat('mt', 'd4c090', 0.85, 0.0)
    mat('mtw', '9a7a58', 0.65, 0.0)
    mat('mte', 'c06030', 0.5, 0.0)
    mat('mt2', 'f0ead0', 0.6, 0.0)
    mat('mza', '5a7a5a', 0.95, 0.0)
    mat('mba', '7aaa7a', 0.75, 0.0)
    mat('msa', 'e8e0c8', 0.95, 0.0)
    mat('mrk', '606060', 0.9, 0.0)
    mat('mlg', 'fff0c0', 0.95, 0.0)
    mat('mlge', 'ffcc60', 0.2, 0.0, 5.0)  # 纸灯笼强发光
    mat('minc', 'ff6020', 0.3, 0.0, 1.0)  # 线香发光
    mat('mfl', 'e85080', 0.4, 0.0)

    box('fl', 600, 500, 10, 0, 0, -5, 'mf', 'c8b87a', 0.8)
    box('ce', 600, 500, 10, 0, 0, 405, 'mc', 'fff8e8', 0.95)
    box('bw', 600, 10, 400, 0, -500, 200, 'mw', 'f0e8d8', 0.9)
    box('lw', 10, 500, 400, -600, 0, 200, 'mw', 'f0e8d8', 0.9)
    box('rw', 10, 500, 400, 600, 0, 200, 'mw', 'f0e8d8', 0.9)
    # 榻榻米
    for xi in range(4):
        for yi in range(5):
            bx = -600 + xi*300 + 150
            by = -500 + yi*200 + 100
            box(f't{xi}{yi}', 295, 195, 8, bx, by, -4, 'mt', 'd4c090', 0.85)
    # 矮茶几 + 茶具
    box('tt', 160, 90, 6, 0, 50, 80, 'mtw', '9a7a58', 0.65)
    for (lx, ly) in [(-65,15),(-65,85),(65,15),(65,85)]:
        box(f'tl{lx}', 8, 8, 75, lx, ly, 37, 'mtw', '8a6a48', 0.7)
    cyl('tp', 16, 22, -20, 50, 95, 0,0,0, 'mte', 'c06030', 0.5)
    cyl('tc1', 8, 10, 20, 45, 92, 0,0,0, 'mt2', 'f0ead0', 0.6)
    cyl('tc2', 8, 10, 35, 60, 92, 0,0,0, 'mt2', 'f0ead0', 0.6)
    box('tr', 80, 50, 4, 10, 60, 88, 'mtw', '9a7a58', 0.6)
    # 蒲团 × 4
    for (qx, qy) in [(-180,100),(0,100),(180,100),(0,-50)]:
        cyl(f'z{qx}', 50, 15, qx, qy, 15, 0,0,0, 'mza', '5a7a5a', 0.95)
    # 竹屏风
    for pi in range(4):
        for hi in range(4):
            cyl(f'pn{pi}{hi}', 3, 200, -520+pi*25, 100+hi*3, 180, 0,0,0, 'mba', '7aaa7a', 0.75)
    box('pf', 110, 4, 200, -490, 100, 180, 'mw', 'f0e8d8', 0.9)
    # 竹子
    for i in range(8):
        bx = -560 + i*35 + (i%2)*15
        by = -400 + (i%3)*20
        h = 280 + (i%4)*40
        cyl(f'bm{i}', 5, h, bx, by, h/2, 0,0,0, 'mba', '7aaa7a', 0.75)
    # 枯山水
    box('zen', 200, 120, 8, 400, -350, 4, 'mrk', '706860', 0.9)
    for si in range(20):
        sx = 330 + (si%5)*28 + (si%3)*5
        sz = -380 + (si//5)*28
        sph(f's{si}', 9, sx, -350, sz, 'msa', 'e8e0c8', 0.95)
    for ri, (rx, rz) in enumerate([(375,-360),(410,-340),(355,-325)]):
        sph(f'rk{ri}', 20+ri*8, rx, -350, rz, 'mrk', '606060', 0.9)
    cyl(f'pt{ri}', 4, 55, 440, -340, 27, 0,0,0, 'mba', '7aaa7a', 0.7)
    sph(f'pc{ri}', 28, 440, -340, 75, 'mba', '228822', 0.85)
    # 壁龛 + 花
    box('tkb', 180, 15, 280, 450, -485, 140, 'mw', 'f0e8d8', 0.9)
    box('tkf', 180, 40, 8, 450, -455, 4, 'mtw', 'c8b87a', 0.8)
    box('kp', 80, 4, 120, 450, -475, 200, 'mw', '1a1008', 0.7)
    cyl('vs', 14, 38, 420, -445, 19, 0,0,0, 'mte', 'c06030', 0.4)
    for ci, (fx, fz, fc) in enumerate([(413,5,'e85080'),(423,8,'ff3070'),(418,0,'e85080'),(408,10,'ff80a0')]):
        cyl(f'fl{ci}', 5, 30, 418+fx, -445, 50+fz, 0,0,0, 'mfl', fc, 0.4)
        sph(f'bl{ci}', 7, 418+fx, -445, 65+fz, 'mfl', fc, 0.4)
    # 纸灯笼（极强发光！）
    sph('lan', 55, 0, 0, 375, 'mlge', 'ffcc60', 0.2, emission=5.0)
    cyl('lco', 2, 70, 0, 0, 320, 0,0,0, 'mtw', 'd4c090', 0.9)
    # 线香
    cyl('inc', 1.5, 40, 80, 50, 87, 0,0,0, 'mt2', '8b4513', 0.8)
    sph('int', 3, 80, 50, 113, 'minc', 'ff6020', 0.3, emission=1.0)

# ─────────────────────────────────────────────────────────────────
# Living Room
# ─────────────────────────────────────────────────────────────────
def build_living_room():
    mat('mf', 'd4b896', 0.6, 0.0)
    mat('mc', 'ffffff', 0.9, 0.0)
    mat('mw', 'ece4d8', 0.85, 0.0)
    mat('msf', '3a6a8a', 0.85, 0.0)
    mat('msf2', '2a5a7a', 0.85, 0.0)
    mat('mp', 'ff6060', 0.9, 0.0)
    mat('mgl', '90b0c8', 0.05, 0.0, 0.6)
    mat('mtv', '050a18', 0.05, 0.0, 2.5)  # 电视发光
    mat('mme', 'c0c0c0', 0.2, 0.9)
    mat('mpl', '228822', 0.9, 0.0)
    mat('mpo', '8b4513', 0.8, 0.0)
    mat('mfg', 'ffe0a0', 0.2, 0.0, 3.0)  # 落地灯发光
    mat('mfg2', 'fff0c0', 0.95, 0.0)
    mat('mar', 'e0d8c8', 0.9, 0.0)
    mat('mrg', 'c06060', 0.95, 0.0)
    mat('msh', 'f5f0d8', 0.95, 0.0)
    bc = ['ff4040','ff8020','ffd020','40a040','4080ff','8040ff']

    box('fl', 600, 500, 10, 0, 0, -5, 'mf', 'd4b896', 0.6)
    box('ce', 600, 500, 10, 0, 0, 405, 'mc', 'ffffff', 0.9)
    box('bw', 600, 10, 400, 0, -500, 200, 'mw', 'ece4d8', 0.85)
    box('lw', 10, 500, 400, -600, 0, 200, 'mw', 'ece4d8', 0.85)
    box('rw', 10, 500, 400, 600, 0, 200, 'mw', 'ece4d8', 0.85)
    # L型沙发
    box('sf', 240, 120, 40, -100, 0, 20, 'msf', '3a6a8a', 0.85)
    box('sb', 240, 15, 90, -100, -55, 85, 'msf2', '2a5a7a', 0.85)
    box('sal', 15, 120, 60, -225, 0, 50, 'msf2', '2a5a7a', 0.85)
    box('sar', 15, 80, 60, 20, 40, 50, 'msf2', '2a5a7a', 0.85)
    for si, (sx, sy) in enumerate([(-170,20),(-100,20),(-30,20),(-170,-20),(-100,-20)]):
        box(f'sc{si}', 55, 55, 15, sx, sy, 55, 'msf', '4a7a9a', 0.9)
    for pi, (px, py, pc) in enumerate([(-180,10,'ff6060'),(-120,15,'ffd020'),(-60,10,'40a040'),(10,20,'4080ff')]):
        box(f'pl{pi}', 40, 15, 40, px, py, 65, f'mp{pi}', pc, 0.9)
    # 玻璃茶几
    box('ct', 140, 80, 4, 150, 0, 75, 'mgl', '90b0c8', 0.05, 0.0, 0.6)
    for (lx, ly) in [(-58,-28),(-58,28),(58,-28),(58,28)]:
        cyl(f'cm{lx}', 3, 70, 150+lx, ly, 35, 0,0,0, 'mme', 'c0c0c0', 0.2, 0.9)
    box('mg', 50, 35, 4, 140, 10, 79, 'mar', 'f0f0f0', 0.9)
    cyl('va', 10, 28, 168, 0, 85, 0,0,0, 'mpl', '2a6a2a', 0.3)
    sph('vf', 10, 168, 0, 97, 'mpl', 'e85080', 0.4)
    # 电视
    box('tv', 200, 8, 115, 0, -350, 175, 'mtv', '050a18', 0.05, 0.0, 2.5)
    box('tvf', 210, 50, 65, 0, -350, 30, 'mme', '2a2a2a', 0.4, 0.1)
    box('sb2', 150, 15, 12, 0, -350, 70, 'mme', '1a1a1a', 0.5)
    # 绿植
    cyl('pt1', 28, 38, -520, 280, 19, 0,0,0, 'mpo', '8b4513', 0.8)
    sph('pl1', 52, -520, 280, 85, 'mpl', '228822', 0.9)
    cyl('tr1', 8, 48, -520, 280, 24, 0,0,0, 'mpo', '5a3010', 0.7)
    cyl('pt2', 20, 28, -520, 180, 14, 0,0,0, 'mpo', '8b4513', 0.8)
    sph('pl2', 32, -520, 180, 65, 'mpl', '2a8a2a', 0.9)
    # 落地灯
    cyl('fe', 3, 155, 440, 280, 0, 0,0,0, 'mme', 'c0c0c0', 0.2, 0.9)
    cone('fsh', 38, 14, 38, 440, 280, 168, 0,0,0, 'msh', 'f5f0d8', 0.95)
    sph('fg', 6, 440, 280, 152, 'mfg', 'ffe0a0', 0.2, emission=3.0)
    # 艺术墙
    box('af', 180, 5, 100, -400, -485, 250, 'mme', '1a1a1a', 0.5)
    box('ac', 170, 2, 90, -400, -490, 250, 'mar', 'e0d8c8', 0.9)
    for ci, (cx, cz, cc) in enumerate([(-450,280,'ff4040'),(-420,270,'ffa020'),(-390,285,'ffd020'),(-450,240,'40a040'),(-410,235,'8040ff')]):
        box(f'ab{ci}', 35, 2, 30, cx, -491, cz, f'mab{ci}', cc, 0.9)
    # 边几灯
    cyl('slb', 10, 4, 345, 150, 4, 0,0,0, 'mme', 'c0c0c0', 0.3, 0.8)
    cyl('sla', 3, 75, 345, 150, 78, 0,0,0.3, 'mme', 'c0c0c0', 0.3, 0.8)
    cone('sls', 24, 10, 28, 358, 168, 138, 0,0,0, 'msh', 'f5f0d8', 0.95)
    sph('slg', 5, 358, 168, 124, 'mfg', 'ffd020', 0.2, emission=2.5)
    # 地毯
    box('rg', 400, 300, 3, 0, 0, -8, 'mrg', 'c06060', 0.95)

# ─────────────────────────────────────────────────────────────────
# Reading Room
# ─────────────────────────────────────────────────────────────────
def build_reading_room():
    mat('mf', '5c3317', 0.4, 0.0)
    mat('mc', 'f8f4e8', 0.9, 0.0)
    mat('mw', 'e0d4c0', 0.85, 0.0)
    mat('mwp', '3d2210', 0.6, 0.0)
    mat('mbw', '2a1a08', 0.6, 0.0)
    mat('mlt', '5c3317', 0.7, 0.0)
    mat('mlt2', '4a2810', 0.7, 0.0)
    mat('mbr', 'b8860b', 0.3, 0.8)
    mat('mrp', '3d2210', 0.7, 0.0)
    mat('mlg', 'ffd700', 0.95, 0.0, 0.0)
    mat('mlge', 'ffd020', 0.2, 0.0, 5.0)  # 台灯发光
    mat('mgl', '1a4a6a', 0.4, 0.0)
    mat('mgr', '2e8a57', 0.5, 0.0)
    mat('mmf', '5c4033', 0.6, 0.0)
    mat('moc', 'b0c0d0', 0.8, 0.0)
    mat('mrg', '228822', 0.85, 0.0)
    mat('mpo', '8b4513', 0.8, 0.0)
    mat('mcc', 'f5f0dc', 0.2, 0.0)
    mat('mcur', '8b0000', 0.9, 0.0)
    mat('mwlg', '80a8c0', 0.05, 0.0, 0.8)  # 窗透光
    bc = ['8b0000','00008b','006400','800000','191970','4b0082','8b4513','2f4f4f','556b2f','b8860b']

    box('fl', 600, 500, 10, 0, 0, -5, 'mf', '5c3317', 0.4)
    box('ce', 600, 500, 10, 0, 0, 405, 'mc', 'f8f4e8', 0.9)
    box('bw', 600, 10, 400, 0, -500, 200, 'mw', 'e0d4c0', 0.85)
    box('lw', 10, 500, 400, -600, 0, 200, 'mw', 'e0d4c0', 0.85)
    box('rw', 10, 500, 400, 600, 0, 200, 'mw', 'e0d4c0', 0.85)
    box('wpb', 600, 8, 180, 0, -492, 90, 'mwp', '3d2210', 0.6)
    box('cr', 610, 8, 4, 0, -492, 185, 'mwp', '5c4033', 0.6)
    # 书墙
    box('bwb', 580, 10, 380, -340, -480, 190, 'mbw', '2a1a08', 0.6)
    for sx in [-650, -30]:
        box(f'bws{sx}', 8, 30, 380, sx, -480, 190, 'mwp', '3d2210', 0.6)
    for i in range(7):
        bh = i * 55 + 5
        box(f'bsh{i}', 620, 30, 6, -340, -480, bh, 'mbw', '2a1a08', 0.6)
    for i in range(45):
        bx = -635 + (i%6)*98 + (i//6)*4
        bh = 8 + (i//6)*55
        bhr = 38 + (i%4)*8
        box(f'rb{i}', 85, 22, bhr, bx, -482, bh+bhr//2, f'mrb{i}', bc[i%len(bc)], 0.8)
        if i%3 == 0:
            box(f'rbs{i}', 3, 22, bhr-10, bx+35, -484, bh+bhr//2, 'mbr', 'daa520', 0.8)
    # 皮沙发
    box('rcs', 130, 120, 15, 200, 100, 85, 'mlt', '5c3317', 0.7)
    box('rcb', 130, 15, 130, 200, 50, 160, 'mlt2', '4a2810', 0.7)
    box('rca', 15, 100, 70, 135, 100, 115, 'mlt2', '4a2810', 0.7)
    box('rcr', 15, 100, 70, 265, 100, 115, 'mlt2', '4a2810', 0.7)
    for (lx, ly) in [(150,170),(250,170),(150,30),(250,30)]:
        cyl(f'rcl{lx}', 4, 75, lx, ly, 35, 0,0,0, 'mbr', 'b8860b', 0.3, 0.8)
    box('ott', 100, 80, 20, 200, 200, 10, 'mlt', '5c3317', 0.7)
    for (lx, ly) in [(165,235),(235,235),(165,165),(235,165)]:
        cyl(f'ocl{lx}', 3, 50, lx, ly, 5, 0,0,0, 'mbr', 'b8860b', 0.3, 0.8)
    # 书桌 + 台灯
    box('rdsk', 200, 90, 6, -100, 200, 165, 'mlt', '5c3317', 0.6)
    for (lx, ly) in [(-185,160),(-185,240),(-15,160),(-15,240)]:
        box(f'rdl{lx}', 8, 8, 160, lx, ly, 80, 'mlt', '4a2810', 0.65)
    box('rdp', 180, 75, 3, -100, 200, 171, 'mrp', '3d2210', 0.7)
    cyl('rlb', 20, 5, -180, 200, 5, 0,0,0, 'mbr', 'b8860b', 0.3, 0.8)
    cyl('rlp', 5, 110, -180, 200, 60, 0,0,0, 'mbr', 'b8860b', 0.3, 0.8)
    cyl('rlb2', 12, 28, -180, 200, 128, 0,0,0, 'mbr', 'b8860b', 0.3, 0.8)
    cone('rls', 33, 14, 43, -180, 200, 163, 0,0,0, 'mlg', 'f5deb3', 0.95)
    sph('rlg', 8, -180, 200, 148, 'mlge', 'ffd020', 0.1, emission=5.0)
    # 地球仪
    cyl('rgs', 5, 65, 80, 200, 0, 0,0,0, 'mbr', 'b8860b', 0.3, 0.8)
    sph('rgl', 48, 80, 200, 65, 'mgl', '1a4a6a', 0.4)
    box('rgb', 68, 68, 5, 80, 200, -28, 'mbr', 'b8860b', 0.3, 0.8)
    # 地图
    box('mf', 160, 5, 110, 400, -485, 260, 'mmf', '5c4033', 0.6)
    box('mc', 148, 2, 98, 400, -490, 260, 'moc', 'b0c0d0', 0.8)
    for li, (lx, lz, lw, lh, lc) in enumerate([(370,290,30,25,'7a6a4a'),(400,280,40,30,'5a8a5a'),(420,265,20,20,'7a6a4a'),(385,260,25,18,'5a8a5a')]):
        box(f'ml{li}', lw, 2, lh, lx, -491, lz, f'mml{li}', lc, 0.9)
    # 落地窗 + 帘
    box('wf', 160, 6, 200, 0, -492, 200, 'mmf', '5c4033', 0.6)
    box('wg', 150, 3, 190, 0, -495, 200, 'mwlg', '80a8c0', 0.05, 0.0, 0.8)
    for si, sx in enumerate([-100, 100]):
        box(f'rc{si}', 6, 120, 220, sx, -370, 190, 'mcur', '8b0000', 0.9)
    cyl('rcr', 3, 220, 0, -370, 305, 0, math.pi/2, 0, 'mbr', 'b8860b', 0.3, 0.8)
    # 琴叶榕
    cyl('fpo', 33, 43, -350, 200, 21, 0,0,0, 'mpo', '8b4513', 0.8)
    sph('fp', 53, -350, 200, 95, 'mrg', '228822', 0.85)
    # 书架地球仪
    cyl('bgs', 3, 33, -550, 280, 16, 0,0,0, 'mbr', 'b8860b', 0.3, 0.8)
    sph('bgl', 18, -550, 280, 48, 'mgl', '1a4a6a', 0.4)
    # 时钟
    cyl('cc', 33, 4, -450, -480, 300, 0,0,0, 'mmf', '5c4033', 0.6)
    cyl('ccf', 28, 4, -450, -480, 300, 0,0,0, 'mcc', 'f5f0dc', 0.2)
    for i in range(12):
        ang = i * math.pi / 6
        bx = -450 + 20 * math.cos(ang)
        bz = 300 + 20 * math.sin(ang)
        sph(f'ct{i}', 2, bx, -480, bz, 'mmf', '3d2210', 0.5)

# ─────────────────────────────────────────────────────────────────
# 渲染截图
# ─────────────────────────────────────────────────────────────────
def setup_camera():
    # 移除旧相机
    for c in list(bpy.data.cameras): bpy.data.cameras.remove(c)
    # 创建相机（俯视45度）
    bpy.ops.object.camera_add(location=(0, 600, 650))
    cam = bpy.context.active_object
    cam.name = 'BakeCam'
    cam.data.type = 'PERSP'
    cam.data.lens = 40
    cam.rotation_euler = (math.radians(75), 0, math.radians(180))
    bpy.context.scene.camera = cam
    return cam

def setup_world():
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (1, 1, 1, 1)
        bg.inputs[1].default_value = 0.9

def render_screenshot(room_name, output_path, res=1920):
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.eevee.taa_render_samples = 8
    scene.render.resolution_x = res
    scene.render.resolution_y = res
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = 'JPEG'
    scene.render.image_settings.quality = 95
    scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"  → 截图: {output_path}")

# ─────────────────────────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    rooms = [
        ("office",    build_office,       "room_office",    "baked_office.jpg"),
        ("bedroom",   build_bedroom,      "room_bedroom",   "baked_bedroom.jpg"),
        ("tea_room",  build_tea_room,     "room_tea",       "baked_tea.jpg"),
        ("living",    build_living_room,  "room_living",    "baked_living.jpg"),
        ("reading",   build_reading_room, "room_reading",   "baked_reading.jpg"),
    ]

    for name, builder, glb_name, tex_name in rooms:
        print(f"\n{'='*50}")
        print(f"Building & rendering {name}...")
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        for m in list(bpy.data.materials): bpy.data.materials.remove(m)

        builder()
        setup_camera()
        setup_world()

        out_tex = OUT_DIR + tex_name
        render_screenshot(name, out_tex, res=1920)
        print(f"✅ {name} 完成!")

    print(f"\n🎉 全部完成！烘焙纹理在: {OUT_DIR}")
