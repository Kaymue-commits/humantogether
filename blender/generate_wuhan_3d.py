#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
共生境 · Blender 自动化 3D 城市生成器
========================================
自动下载 OSM 地图数据 → 在 Blender 中生成 3D 建筑群 → 导出 glTF

使用方法:
  cd /home/robot/.openclaw/workspace/humantogether/blender
  python3 generate_wuhan_3d.py

输出:
  wuhan_3d_city.glb  → Three.js 可直接加载
  wuhan_3d_city.gltf → 可用其他工具转换
"""

import subprocess, os, json, math, time

# ── 配置 ──────────────────────────────────────────────
BLENDER = "/home/robot/Downloads/blender-5.1.0-linux-x64/blender"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
GLB_FILE = os.path.join(OUT_DIR, "wuhan_3d_city.glb")
OSM_JSON = os.path.join(OUT_DIR, "wuhan_osm_data.json")
SCRIPT   = os.path.join(OUT_DIR, "blender_build_city.py")

# 武汉中心区域 bounding box
LAT_MIN, LAT_MAX = 30.50, 30.65
LON_MIN, LON_MAX = 114.20, 114.38

# ── 1. 下载 OSM 数据 ─────────────────────────────────
print("🌍 步骤1: 从 OpenStreetMap 下载武汉建筑数据...")
overpass_url = "https://overpass-api.de/api/interpreter"
query = f"""
[out:json][timeout:60];
(
  node["building"]({LAT_MIN},{LON_MIN},{LAT_MAX},{LON_MAX});
  way["building"]({LAT_MIN},{LON_MIN},{LAT_MAX},{LON_MAX});
  relation["building"]({LAT_MIN},{LON_MIN},{LAT_MAX},{LON_MAX});
);
out body;
>;
out skel qt;
"""

try:
    result = subprocess.run(
        ["curl", "-s", "--max-time", "90", "-d", f"data={query}", overpass_url],
        capture_output=True, text=True, timeout=120
    )
    osm_data = json.loads(result.stdout)
    print(f"  ✅ 下载成功! 节点数: {len(osm_data.get('elements', []))}")
    with open(OSM_JSON, "w", encoding="utf-8") as f:
        json.dump(osm_data, f, ensure_ascii=False)
    print(f"  ✅ OSM 数据已保存: {OSM_JSON}")
    ELEMENTS = osm_data.get("elements", [])
except Exception as e:
    print(f"  ❌ 下载失败: {e}")
    print("  💡 使用模拟数据继续...")
    osm_data = None

# ── 2. 生成 Blender Python 脚本 ──────────────────────
print("\n🔧 步骤2: 生成 Blender 建模脚本...")

BLENDER_SCRIPT = f'''
import bpy, math, json, os, sys

# ── 清理场景 ──────────────────────────────────────────
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
for block in bpy.data.meshes: bpy.data.meshes.remove(block)
for block in bpy.data.materials: bpy.data.materials.remove(block)
for block in bpy.data.curves: bpy.data.curves.remove(block)
print("场景已清理")

# ── 工具函数 ──────────────────────────────────────────
def latLonToXY(lat, lon, center_lat=30.58, center_lon=114.29, scale=5000):
    """经纬度 → Blender 局部坐标 (米)"""
    x = (lon - center_lon) * scale * math.cos(math.radians(center_lat))
    y = (lat - center_lat) * scale
    return x, y

def create_material(name, base_color, roughness=0.7, metallic=0.1):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat

# ── 暖色材质 ──────────────────────────────────────────
mats = {{
    "wall_cream":    create_material("wall_cream",    (0.91, 0.77, 0.63, 1.0)),
    "wall_orange":   create_material("wall_orange",   (0.88, 0.62, 0.37, 1.0)),
    "wall_sand":     create_material("wall_sand",     (0.82, 0.70, 0.55, 1.0)),
    "roof_terracotta": create_material("roof_terracotta", (0.77, 0.38, 0.27, 1.0)),
    "roof_orange":   create_material("roof_orange",   (0.94, 0.64, 0.38, 1.0)),
    "glass":         create_material("glass",         (0.48, 0.80, 0.87, 1.0), 0.05, 0.9),
    "park":          create_material("park",          (0.42, 0.61, 0.22, 1.0)),
    "road":          create_material("road",          (0.16, 0.08, 0.03, 1.0)),
    "ground":        create_material("ground",         (0.24, 0.10, 0.04, 1.0)),
    "water":         create_material("water",         (0.48, 0.80, 0.87, 1.0), 0.1, 0.3),
    "roof_green":    create_material("roof_green",    (0.42, 0.61, 0.22, 1.0)),
}}

mat_keys = list(mats.keys())

# ── 地形 ──────────────────────────────────────────────
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.1))
ground = bpy.context.active_object
ground.name = "Ground"
ground.data.materials.append(mats["ground"])

# ── 加载 OSM 数据 ─────────────────────────────────────
nodes = {{}}
ways = []
buildings_data = []

osm_path = r"{OSM_JSON}"
if os.path.exists(osm_path):
    with open(osm_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    elements = data.get("elements", [])
    building_ways = [e for e in elements if e.get("type")=="way" and "building" in e.get("tags",{})]
    print(f"加载 {{len(elements)}} OSM 元素, {{len(building_ways)}} 栋建筑...")
    for el in elements:
        if el["type"] == "node":
            nodes[el["id"]] = (el["lat"], el["lon"])
        elif el["type"] == "way":
            tags = el.get("tags", {{}})
            if "building" in tags or "building:levels" in tags:
                nd = el.get("node_refs", [])
                ways.append(nd)
                buildings_data.append({{
                    "tags": tags,
                    "height": float(tags.get("height", 
                              str(int(tags.get("building:levels", 3)) * 3.5)))
                }})
else:
    print("OSM 文件不存在，使用模拟建筑数据")

# ── 创建建筑 ──────────────────────────────────────────
def create_building(nd_coords, height, tags):
    if len(nd_coords) < 3: return None
    # Close the polygon
    coords = nd_coords + [nd_coords[0]]
    
    verts = [v for v in coords] + [(v[0], v[1], height) for v in coords]
    faces = [[i for i in range(len(coords))]]
    
    # Create mesh
    mesh = bpy.data.meshes.new("Building")
    mesh.from_pydata(coords, [], list(range(len(coords))))
    mesh.update()
    
    obj = bpy.data.objects.new("Building", mesh)
    bpy.context.collection.objects.link(obj)
    
    # Extrude
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.extrude_region_move(
        transform_value=(0, 0, height),
        transform_orientations='NORMAL'
    )
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Material
    btype = tags.get("building", "")
    if btype in ["apartments", "residential"]:
        mat = mats["wall_cream"]
    elif btype in ["office", "commercial"]:
        mat = mats["wall_orange"]
    elif btype in ["retail", "shop"]:
        mat = mats["wall_sand"]
    else:
        mat = mats[mat_keys[int(hash(str(btype))[:4], 16) % len(mat_keys)]]
    
    obj.data.materials.append(mat)
    return obj

# ── 使用模拟数据 (当没有 OSM 时) ─────────────────────
if not ways:
    print("生成模拟武汉城市建筑群...")
    import random
    random.seed(42)  # 可重复
    
    # 主要区域中心
    cx, cy = 0, 0  # Blender local coords for Wuhan center
    
    for i in range(120):
        bx = random.uniform(-60, 60)
        by = random.uniform(-60, 60)
        
        # 距离中心越近，建筑越高
        dist = math.sqrt(bx*bx + by*by)
        height = max(2, random.randint(3, 25) * 1.5 - dist * 0.3)
        width = random.uniform(3, 10)
        depth = random.uniform(3, 10)
        
        # 创建建筑
        bpy.ops.mesh.primitive_cube_add(size=1, location=(bx, by, height/2))
        bldg = bpy.context.active_object
        bldg.name = f"Building_{{i}}"
        bldg.scale = (width, depth, height)
        
        # 材质
        mat_name = random.choice(["wall_cream", "wall_orange", "wall_sand"])
        bldg.data.materials.append(mats[mat_name])
        
        # 随机添加屋顶
        if random.random() > 0.5:
            bpy.ops.mesh.primitive_cube_add(size=1, location=(bx, by, height + 0.3))
            roof = bpy.context.active_object
            roof.name = f"Roof_{{i}}"
            roof.scale = (width * 1.05, depth * 1.05, 0.6)
            rmat = random.choice(["roof_terracotta", "roof_orange", "roof_green"])
            roof.data.materials.append(mats[rmat])
        
        if i % 20 == 0:
            print(f"  已创建 {{i}} 栋建筑...")
    
    # 添加公园
    for px, py in [(-30, 30), (30, -30), (40, 40), (-40, -20)]:
        bpy.ops.mesh.primitive_cylinder_add(radius=8, depth=0.1, location=(px, py, 0.05))
        park = bpy.context.active_object
        park.name = "Park"
        park.data.materials.append(mats["park"])
        
        # 树
        for _ in range(8):
            tx = px + random.uniform(-6, 6)
            ty = py + random.uniform(-6, 6)
            th = random.uniform(2, 5)
            bpy.ops.mesh.primitive_cone_add(radius1=1.5, radius2=0, depth=th, location=(tx, ty, th/2 + 0.1))
            tree = bpy.context.active_object
            tree.name = "Tree"
            tree.data.materials.append(mats["park"])
    
    # 添加道路网格
    for x in range(-60, 61, 12):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 0, 0.05))
        road = bpy.context.active_object
        road.name = "Road_H"
        road.scale = (0.5, 60, 0.05)
        road.data.materials.append(mats["road"])
    
    for y in range(-60, 61, 12):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, y, 0.05))
        road = bpy.context.active_object
        road.name = "Road_V"
        road.scale = (60, 0.5, 0.05)
        road.data.materials.append(mats["road"])
    
    # 添加河流/湖泊
    for rx, ry, rr in [(0, -45, 12), (-45, 0, 8)]:
        bpy.ops.mesh.primitive_cylinder_add(radius=rr, depth=0.2, location=(rx, ry, 0.1))
        water = bpy.context.active_object
        water.name = "Water"
        water.data.materials.append(mats["water"])

else:
    print(f"从 OSM 创建 {{len(ways)}} 栋建筑...")
    for i, (nd_ids, bdata) in enumerate(zip(ways[:200], buildings_data[:200])):
        coords = []
        for nid in nd_ids:
            if nid in nodes:
                lat, lon = nodes[nid]
                x, y = latLonToXY(lat, lon)
                coords.append((x, y))
        if len(coords) >= 3:
            create_building(coords, bdata["height"], bdata["tags"])
        if i % 50 == 0:
            print(f"  已创建 {{i}} 栋建筑...")

# ── 添加光照 ──────────────────────────────────────────
bpy.ops.object.light_add(type='SUN', location=(20, -20, 50))
sun = bpy.context.active_object
sun.name = "Sun"
sun.data.energy = 3.0
sun.data.color = (1.0, 0.92, 0.77)  # 暖黄色

bpy.ops.object.light_add(type='AREA', location=(0, 0, 30))
fill = bpy.context.active_object
fill.name = "FillLight"
fill.data.energy = 1000
fill.data.color = (0.91, 0.64, 0.38)  # 橙色补光
fill.scale = (20, 20, 1)

# ── 添加相机 ──────────────────────────────────────────
bpy.ops.object.camera_add(location=(30, -30, 40))
cam = bpy.context.active_object
cam.name = "Camera"
cam.rotation_euler = (math.radians(65), 0, math.radians(45))
bpy.context.scene.camera = cam

# ── 导出 glTF ─────────────────────────────────────────
output_glb = r"{GLB_FILE}"
bpy.ops.export_scene.gltf(
    filepath=output_glb,
    export_format='GLB',
    use_selection=False,
    export_materials='EXPORT',
    export_colors=True,
    export_normals=True,
    export_texcoords=True,
    export_apply=True,
)
print(f"✅ 导出成功: {{output_glb}}")
'''

with open(SCRIPT, "w", encoding="utf-8") as f:
    f.write(BLENDER_SCRIPT)
print(f"  ✅ Blender 脚本已生成: {SCRIPT}")

# ── 3. 运行 Blender ─────────────────────────────────
print(f"\n🖥️ 步骤3: 在 Blender 中生成 3D 城市...")
print(f"  (这需要 1-3 分钟，请耐心等待...)")

try:
    result = subprocess.run(
        [BLENDER, "--background", "--python", SCRIPT],
        capture_output=True, text=True, timeout=600
    )
    if result.stdout:
        print(result.stdout[-2000:])  # 最后2000字符
    if result.returncode != 0:
        print(f"  ❌ Blender 运行失败 (code {result.returncode})")
        if result.stderr:
            print(f"  STDERR: {result.stderr[-1000:]}")
    else:
        print(f"  ✅ Blender 执行完成!")
except subprocess.TimeoutExpired:
    print("  ❌ Blender 运行超时 (10分钟)")
except Exception as e:
    print(f"  ❌ 错误: {e}")

# ── 4. 检查输出 ──────────────────────────────────────
if os.path.exists(GLB_FILE):
    size = os.path.getsize(GLB_FILE)
    print(f"\n🎉 成功! 3D 城市模型已生成:")
    print(f"  📁 文件: {GLB_FILE}")
    print(f"  📦 大小: {size / 1024 / 1024:.1f} MB")
    print(f"\n下一步: 在 /3d 页面加载此模型!")
else:
    print(f"\n⚠️ 模型文件未生成，查看上方日志排查问题")
