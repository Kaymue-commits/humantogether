#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
共生境 · Blender 武汉 3D 城市生成器
=================================
基于武汉真实坐标分布 + OSM风格建筑数据
完全离线运行，不依赖外部API
"""
import subprocess, os, math, random, json

BLENDER = "/home/robot/Downloads/blender-5.1.0-linux-x64/blender"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
GLB_FILE = os.path.join(OUT_DIR, "wuhan_3d_city.glb")
BLENDER_SCRIPT = os.path.join(OUT_DIR, "wuhan_build.py")

# ── 城市参数 ───────────────────────────────────────────
CITY_CENTER_LAT, CITY_CENTER_LON = 30.58, 114.29  # 武汉中心
SCALE = 5000  # 1度 ≈ 5000米

# 武汉市主要区域 (大致坐标)
DISTRICTS = [
    # (lat, lon, radius_deg, name, building_density, avg_height)
    (30.60, 114.30, 0.015, "江汉区(市中心)",    0.9, 18),  # 繁华商业
    (30.57, 114.27, 0.020, "武昌区",            0.7, 12),  # 商住混合
    (30.63, 114.33, 0.018, "江岸区",            0.7, 14),  # 沿江商务
    (30.52, 114.31, 0.025, "汉阳区",            0.5,  8),  # 工业住宅
    (30.58, 114.20, 0.020, "洪山区",            0.6, 10),  # 科技教育
    (30.65, 114.28, 0.015, "青山区",            0.4,  9),  # 工业
    (30.50, 114.23, 0.018, "沌口开发区",        0.5, 11),  # 科技园区
    (30.55, 114.35, 0.012, "东湖高新区",        0.6, 13),  # 光谷科技
]

def ll2xy(lat, lon):
    x = (lon - CITY_CENTER_LON) * SCALE * math.cos(math.radians(CITY_CENTER_LON))
    y = (lat - CITY_CENTER_LAT) * SCALE
    return x, y

# ── 生成建筑清单 ──────────────────────────────────────
random.seed(42)
buildings = []

for (dlat, dlon, radius, dname, density, avg_h) in DISTRICTS:
    cx, cy = ll2xy(dlat, dlon)
    n = int(density * 80)  # 每区建筑数量
    for i in range(n):
        angle = random.uniform(0, 2*math.pi)
        dist = random.uniform(0, radius * SCALE)
        bx = cx + dist * math.cos(angle)
        by = cy + dist * math.sin(angle)
        h = max(3, avg_h * random.uniform(0.5, 1.8))
        w = random.uniform(4, 14)
        d_ = random.uniform(4, 12)
        bt = random.choice(["公寓", "写字楼", "商场", "住宅", "厂房", "学校", "医院"])
        buildings.append((bx, by, h, w, d_, bt, dname))

print(f"Generated {len(buildings)} buildings across {len(DISTRICTS)} districts")

# Save building list for Blender
BLDG_JSON = os.path.join(OUT_DIR, "wuhan_buildings.json")
with open(BLDG_JSON, "w", encoding="utf-8") as f:
    json.dump(buildings, f)
print(f"Saved: {BLDG_JSON}")

# ── 生成 Blender 脚本 ─────────────────────────────────
SCRIPT = r"""
import bpy, math, json, os, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── CLEAR ─────────────────────────────────────────────
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
for m in list(bpy.data.meshes): bpy.data.meshes.remove(m)
for m in list(bpy.data.materials): bpy.data.materials.remove(m)
print("Cleared")

# ── MATERIALS (warm Wuhan palette) ────────────────────
def mat(name, rgb, rough=0.72, metal=0.08):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes['Principled BSDF']
    n.inputs['Base Color'].default_value = (*rgb, 1.0)
    n.inputs['Roughness'].default_value = rough
    n.inputs['Metallic'].default_value = metal
    return m

M = {
    'cream':      mat('m_cream',      (0.91, 0.77, 0.63)),
    'orange':     mat('m_orange',     (0.88, 0.63, 0.37)),
    'sand':       mat('m_sand',       (0.83, 0.71, 0.56)),
    'tan':        mat('m_tan',        (0.76, 0.62, 0.47)),
    'terracotta': mat('m_terracotta',(0.77, 0.38, 0.27)),
    'roof_org':   mat('m_roof_org',  (0.94, 0.64, 0.38)),
    'roof_grn':   mat('m_roof_grn',  (0.42, 0.61, 0.22)),
    'glass':      mat('m_glass',      (0.55, 0.82, 0.90), 0.05, 0.85),
    'park':       mat('m_park',       (0.42, 0.61, 0.22)),
    'road':       mat('m_road',       (0.17, 0.09, 0.04)),
    'ground':     mat('m_ground',     (0.24, 0.11, 0.05)),
    'water':      mat('m_water',      (0.50, 0.82, 0.88), 0.08, 0.3),
    'roof_blue':  mat('m_roof_blue', (0.50, 0.62, 0.82)),
}
ML = list(M.values())

