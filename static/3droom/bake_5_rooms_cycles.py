"""
共生境 - 5房间高质量 Cycles 烘焙渲染
- Cycles 渲染引擎（路径追踪，真正全局光照）
- 光照贴图烘焙（bake lighting）
- 每个房间根据AI性格设计独特氛围
用法: /snap/bin/blender --background --python bake_5_rooms_final.py
"""
import bpy, os, math, sys

OUT_DIR = os.path.dirname(os.path.abspath(__file__)) + "/assets/rooms_v2/"
os.makedirs(OUT_DIR, exist_ok=True)

# ── 清理场景 ─────────────────────────────────────────────────────
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.materials): bpy.data.materials.remove(m)
for t in list(bpy.data.textures): bpy.data.textures.remove(t)
for img in list(bpy.data.images): bpy.data.images.remove(img)

# ── Cycles 配置 ─────────────────────────────────────────────────
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'         # CPU for reliability
scene.cycles.samples = 256
scene.cycles.diffuse_bounces = 3
scene.cycles.glossy_bounces = 3
scene.cycles.min_transparent_bounces = 8
scene.cycles.max_bounces = 12
scene.cycles.use_denoising = True
scene.cycles.denoiser = 'OPENIMAGEDENOISE'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1920
scene.render.image_settings.file_format = 'JPEG'
scene.render.image_settings.quality = 95

bg = world.node_tree.nodes.get("Background")
bg.inputs[0].default_value = (0.015, 0.015, 0.02, 1.0)
bg.inputs[1].default_value = 1.0

# ── 材质 helpers ─────────────────────────────────────────────────
def mat(name, hex_c, rough=0.5, metallic=0.0, emission_col=None, emission_str=0.0, spec=0.5):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name=name)
    m.use_nodes = True
    nt = m.node_tree
    nt.clear()
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    r, g, b = int(hex_c[0:2],16)/255, int(hex_c[2:4],16)/255, int(hex_c[4:6],16)/255
    bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Specular IOR Level"].default_value = spec
    if emission_col and emission_str > 0:
        ec = int(emission_col[0:2],16)/255, int(emission_col[2:4],16)/255, int(emission_col[4:6],16)/255
        bsdf.inputs["Emission Color"].default_value = (*ec, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_str
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (300, 0)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return m

def am(obj, m):
    if obj.data.materials: obj.data.materials[0] = m
    else: obj.data.materials.append(m)

def box(sx, sy, sz, lx, ly, lz, m_name, rough=0.5, metallic=0.0, emiss_col=None, emiss_str=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(lx,ly,lz))
    o = bpy.context.active_object
    o.scale = (sx, sy, sz)
    bpy.ops.object.transform_apply()
    m = mat(m_name+str(lx), m_name, rough, metallic, emiss_col, emiss_str)
    am(o, m)
    return o

def cyl(r, h, lx, ly, lz, m_name, rough=0.5, metallic=0.0, emiss_col=None, emiss_str=0.0):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=(lx,ly,lz))
    o = bpy.context.active_object
    bpy.ops.object.transform_apply()
    m = mat(m_name+str(lx), m_name, rough, metallic, emiss_col, emiss_str)
    am(o, m)
    return o

def sph(r, lx, ly, lz, m_name, rough=0.5, metallic=0.0, emiss_col=None, emiss_str=0.0):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(lx,ly,lz))
    o = bpy.context.active_object
    bpy.ops.object.transform_apply()
    m = mat(m_name+str(lx), m_name, rough, metallic, emiss_col, emiss_str)
    am(o, m)
    return o

# ── 灯光 ─────────────────────────────────────────────────────────
def add_area_light(loc, rot, size, color_hex, strength=50):
    bpy.ops.object.light_add(type='AREA', location=loc, rotation=rot)
    l = bpy.context.active_object
    l.data.color = (*[int(color_hex[i:i+2],16)/255 for i in (0,2,4)], 1.0)
    l.data.energy = strength
    l.data.size = size
    return l

def add_point_light(loc, color_hex, strength=100):
    bpy.ops.object.light_add(type='POINT', location=loc)
    l = bpy.context.active_object
    l.data.color = (*[int(color_hex[i:i+2],16)/255 for i in (0,2,4)], 1.0)
    l.data.energy = strength
    return l

