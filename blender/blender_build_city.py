
import bpy, math, json, os, sys, random

# ── CLEAR SCENE ──────────────────────────────────────
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
for block in list(bpy.data.meshes) + list(bpy.data.materials) + list(bpy.data.curves):
    try: bpy.data.meshes.remove(block)
    except: pass
    try: bpy.data.materials.remove(block)
    except: pass
    try: bpy.data.curves.remove(block)
    except: pass
print("Scene cleared")

# ── COORDINATE TRANSFORM ─────────────────────────────
CENTER_LAT, CENTER_LON = 30.58, 114.29
SCALE = 5000  # meters per degree

def ll2xy(lat, lon):
    x = (lon - CENTER_LON) * SCALE * math.cos(math.radians(CENTER_LAT))
    y = (lat - CENTER_LAT) * SCALE
    return x, y

# ── WARM MATERIALS ───────────────────────────────────
def make_mat(name, rgb, rough=0.7, metallic=0.1):
    m = bpy.data.materials.new(name=name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    return m

MAT = {
    "cream":    make_mat("cream",    (0.91, 0.77, 0.63)),
    "orange":   make_mat("orange",   (0.88, 0.62, 0.37)),
    "sand":     make_mat("sand",     (0.82, 0.70, 0.55)),
    "terracotta": make_mat("terracotta", (0.77, 0.38, 0.27)),
    "roof_org": make_mat("roof_org", (0.94, 0.64, 0.38)),
    "roof_grn": make_mat("roof_grn", (0.42, 0.61, 0.22)),
    "glass":    make_mat("glass",    (0.48, 0.80, 0.87), 0.05, 0.9),
    "park":     make_mat("park",     (0.42, 0.61, 0.22)),
    "road":     make_mat("road",     (0.16, 0.08, 0.03)),
    "ground":   make_mat("ground",   (0.24, 0.10, 0.04)),
    "water":    make_mat("water",    (0.48, 0.80, 0.87), 0.1, 0.3),
}
MAT_LIST = list(MAT.values())

# ── GROUND ───────────────────────────────────────────
bpy.ops.mesh.primitive_plane_add(size=300, location=(0, 0, -0.1))
g = bpy.context.active_object
g.name = "Ground"
g.data.materials.append(MAT["ground"])

# ── OSM DATA ─────────────────────────────────────────
nodes_db = {}
osm_buildings = []

json_path = "/home/robot/.openclaw/workspace/humantogether/blender/wuhan_osm_data.json"
if os.path.exists(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    elem_list = raw.get("elements", [])
    print(f"Loaded {len(elem_list)} elements from OSM")

    for e in elem_list:
        if e["type"] == "node":
            nodes_db[e["id"]] = (e["lat"], e["lon"])
        elif e["type"] == "way":
            t = e.get("tags", {})
            if "building" in t:
                osm_buildings.append(e)

    print(f"Found {len(osm_buildings)} buildings in OSM data")
else:
    print("No OSM file, using procedural city")

# ── BUILDING CREATION ─────────────────────────────────
def make_box(name, loc, scale, mat_idx):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(MAT_LIST[mat_idx])
    return obj

def make_roof(name, loc, scale, mat_key):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(MAT[mat_key])
    return obj

random.seed(42)

if osm_buildings:
    # Use real OSM buildings (limited for performance)
    count = 0
    for way in osm_buildings[:800]:  # max 800 buildings
        tags = way.get("tags", {})
        refs = way.get("node_refs", [])
        if len(refs) < 3:
            continue

        try:
            coords = [nodes_db[n] for n in refs if n in nodes_db]
            if len(coords) < 3:
                continue
        except KeyError:
            continue

        # Calculate centroid
        cx = sum(c[0] for c in coords) / len(coords)
        cy = sum(c[1] for c in coords) / len(coords)
        x, y = ll2xy(cx, cy)

        # Height from building:levels or tags
        levels = int(tags.get("building:levels", 3))
        height = float(tags.get("height", levels * 3.5))
        height = min(max(height, 3.0), 80.0)  # clamp 3-80m

        # Building footprint (simple bounding box)
        lons = [c[1] for c in coords]
        lats = [c[0] for c in coords]
        w = abs(max(lons) - min(lons)) * SCALE * 0.9
        d = abs(max(lats) - min(lats)) * SCALE * 0.9
        w = min(max(w, 2.0), 20.0)
        d = min(max(d, 2.0), 20.0)

        # Material by building type
        bt = tags.get("building", "")
        if bt in ("apartments", "residential", "house"):
            mi = 0  # cream
        elif bt in ("office", "commercial"):
            mi = 1  # orange
        elif bt in ("retail", "shop"):
            mi = 2  # sand
        else:
            mi = hash(bt + str(way["id"])) % len(MAT_LIST)

        obj = make_box(f"Bld_{count}",
                       (x, y, height / 2),
                       (w, d, height),
                       mi)

        # Flat roof
        make_roof(f"Roof_{count}",
                  (x, y, height + 0.3),
                  (w * 1.05, d * 1.05, 0.6),
                  random.choice(["terracotta", "roof_org", "roof_grn"]))

        count += 1
        if count % 100 == 0:
            print(f"  Created {count} buildings...")

    print(f"Total OSM buildings created: {count}")

else:
    # Procedural city
    print("Building procedural city...")
    for i in range(200):
        bx = random.uniform(-80, 80)
        by = random.uniform(-80, 80)
        dist = math.sqrt(bx*bx + by*by)
        height = max(2, random.randint(4, 30) * 1.2 - dist * 0.2)
        w = random.uniform(4, 12)
        d = random.uniform(4, 12)

        mi = random.choice([0, 1, 2])
        make_box(f"PrBld_{i}", (bx, by, height/2), (w, d, height), mi)

        if random.random() > 0.4:
            make_roof(f"PrRoof_{i}", (bx, by, height + 0.3),
                      (w*1.05, d*1.05, 0.6),
                      random.choice(["terracotta", "roof_org"]))

        if i % 40 == 0:
            print(f"  {i}/200...")

    print("Procedural city done")

# ── ROADS ─────────────────────────────────────────────
print("Adding roads...")
for x in range(-100, 101, 15):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 0, 0.06))
    r = bpy.context.active_object
    r.scale = (0.8, 120, 0.06)
    r.data.materials.append(MAT["road"])