# ── HELPERS ──────────────────────────────────────────
def cube(name, loc, scale, mat_):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    if mat_ is not None:
        o.data.materials.append(mat_)
    return o

def cylinder(name, loc, radius, depth, mat_):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc)
    o = bpy.context.active_object
    o.name = name
    if mat_ is not None:
        o.data.materials.append(mat_)
    return o

def cone(name, loc, r1, r2, depth, mat_):
    bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=depth, location=loc)
    o = bpy.context.active_object
    o.name = name
    if mat_ is not None:
        o.data.materials.append(mat_)
    return o

# ── GROUND ───────────────────────────────────────────
cube('Ground', (0,0,-0.12), (500,500,0.24), M['ground'])

# ── ROADS ────────────────────────────────────────────
print("Roads...")
for x in range(-200, 201, 18):
    cube(f'RH_{x}', (x, 0, 0.07), (1.0, 250, 0.14), M['road'])
for y in range(-200, 201, 18):
    cube(f'RV_{y}', (0, y, 0.07), (250, 1.0, 0.14), M['road'])

# ── BUILDINGS ────────────────────────────────────────
BLDG_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wuhan_buildings.json')
if os.path.exists(BLDG_JSON):
    with open(BLDG_JSON, 'r', encoding='utf-8') as f:
        bldgs = json.load(f)
else:
    bldgs = []
    print("WARNING: wuhan_buildings.json not found")

print(f"Creating {len(bldgs)} buildings...")
B_TYPES = {
    '公寓':    (M['cream'],      M['roof_org']),
    '写字楼':  (M['orange'],     M['roof_org']),
    '商场':    (M['sand'],       M['roof_blue']),
    '住宅':    (M['cream'],      M['roof_org']),
    '厂房':    (M['tan'],        M['terracotta']),
    '学校':    (M['sand'],       M['roof_grn']),
    '医院':    (M['orange'],     M['roof_blue']),
}

cnt = 0
for (bx, by, h, w, d, bt, district) in bldgs:
    mat_body, mat_roof = B_TYPES.get(bt, (random.choice(ML), M['roof_org']))
    
    # Body
    cube(f'B_{cnt}', (bx, by, h/2), (w, d, h), mat_body)
    
    # Roof
    roof_type = random.random()
    if roof_type > 0.6:
        # Flat roof
        cube(f'R_{cnt}', (bx, by, h + 0.3), (w*1.05, d*1.05, 0.6), mat_roof)
    elif roof_type > 0.3:
        # Slanted roof
        cube(f'R_{cnt}', (bx, by, h + 0.5), (w*1.1, d*1.1, 1.0), mat_roof)
    else:
        # Dome
        cylinder(f'R_{cnt}', (bx, by, h + 0.5), max(w,d)*0.6, 1.0, mat_roof)
    
    # Glass curtain walls (tall buildings only)
    if h > 15 and random.random() > 0.5:
        for side in range(4):
            angle = side * math.pi / 2
            ox = math.cos(angle) * (w/2 + 0.05)
            oy = math.sin(angle) * (d/2 + 0.05)
            cw = w if side % 2 == 0 else d
            cd = 0.08
            cube(f'CW_{cnt}_{side}', (bx+ox, by+oy, h/2), (cw*0.8, cd, h*0.7), M['glass'])
    
    cnt += 1
    if cnt % 50 == 0:
        print(f"  {cnt}/{len(bldgs)}...")

print(f"Created {cnt} buildings")

# ── PARKS ────────────────────────────────────────────
print("Parks and trees...")
park_spots = [
    (ll2xy(30.596, 114.305), 14),  # 中山公园附近
    (ll2xy(30.573, 114.279), 10),  # 洪山公园
    (ll2xy(30.623, 114.314), 12),  # 江滩公园
    (ll2xy(30.558, 114.288), 10),  # 东湖附近
    (ll2xy(30.608, 114.256),  8),  # 青山公园
    (-50, 50, 10), (-50, -50, 8), (50, 50, 8), (50, -50, 10),
]
for (px, py), pr in park_spots:
    cylinder(f'Park_{px}_{py}', (px, py, 0.1), pr, 0.15, M['park'])
    for _ in range(int(pr * 1.5)):
        tx = px + random.uniform(-pr*0.8, pr*0.8)
        ty = py + random.uniform(-pr*0.8, pr*0.8)
        th = random.uniform(2, 7)
        cone(f'Tree_{random.randint(0,9999)}', (tx, ty, th/2 + 0.15),
             random.uniform(1.0, 2.2), 0, th, M['park'])