# ── 相机 ─────────────────────────────────────────────────────────
def setup_camera(fov_deg=40, x=0, y=-1800, z=900, look_x=0, look_y=0, look_z=200):
    for c in list(bpy.data.cameras): bpy.data.cameras.remove(c)
    bpy.ops.object.camera_add(location=(x,y,z))
    cam = bpy.context.active_object
    cam.name = 'BakeCam'
    cam.data.type = 'PERSP'
    cam.data.lens = fov_deg
    cam.rotation_euler = (math.radians(90 + math.degrees(math.atan2(z-look_z, math.sqrt((x-look_x)**2+(y-look_y)**2)))) if (x-look_x)**2+(y-look_y)**2 > 0 else math.radians(75), 
                           0, 
                           math.radians(180 + math.degrees(math.atan2(x-look_x, y-look_y)) if abs(y-look_y) > 0.1 else 0))
    # Simple top-down-ish angle
    cam.rotation_euler = (math.radians(65), 0, math.radians(180))
    scene.camera = cam
    return cam

# ─────────────────────────────────────────────────────────────────
# Luna 卧室 - 温暖夜间氛围，柔和粉色灯光
# ─────────────────────────────────────────────────────────────────
def build_luna_bedroom():
    # 地板 - 深木色
    mat('luna_floor', '2d1810', 0.3, 0.0, '1a0a05', 0.3)
    # 墙壁 - 深蓝灰
    mat('luna_wall', '1a1e2a', 0.9, 0.0)
    # 天花板 - 深色
    mat('luna_ceil', '0f1018', 0.95, 0.0)
    # 床架 - 深木
    mat('luna_bed_f', '2a1a0a', 0.6, 0.0)
    # 床垫 - 浅色
    mat('luna_bed_m', 'e8e0d8', 0.95, 0.0)
    # 床单 - 米白
    mat('luna_sheet', 'f5f0e8', 0.9, 0.0)
    # 枕头 - 粉色
    mat('luna_pil', 'ffccd5', 0.95, 0.0)
    # 床头板 - 布艺
    mat('luna_hb', '3a2a40', 0.9, 0.0)
    # 床头柜
    mat('luna_ns', '2a1a10', 0.6, 0.0)
    # 台灯 - 暖黄发光
    mat('luna_lamp_c', '2a1a10', 0.6, 0.0)
    mat('luna_lamp_e', 'ffd080', 0.3, 0.0, 'ffd080', 8.0)  # 强发光
    # 窗户 - 深蓝夜空
    mat('luna_win', '050a18', 0.1, 0.0, '0a1830', 1.0)
    # 月亮装饰
    mat('luna_moon', 'ffe8a0', 0.2, 0.0, 'fff0b0', 4.0)
    # 衣柜
    mat('luna_ward', '1e1410', 0.65, 0.0)
    # 地毯
    mat('luna_rug', '3a1a2a', 0.95, 0.0)

    # 房间结构
    box(1400, 1200, 30, 0, 0, -15, 'luna_floor')   # 地板
    box(1400, 1200, 30, 0, 0, 415, 'luna_ceil')    # 天花板
    box(1400, 20, 400, 0, -600, 200, 'luna_wall')   # 后墙
    box(20, 1200, 400, -700, 0, 200, 'luna_wall')   # 左墙
    box(20, 1200, 400, 700, 0, 200, 'luna_wall')   # 右墙
    box(1400, 20, 400, 0, 600, 200, 'luna_wall')   # 前墙

    # 床
    box(320, 260, 35, 0, -200, 17, 'luna_bed_f')    # 床框
    box(310, 250, 30, 0, -200, 50, 'luna_bed_m')   # 床垫
    box(300, 220, 20, 0, -200, 75, 'luna_sheet')   # 床单
    for px in [-75, 75]:
        box(80, 50, 22, px, -200, 95, 'luna_pil')  # 枕头
    box(320, 20, 140, 0, -330, 110, 'luna_hb')     # 床头板

    # 床头柜 + 台灯
    for sx in [-200, 200]:
        box(65, 55, 60, sx, -280, 30, 'luna_ns')    # 柜子
        cyl(5, 45, sx, -280, 75, 'luna_lamp_c')     # 灯柱
        sph(16, sx, -280, 95, 'luna_lamp_e', 0.2, 0.0, 'ffd080', 8.0)  # 灯泡发光

    # 窗户（月夜）
    box(200, 5, 180, 0, -592, 220, 'luna_win')
    sph(40, 80, -592, 280, 'luna_moon', 0.2, 0.0, 'fff0a0', 4.0)  # 月亮

    # 衣柜
    box(220, 80, 300, -500, 200, 150, 'luna_ward')
    for i in range(3):
        box(65, 5, 280, -500+i*70, 200, 150, 'luna_ward')

    # 地毯
    box(400, 300, 3, 0, -100, -11, 'luna_rug')

    # 氛围灯（墙角）
    add_point_light((0, -400, 350), 'ffd0a0', 15)

    # 月光（窗外）
    add_point_light((0, -700, 300), '4060c0', 8)

    # 相机
    setup_camera(fov_deg=42, x=0, y=-1200, z=700, look_x=0, look_y=-200, look_z=200)