for y in range(-100, 101, 15):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, y, 0.06))
    r = bpy.context.active_object
    r.scale = (120, 0.8, 0.06)
    r.data.materials.append(MAT["road"])

# ── PARKS & WATER ─────────────────────────────────────
print("Adding parks and water...")
for px, py in [(-45, 45), (45, -45), (55, 55), (-55, -25), (0, -60)]:
    bpy.ops.mesh.primitive_cylinder_add(radius=12, depth=0.12, location=(px, py, 0.07))
    p = bpy.context.active_object
    p.name = "Park"
    p.data.materials.append(MAT["park"])

    for _ in range(12):
        tx = px + random.uniform(-9, 9)
        ty = py + random.uniform(-9, 9)
        th = random.uniform(2, 6)
        bpy.ops.mesh.primitive_cone_add(radius1=1.8, radius2=0, depth=th, location=(tx, ty, th/2 + 0.12))
        t = bpy.context.active_object
        t.name = "Tree"
        t.data.materials.append(MAT["park"])

# Water bodies
for rx, ry, rr in [(0, -55, 15), (-55, 0, 10), (60, -40, 8)]:
    bpy.ops.mesh.primitive_cylinder_add(radius=rr, depth=0.25, location=(rx, ry, 0.12))
    w = bpy.context.active_object
    w.name = "Water"
    w.data.materials.append(MAT["water"])

# ── LIGHTING ──────────────────────────────────────────
print("Adding lights...")
bpy.ops.object.light_add(type="SUN", location=(30, -30, 60))
sun = bpy.context.active_object
sun.name = "Sun"
sun.data.energy = 3.5
sun.data.color = (1.0, 0.92, 0.77)

bpy.ops.object.light_add(type="AREA", location=(0, 0, 40))
fill = bpy.context.active_object
fill.name = "Fill"
fill.data.energy = 2000
fill.data.color = (0.91, 0.64, 0.38)
fill.scale = (30, 30, 1)

# ── CAMERA ─────────────────────────────────────────────
bpy.ops.object.camera_add(location=(60, -60, 55))
cam = bpy.context.active_object
cam.name = "Camera"
cam.rotation_euler = (math.radians(58), 0, math.radians(45))
bpy.context.scene.camera = cam

# ── EXPORT GLB ─────────────────────────────────────────
output = "/home/robot/.openclaw/workspace/humantogether/blender/wuhan_3d_city.glb"
print(f"Exporting to {output}...")
bpy.ops.export_scene.gltf(
    filepath=output,
    export_format="GLB",
    use_selection=False,
    export_materials="EXPORT",
    export_colors=True,
)
print(f"DONE: {output}")
