
import bpy, math, json, os, sys, random

# Coordinate transform (Wuhan center)
CITY_LAT, CITY_LON = 30.58, 114.29
SCALE = 5000
def ll2xy(lat, lon):
    x = (lon - CITY_LON) * SCALE * math.cos(math.radians(CITY_LAT))
    y = (lat - CITY_LAT) * SCALE
    return x, y

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
    ((ll2xy(30.596, 114.305)[0], ll2xy(30.596, 114.305)[1]), 14),
    ((ll2xy(30.573, 114.279)[0], ll2xy(30.573, 114.279)[1]), 10),
    ((ll2xy(30.623, 114.314)[0], ll2xy(30.623, 114.314)[1]), 12),
    ((ll2xy(30.558, 114.288)[0], ll2xy(30.558, 114.288)[1]), 10),
    ((ll2xy(30.608, 114.256)[0], ll2xy(30.608, 114.256)[1]),  8),
    ((-50, 50), 10), ((-50, -50), 8), ((50, 50), 8), ((50, -50), 10),
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
    (ll2xy(30.580, 114.270)[0], ll2xy(30.580, 114.270)[1], 18, 6),
    (ll2xy(30.590, 114.270)[0], ll2xy(30.590, 114.270)[1], 14, 5),
    (ll2xy(30.570, 114.295)[0], ll2xy(30.570, 114.295)[1], 10, 4),
    (ll2xy(30.555, 114.310)[0], ll2xy(30.555, 114.310)[1],  6, 3),
    (0, -80, 20, 8),
]
for wx, wy, wr, wd in water_bodies:
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
    l.data.cutoff_distance = 20

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
c.inputs['Alpha'].default_value = 0.7
# Skip emission inputs for Blender 5 compatibility
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
amb.data.cutoff_distance = 200

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
    export_texcoords=True,
    export_normals=True,
)
print(f"SUCCESS: {GLB}")