# ─────────────────────────────────────────────────────────────────
# Kai 办公室 - 冷蓝专业灯光，屏幕光
# ─────────────────────────────────────────────────────────────────
def build_kai_office():
    mat('kai_floor', '1a1510', 0.4, 0.0)
    mat('kai_wall', '1a1e28', 0.85, 0.0)
    mat('kai_ceil', '181820', 0.9, 0.0)
    mat('kai_desk', '0f0f0f', 0.3, 0.1)
    mat('kai_metal', '2a2a2a', 0.2, 0.9)
    mat('kai_scr', '001040', 0.05, 0.0, '1040ff', 5.0)  # 蓝色屏幕强发光
    mat('kai_kb', '1a1a1a', 0.6, 0.0)
    mat('kai_chair', '141418', 0.8, 0.0)
    mat('kai_globe', '1a4060', 0.4, 0.0)
    mat('kai_plant', '1a5030', 0.9, 0.0)
    mat('kai_pot', '5a3010', 0.8, 0.0)
    mat('kai_lamp', 'b8860b', 0.3, 0.8)
    mat('kai_lamp_e', 'fff0c0', 0.2, 0.0, 'ffe080', 6.0)  # 台灯发光
    mat('kai_book', '8b0000', 0.8, 0.0)
    mat('kai_wood', '2d1a0a', 0.6, 0.0)
    mat('kai_clock', '333340', 0.3, 0.0)
    mat('kai_coffee', '2a2a2a', 0.4, 0.2)

    box(1400, 1200, 30, 0, 0, -15, 'kai_floor')
    box(1400, 1200, 30, 0, 0, 415, 'kai_ceil')
    box(1400, 20, 400, 0, -600, 200, 'kai_wall')
    box(20, 1200, 400, -700, 0, 200, 'kai_wall')
    box(20, 1200, 400, 700, 0, 200, 'kai_wall')

    # 升降桌
    box(280, 130, 7, 0, 80, 160, 'kai_desk')
    for lx in [-110, 110]:
        cyl(4, 155, lx, 80, 80, 0, 0, 0, 'kai_metal')

    # 双屏显示器
    for sx in [-90, 90]:
        box(90, 5, 60, sx, 50, 215, 'kai_scr', 0.05, 0.0, '1040ff', 5.0)
        cyl(3, 42, sx, 80, 198, 0, 0, 0, 'kai_metal')
        box(45, 5, 18, sx, 80, 188, 'kai_metal')
    box(130, 35, 7, 0, 60, 168, 'kai_kb')

    # 人体工学椅
    box(110, 100, 12, 0, -30, 100, 'kai_chair')
    box(110, 12, 140, 0, -70, 170, 'kai_chair')
    box(12, 90, 55, -58, -30, 118, 'kai_chair')
    box(12, 90, 55, 58, -30, 118, 'kai_chair')
    cyl(5, 85, 0, -30, 48, 0, 0, 0, 'kai_metal')
    for i in range(5):
        ang = i * 2*math.pi/5
        cyl(4, 6, 50*math.cos(ang), -30+50*math.sin(ang), 15, 0, 0, 0, 'kai_metal')

    # 台灯
    cyl(18, 5, 140, 170, 168, 0, 0, 0, 'kai_lamp')
    cyl(4, 110, 140, 170, 174, 0, 0, math.pi/5, 'kai_lamp')
    sph(10, 165, 195, 218, 'kai_lamp_e', 0.2, 0.0, 'ffe080', 6.0)

    # 书架 + 书
    for i in range(7):
        bh = i * 55 + 5
        box(200, 28, 7, -500, 200, bh, 'kai_wood')
    box(200, 7, 390, -500, 210, 190, 'kai_wood')
    bc = ['1a3aff','cc2222','22aa22','daa520','8b008b','cd853f','2f4f4f','b8860b']
    for i in range(24):
        bx = -580 + (i%4)*42 + (i//4)*3
        bh = 10 + (i//4)*55
        bhr = 36 + (i%3)*12
        box(36, 22, bhr, bx, 208, bh+bhr//2, f'kai_book{i}', bc[i%len(bc)], 0.8)

    # 地球仪
    cyl(22, 5, 0, 130, 170, 0, 0, 0, 'kai_lamp')
    cyl(4, 55, 0, 130, 195, 0, 0, 0, 'kai_lamp')
    sph(25, 0, 130, 235, 'kai_globe')

    # 绿植
    cyl(30, 42, -520, 280, 21, 0, 0, 0, 'kai_pot')
    sph(55, -520, 280, 95, 'kai_plant')

    # 落地灯
    cyl(4, 165, 400, 200, 0, 0, 0, 0, 'kai_metal')
    cone(40, 14, 40, 400, 200, 178, 0, 0, 0, 'kai_lamp')
    sph(8, 400, 200, 158, 'kai_lamp_e', 0.2, 0.0, 'ffe080', 4.0)

    # 咖啡机
    box(55, 45, 75, 440, 200, 37, 'kai_coffee')
    sph(6, 440, 200, 82, 'kai_lamp_e', 0.3, 0.0, 'ff4000', 2.0)

    # 时钟
    cyl(32, 4, -500, -480, 300, 0, 0, 0, 'kai_clock')
    for i in range(12):
        ang = i * math.pi / 6
        bx = -500 + 22*math.cos(ang)
        bz = 300 + 22*math.sin(ang)
        sph(3, bx, -480, bz, 'kai_clock')

    # 灯光
    add_point_light((0, -400, 360), 'ffffff', 12)
    add_point_light((140, 170, 218), '4080ff', 15)   # 屏幕蓝光
    add_point_light((165, 195, 218), '4080ff', 10)  # 屏幕蓝光
    add_point_light((400, 200, 158), 'fff0c0', 8)    # 落地灯暖光

    setup_camera(fov_deg=40, x=0, y=-1200, z=700, look_x=0, look_y=80, look_z=200)

# ─────────────────────────────────────────────────────────────────
# Milo 茶室 - 日式禅意，柔和自然光
# ─────────────────────────────────────────────────────────────────
def build_milo_tearoom():
    mat('milo_floor', 'c8a870', 0.8, 0.0)
    mat('milo_ceil', 'f8f0e0', 0.95, 0.0)
    mat('milo_wall', 'f0e8d8', 0.9, 0.0)
    mat('milo_tat', 'd4c090', 0.85, 0.0)
    mat('milo_tea_w', '9a7a58', 0.65, 0.0)
    mat('milo_tea', 'c06030', 0.5, 0.0)
    mat('milo_tea2', 'f0ead0', 0.6, 0.0)
    mat('milo_zab', '5a7a5a', 0.95, 0.0)
    mat('milo_bamb', '7aaa7a', 0.75, 0.0)
    mat('milo_sand', 'e0d8c0', 0.95, 0.0)
    mat('milo_rk', '606060', 0.9, 0.0)
    mat('milo_paper', 'fff8e0', 0.9, 0.0)
    mat('milo_lan_e', 'ffcc60', 0.2, 0.0, 'ffcc60', 10.0)  # 纸灯笼极强发光
    mat('milo_inc', 'ff4000', 0.3, 0.0, 'ff4000', 1.5)
    mat('milo_flower', 'e85080', 0.4, 0.0)

    box(1400, 1200, 30, 0, 0, -15, 'milo_floor')
    box(1400, 1200, 30, 0, 0, 415, 'milo_ceil')
    box(1400, 20, 400, 0, -600, 200, 'milo_wall')
    box(20, 1200, 400, -700, 0, 200, 'milo_wall')
    box(20, 1200, 400, 700, 0, 200, 'milo_wall')

    # 榻榻米
    for xi in range(4):
        for yi in range(5):
            bx = -600 + xi*300 + 150
            by = -500 + yi*200 + 100
            box(295, 195, 8, bx, by, -4, 'milo_tat')

    # 矮茶几 + 茶具
    box(180, 100, 7, 0, 50, 82, 'milo_tea_w')
    for (lx, ly) in [(-70,15),(-70,85),(70,15),(70,85)]:
        box(9, 9, 78, lx, ly, 39, 'milo_tea_w')
    cyl(18, 25, -20, 50, 100, 0, 0, 0, 'milo_tea')
    cyl(9, 12, 20, 45, 98, 0, 0, 0, 'milo_tea2')
    cyl(9, 12, 38, 62, 98, 0, 0, 0, 'milo_tea2')
    box(85, 55, 5, 10, 60, 90, 'milo_tea_w')

    # 蒲团 × 4
    for (qx, qy) in [(-180,110),(0,110),(180,110),(0,-40)]:
        cyl(55, 16, qx, qy, 16, 0, 0, 0, 'milo_zab')

    # 竹屏风
    for pi in range(4):
        for hi in range(4):
            cyl(3, 200, -520+pi*26, 100+hi*3, 180, 0, 0, 0, 'milo_bamb')
    box(115, 5, 200, -490, 100, 180, 'milo_wall')

    # 竹子装饰
    for i in range(8):
        bx = -560 + i*38 + (i%2)*15
        by = -400 + (i%3)*20
        h = 290 + (i%4)*40
        cyl(5, h, bx, by, h//2, 0, 0, 0, 'milo_bamb')

    # 枯山水
    box(220, 130, 9, 420, -350, 4, 'milo_sand')
    for si in range(18):
        sx = 345 + (si%5)*28 + (si%3)*5
        sz = -375 + (si//5)*28
        sph(10, sx, -350, sz, 'milo_sand')
    for ri, (rx, rz, rs) in enumerate([(380,-365,25),(415,-345,32),(360,-330,20)]):
        sph(rs, rx, -350, rz, 'milo_rk')
    cyl(5, 58, 450, -340, 29, 0, 0, 0, 'milo_bamb')
    sph(30, 450, -340, 80, 'milo_bamb')

    # 壁龛 + 花
    box(190, 18, 290, 460, -485, 145, 'milo_wall')
    box(190, 45, 9, 460, -455, 4, 'milo_tea_w')
    cyl(16, 42, 430, -445, 21, 0, 0, 0, 'milo_tea')
    for ci, (fx, fz, fc) in enumerate([(415,5,'e85080'),(425,8,'ff3070'),(420,0,'e85080'),(410,10,'ff80a0')]):
        cyl(6, 32, 420+fx, -445, 52+fz, 0, 0, 0, 'milo_flower', 0.4)
        sph(8, 420+fx, -445, 68+fz, 'milo_flower', 0.4)

    # 纸灯笼（极强发光！）
    sph(60, 0, 0, 380, 'milo_lan_e', 0.2, 0.0, 'ffcc60', 10.0)
    cyl(3, 75, 0, 0, 318, 0, 0, 0, 'milo_tea_w')

    # 线香（发光）
    cyl(2, 45, 85, 55, 90, 0, 0, 0, 'milo_tea2')
    sph(4, 85, 55, 118, 'milo_inc', 0.3, 0.0, 'ff4000', 1.5)

    # 灯光 - 纸灯笼和窗外自然光
    add_point_light((0, 0, 380), 'ffcc60', 25)
    add_point_light((0, -700, 250), 'c0d8ff', 6)  # 窗透光

    setup_camera(fov_deg=42, x=0, y=-1200, z=700, look_x=0, look_y=50, look_z=200)

# ─────────────────────────────────────────────────────────────────
# Nova 客厅 - 活力彩色，动态灯光
# ─────────────────────────────────────────────────────────────────
def build_nova_living():
    mat('nova_floor', 'd4b896', 0.6, 0.0)
    mat('nova_ceil', 'ffffff', 0.9, 0.0)
    mat('nova_wall', 'ece4d8', 0.85, 0.0)
    mat('nova_sofa', '3a6a8a', 0.85, 0.0)
    mat('nova_sofa2', '2a5a7a', 0.85, 0.0)
    mat('nova_pil', 'ff6060', 0.9, 0.0)
    mat('nova_tv', '050a18', 0.05, 0.0, '1040c0', 4.0)  # 电视蓝光
    mat('nova_metal', 'c0c0c0', 0.2, 0.9)
    mat('nova_plant', '228822', 0.9, 0.0)
    mat('nova_pot', '8b4513', 0.8, 0.0)
    mat('nova_lamp', 'fff0d0', 0.95, 0.0)
    mat('nova_lamp_e', 'ffe080', 0.2, 0.0, 'ffe080', 5.0)
    mat('nova_art', 'e0d8c8', 0.9, 0.0)
    mat('nova_rug', 'c87070', 0.95, 0.0)
    mat('nova_gl', '90b0c8', 0.05, 0.0, '90b0c8', 0.8)

    box(1400, 1200, 30, 0, 0, -15, 'nova_floor')
    box(1400, 1200, 30, 0, 0, 415, 'nova_ceil')
    box(1400, 20, 400, 0, -600, 200, 'nova_wall')
    box(20, 1200, 400, -700, 0, 200, 'nova_wall')
    box(20, 1200, 400, 700, 0, 200, 'nova_wall')

    # L型沙发
    box(260, 130, 42, -80, 0, 21, 'nova_sofa')
    box(260, 16, 100, -80, -58, 92, 'nova_sofa2')
    box(16, 130, 65, -228, 0, 53, 'nova_sofa2')
    box(16, 90, 65, 28, 40, 53, 'nova_sofa2')
    for si, (sx, sy) in enumerate([(-160,20),(-90,20),(-20,20),(-160,-20),(-90,-20)]):
        box(60, 60, 16, sx, sy, 58, 'nova_sofa')
    for pi, (px, py, pc) in enumerate([(-170,10,'ff4040'),(-110,15,'ffd020'),(-50,10,'40a040'),(15,20,'4080ff')]):
        box(42, 16, 42, px, py, 68, f'nova_pil{pi}', pc, 0.9)

    # 玻璃茶几
    box(150, 85, 5, 160, 0, 78, 'nova_gl', 0.05, 0.0, '90b0c8', 0.8)
    for (lx, ly) in [(-58,-30),(-58,30),(58,-30),(58,30)]:
        cyl(4, 72, 160+lx, ly, 36, 0, 0, 0, 'nova_metal')
    box(55, 38, 5, 150, 10, 82, 'nova_art')
    cyl(12, 30, 175, 0, 90, 0, 0, 0, 'nova_plant')
    sph(12, 175, 0, 102, 'nova_plant')

    # 电视墙
    box(210, 50, 65, 0, -350, 32, 'nova_metal')
    box(210, 5, 50, 0, -350, 67, 'nova_metal')
    box(210, 8, 120, 0, -350, 180, 'nova_tv', 0.05, 0.0, '1040c0', 4.0)
    box(160, 16, 14, 0, -350, 75, 'nova_metal')

    # 绿植
    cyl(30, 42, -520, 280, 21, 0, 0, 0, 'nova_pot')
    sph(55, -520, 280, 90, 'nova_plant')
    cyl(9, 52, -520, 280, 26, 0, 0, 0, 'nova_pot')
    cyl(22, 32, -520, 185, 16, 0, 0, 0, 'nova_pot')
    sph(35, -520, 185, 70, 'nova_plant')

    # 落地灯
    cyl(4, 160, 450, 290, 0, 0, 0, 0, 'nova_metal')
    cone(42, 15, 42, 450, 290, 174, 0, 0, 0, 'nova_lamp')
    sph(8, 450, 290, 154, 'nova_lamp_e', 0.2, 0.0, 'ffe080', 5.0)

    # 艺术墙
    box(190, 6, 105, -400, -485, 260, 'nova_metal')
    box(178, 3, 93, -400, -490, 260, 'nova_art')
    for ci, (cx, cz, cc) in enumerate([(-448,285,'ff4040'),(-418,275,'ffa020'),(-388,285,'ffd020'),(-448,240,'40a040'),(-408,235,'8040ff')]):
        box(38, 3, 32, cx, -491, cz, f'nova_ab{ci}', cc, 0.9)

    # 地毯
    box(420, 320, 4, 0, 0, -12, 'nova_rug')

    # 彩色灯光
    add_point_light((0, -400, 360), 'ffffff', 15)
    add_point_light((0, -350, 180), '1040c0', 20)   # 电视蓝光
    add_point_light((450, 290, 154), 'ffe080', 12) # 落地灯
    add_point_light((-200, 50, 80), 'ff4020', 6)   # 暖色沙发灯

    setup_camera(fov_deg=42, x=0, y=-1200, z=700, look_x=0, look_y=0, look_z=200)

# ─────────────────────────────────────────────────────────────────
# Sage 书房 - 古典书香，温暖台灯
# ─────────────────────────────────────────────────────────────────
def build_sage_study():
    mat('sage_floor', '5c3317', 0.4, 0.0)
    mat('sage_ceil', 'f8f4e8', 0.9, 0.0)
    mat('sage_wall', 'e0d4c0', 0.85, 0.0)
    mat('sage_wall_p', '3d2210', 0.6, 0.0)
    mat('sage_bw', '2a1a08', 0.6, 0.0)
    mat('sage_lt', '5c3317', 0.7, 0.0)
    mat('sage_lt2', '4a2810', 0.7, 0.0)
    mat('sage_brass', 'b8860b', 0.3, 0.8)
    mat('sage_lamp_e', 'ffd700', 0.1, 0.0, 'ffd020', 8.0)  # 台灯极强发光
    mat('sage_globe', '1a4a6a', 0.4, 0.0)
    mat('sage_globe_l', '2e8a57', 0.5, 0.0)
    mat('sage_mf', '5c4033', 0.6, 0.0)
    mat('sage_map', 'b0c0d0', 0.8, 0.0)
    mat('sage_plant', '228822', 0.85, 0.0)
    mat('sage_pot', '8b4513', 0.8, 0.0)
    mat('sage_cur', '8b0000', 0.9, 0.0)
    mat('sage_win', '80a8c0', 0.05, 0.0, '6090b0', 1.2)
    mat('sage_clock', 'f5f0dc', 0.2, 0.0)

    box(1400, 1200, 30, 0, 0, -15, 'sage_floor')
    box(1400, 1200, 30, 0, 0, 415, 'sage_ceil')
    box(1400, 20, 400, 0, -600, 200, 'sage_wall')
    box(20, 1200, 400, -700, 0, 200, 'sage_wall')
    box(20, 1200, 400, 700, 0, 200, 'sage_wall')
    box(1400, 8, 200, 0, -592, 100, 'sage_wall_p')  # 护墙板
    box(1420, 8, 5, 0, -592, 195, 'sage_wall_p')    # 顶线

    # 书墙
    box(620, 10, 400, -360, -480, 200, 'sage_bw')
    for sx in [-680, -40]:
        box(9, 32, 400, sx, -480, 200, 'sage_wall_p')
    for i in range(8):
        bh = i * 50 + 5
        box(640, 32, 7, -360, -480, bh, 'sage_bw')
    box(640, 32, 7, -360, -480, 405, 'sage_bw')
    bc = ['8b0000','00008b','006400','800000','191970','4b0082','8b4513','2f4f4f','556b2f','b8860b']
    for i in range(42):
        bx = -665 + (i%6)*100 + (i//6)*4
        bh = 8 + (i//6)*50
        bhr = 35 + (i%4)*8
        box(88, 24, bhr, bx, -482, bh+bhr//2, f'sage_rb{i}', bc[i%len(bc)], 0.8)
        if i%3 == 0:
            box(4, 24, bhr-10, bx+38, -484, bh+bhr//2, 'sage_brass')

    # 皮沙发
    box(140, 130, 16, 220, 110, 88, 'sage_lt')
    box(140, 16, 140, 220, 55, 168, 'sage_lt2')
    box(16, 110, 75, 148, 110, 120, 'sage_lt2')
    box(16, 110, 75, 292, 110, 120, 'sage_lt2')
    for (lx, ly) in [(165,180),(275,180),(165,40),(275,40)]:
        cyl(5, 80, lx, ly, 38, 0, 0, 0, 'sage_brass')
    box(110, 90, 22, 220, 210, 11, 'sage_lt')
    for (lx, ly) in [(182,245),(258,245),(182,175),(258,175)]:
        cyl(4, 55, lx, ly, 5, 0, 0, 0, 'sage_brass')

    # 书桌 + 台灯
    box(220, 100, 7, -80, 200, 170, 'sage_lt')
    for (lx, ly) in [(-185,165),(-185,235),(-15,165),(-15,235)]:
        box(9, 9, 165, lx, ly, 82, 'sage_lt')
    box(200, 82, 4, -80, 200, 176, 'sage_lt')
    cyl(22, 6, -190, 200, 6, 0, 0, 0, 'sage_brass')
    cyl(6, 120, -190, 200, 65, 0, 0, 0, 'sage_brass')
    cyl(14, 32, -190, 200, 132, 0, 0, 0, 'sage_brass')
    cone(36, 15, 48, -190, 200, 168, 0, 0, 0, 'sage_lamp_e', 0.1, 0.0, 'ffd020', 8.0)
    sph(10, -190, 200, 152, 'sage_lamp_e', 0.1, 0.0, 'ffd020', 8.0)

    # 地球仪
    cyl(6, 70, 90, 200, 0, 0, 0, 0, 'sage_brass')
    sph(52, 90, 200, 70, 'sage_globe')
    box(72, 72, 6, 90, 200, -28, 'sage_brass')

    # 古典地图
    box(170, 6, 115, 420, -485, 270, 'sage_mf')
    box(158, 3, 103, 420, -490, 270, 'sage_map')
    for li, (lx, lz, lw, lh, lc) in enumerate([(390,300,32,28,'7a6a4a'),(420,290,42,32,'5a8a5a'),(440,275,22,22,'7a6a4a'),(405,270,28,20,'5a8a5a')]):
        box(lw, 3, lh, lx, -491, lz, f'sage_ml{li}', lc, 0.9)

    # 落地窗 + 帘
    box(170, 7, 210, 0, -492, 210, 'sage_mf')
    box(158, 4, 198, 0, -495, 210, 'sage_win', 0.05, 0.0, '6090b0', 1.2)
    for si, sx in enumerate([-105, 105]):
        box(7, 130, 225, sx, -370, 195, 'sage_cur')
    cyl(4, 225, 0, -370, 310, 0, math.pi/2, 0, 'sage_brass')

    # 琴叶榕
    cyl(36, 48, -360, 200, 24, 0, 0, 0, 'sage_pot')
    sph(58, -360, 200, 100, 'sage_plant')

    # 时钟
    cyl(36, 5, -460, -480, 310, 0, 0, 0, 'sage_mf')
    cyl(30, 5, -460, -480, 310, 0, 0, 0, 'sage_clock')
    for i in range(12):
        ang = i * math.pi / 6
        bx = -460 + 22*math.cos(ang)
        bz = 310 + 22*math.sin(ang)
        sph(3, bx, -480, bz, 'sage_mf')

    # 书架地球仪
    cyl(4, 36, -560, 285, 18, 0, 0, 0, 'sage_brass')
    sph(20, -560, 285, 52, 'sage_globe')

    # 灯光
    add_point_light((-190, 200, 152), 'ffd020', 30)   # 台灯金黄光
    add_point_light((90, 200, 70), 'ffd010', 15)     # 地球仪
    add_point_light((0, -495, 210), '6090c0', 10)    # 窗透光
    add_point_light((-460, -480, 310), 'ffd080', 6) # 时钟
    add_point_light((-360, 200, 100), '205020', 8)  # 绿植

    setup_camera(fov_deg=42, x=0, y=-1200, z=700, look_x=0, look_y=200, look_z=200)

# ─────────────────────────────────────────────────────────────────
# 渲染并导出
# ─────────────────────────────────────────────────────────────────
def render_room(name, builder, out_prefix):
    print(f"\n{'='*50}")
    print(f"Building & rendering {name}...")
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for m in list(bpy.data.materials): bpy.data.materials.remove(m)

    builder()

    # Cycles 渲染
    out_path = OUT_DIR + f"baked_{out_prefix}.jpg"
    scene.render.filepath = out_path
    scene.render.image_settings.file_format = 'JPEG'
    scene.render.image_settings.quality = 95
    bpy.ops.render.render(write_still=True)
    print(f"  → {out_path}")

    # 导出简化的 GLB（用于参考定位）
    # 我们不需要导出GLB，因为rooms_v2已经有了
    print(f"✅ {name} 渲染完成!")

rooms = [
    ("luna",   build_luna_bedroom,   "luna_bedroom",   "room_bedroom"),
    ("kai",    build_kai_office,      "kai_office",     "room_office"),
    ("milo",   build_milo_tearoom,    "milo_tea",       "room_tea"),
    ("nova",   build_nova_living,     "nova_living",    "room_living"),
    ("sage",   build_sage_study,      "sage_reading",   "room_reading"),
]

if __name__ == "__main__":
    for name, builder, tex_name, glb_name in rooms:
        render_room(name, builder, tex_name)
    print(f"\n🎉 全部完成！高质量烘焙图在: {OUT_DIR}")