# ── WATER (长江/东湖) ─────────────────────────────────
print("Water bodies...")
water_bodies = [
    (ll2xy(30.580, 114.270), 18, 6),   # 长江武昌段
    (ll2xy(30.590, 114.270), 14, 5), # 长江江汉段
    (ll2xy(30.570, 114.295), 10, 4),  # 东湖
    (ll2xy(30.555, 114.310),  6, 3),  # 南湖
    (0, -80, 20),  # 更大水域
]
for (wx, wy), wr, wd in water_bodies:
    cylinder(f'Water_{wx}', (wx, wy, 0.12), wr, wd, M['water'])

# ── STREET FURNITURE ─────────────────────────────────
print("Street lights...")
for i in range(30):
    x = random.uniform(-150, 150)
    y = random.uniform(-150, 150)
    # Light pole
    cylinder(f'Pole_{i}', (x, y, 3), 0.1, 6, M['tan'])
    # Light
    bpy.ops.object.light_add(type='POINT', location=(x, y, 6.5))
    l = bpy.context.active_object
    l.name = f'StreetLight_{i}'
    l.data.energy = 50
    l.data.color = (1.0, 0.9, 0.7)
    l.data.falloff_distance = 20

# ── CITY CENTER HOLOGRAM ─────────────────────────────
print("City center hologram crystal...")
# Central plaza base
cylinder('PlazaBase', (0, 0, 0.2), 12, 0.4, M['road'])
# Crystal
bpy.ops.mesh.primitive_uv_sphere_add(radius=2.5, location=(0, 0, 5))
crystal = bpy.context.active_object
crystal.name = 'Crystal'
crystal_mat = bpy.data.materials.new('crystal')
crystal_mat.use_nodes = True
c = crystal_mat.node_tree.nodes['Principled BSDF']
c.inputs['Base Color'].default_value = (0.96, 0.76, 0.38, 1.0)
c.inputs['Emission'].default_value = (0.96, 0.76, 0.38, 1.0)
c.inputs['Emission Strength'].default_value = 3.0
c.inputs['Alpha'].default_value = 0.7
crystal.data.materials.append(crystal_mat)
# Rings
for i, r in enumerate([4, 6, 8]):
    cylinder(f'Ring_{i}', (0, 0, 1 + i*0.5), r, 0.15, M['roof_org'])

# ── LIGHTING ─────────────────────────────────────────
print("Lighting...")
bpy.ops.object.light_add(type='SUN', location=(80, -60, 120))
sun = bpy.context.active_object
sun.name = 'Sun'
sun.data.energy = 4.0
sun.data.color = (1.0, 0.93, 0.78)
sun.data.angle = math.radians(30)

bpy.ops.object.light_add(type='AREA', location=(0, 0, 80))
fill = bpy.context.active_object
fill.name = 'Fill'
fill.data.energy = 3000
fill.data.color = (0.91, 0.65, 0.39)
fill.scale = (50, 50, 1)

# Ambient
bpy.ops.object.light_add(type='POINT', location=(0, 0, 60))
amb = bpy.context.active_object
amb.name = 'Ambient'
amb.data.energy = 500
amb.data.color = (0.88, 0.60, 0.38)
amb.data.falloff_distance = 200

# ── CAMERA ───────────────────────────────────────────
bpy.ops.object.camera_add(location=(80, -80, 70))
cam = bpy.context.active_object
cam.name = 'Camera'
cam.rotation_euler = (math.radians(58), 0, math.radians(45))
bpy.context.scene.camera = cam

# ── EXPORT ────────────────────────────────────────────
GLB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wuhan_3d_city.glb')
print(f"Exporting to {GLB}...")
bpy.ops.export_scene.gltf(
    filepath=GLB,
    export_format='GLB',
    use_selection=False,
    export_materials='EXPORT',
    export_colors=True,
    export_normals=True,
)
print(f"SUCCESS: {GLB}")
"""

with open(BLENDER_SCRIPT, "w", encoding="utf-8") as f:
    f.write(SCRIPT)
print(f"Blender script: {BLENDER_SCRIPT}")

# ── RUN BLENDER ───────────────────────────────────────
print(f"\nRunning Blender... (3-8 minutes)")
result = subprocess.run(
    [BLENDER, "--background", "--python", BLENDER_SCRIPT],
    capture_output=True, text=True, timeout=720
)

if result.stdout:
    for line in result.stdout.strip().split("\n"):
        if any(k in line for k in ["Created", "SUCCESS", "ERROR", "Warning", "Traceback"]):
            print(f"  {line}")

if result.returncode != 0:
    print(f"BLENDER ERROR {result.returncode}")
    if result.stderr:
        err = result.stderr.strip().split("\n")
        for l in err[-10:]: print(f"  STDERR: {l}")
else:
    print("\n✅ Blender finished!")

# ── CHECK OUTPUT ──────────────────────────────────────
if os.path.exists(GLB_FILE):
    size = os.path.getsize(GLB_FILE)
    print(f"\n🎉 3D武汉城市已生成!")
    print(f"   文件: {GLB_FILE}")
    print(f"   大小: {size/1024/1024:.1f} MB")
else:
    print(f"\n⚠️  GLB未生成，检查上方日志")
