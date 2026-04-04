#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
共生境 · 处理已有OSM数据 → 真实建筑JSON
==========================================
从 wuhan_osm_data.json 提取建筑 + 高度信息
"""
import json, math, os

IN_FILE = "/home/robot/.openclaw/workspace/humantogether/blender/wuhan_osm_data.json"
OUT_FILE = "/home/robot/.openclaw/workspace/humantogether/static/data/wuhan_buildings_3d.json"
CITY_LAT, CITY_LON = 30.58, 114.29
SCALE = 5000

def ll2xy(lat, lon):
    x = (lon - CITY_LON) * SCALE * math.cos(math.radians(CITY_LAT))
    y = (lat - CITY_LAT) * SCALE
    return x, y

def get_height(tags):
    if "height" in tags:
        try:
            h = float(tags["height"])
            if 0 < h < 500: return h
        except: pass
    if "building:levels" in tags:
        try:
            return min(int(tags["building:levels"]) * 3.5, 200)
        except: pass
    h = {
        "apartments":30,"residential":18,"house":8,"detached":8,"commercial":45,
        "office":40,"retail":12,"supermarket":10,"warehouse":10,"industrial":12,
        "school":15,"university":25,"hospital":30,"hotel":35,"church":20,
        "mosque":18,"temple":15,"tower":80,"skyscraper":150,
    }.get(tags.get("building",""), 12)
    return h

def get_color(tags):
    rgb = {
        "apartments":(0.91,0.77,0.63),"residential":(0.88,0.75,0.60),
        "house":(0.93,0.82,0.68),"commercial":(0.85,0.65,0.45),
        "office":(0.82,0.60,0.40),"retail":(0.90,0.78,0.62),
        "industrial":(0.75,0.60,0.50),"school":(0.88,0.70,0.55),
        "university":(0.85,0.65,0.50),"hospital":(0.90,0.75,0.70),
        "hotel":(0.82,0.62,0.50),"church":(0.90,0.85,0.80),
        "temple":(0.80,0.50,0.40),"warehouse":(0.70,0.65,0.60),
        "yes":(0.88,0.72,0.58),"tower":(0.78,0.58,0.42),
        "skyscraper":(0.60,0.75,0.80),
    }.get(tags.get("building",""),(0.88,0.72,0.58))
    return {"r":round(rgb[0],3),"g":round(rgb[1],3),"b":round(rgb[2],3)}

def process():
    print("Reading OSM data...")
    with open(IN_FILE, encoding="utf-8") as f:
        data = json.load(f)
    
    elements = data["elements"]
    print(f"Total elements: {len(elements)}")
    
    # Build node lookup
    nodes = {}
    for e in elements:
        if e["type"] == "node" and "lat" in e and "lon" in e:
            nodes[e["id"]] = (e["lat"], e["lon"])
    print(f"Nodes with coords: {len(nodes)}")
    
    # Get building ways
    ways = [e for e in elements if e["type"]=="way" and "building" in e.get("tags",{})]
    print(f"Building ways: {len(ways)}")
    
    buildings = []
    for i, way in enumerate(ways):
        tags = way.get("tags", {})
        node_ids = way.get("nodes", [])
        
        # Get coordinates for all nodes
        coords = []
        for nid in node_ids:
            if nid in nodes:
                lat, lon = nodes[nid]
                x, y = ll2xy(lat, lon)
                coords.append([round(x,1), round(y,1)])
        
        if len(coords) < 3:
            continue
        
        # Centroid
        cx = sum(c[0] for c in coords) / len(coords)
        cy = sum(c[1] for c in coords) / len(coords)
        dist = math.sqrt(cx*cx + cy*cy)
        
        # Skip if too far from center (> 30000m = 30km)
        if dist > 30000:
            continue
        
        # Bounding box for width/depth
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        width = round(max(abs(max(xs)-min(xs)), 1))
        depth = round(max(abs(max(ys)-min(ys)), 1))
        
        height = round(get_height(tags), 1)
        color = get_color(tags)
        
        buildings.append({
            "id": way["id"],
            "type": tags.get("building","yes"),
            "name": tags.get("name",""),
            "center": [round(cx,1), round(cy,1)],
            "height": height,
            "width": width,
            "depth": depth,
            "color": color,
            "levels": tags.get("building:levels",""),
            "coords": coords[:24],  # limit vertices for perf
            "addr": (tags.get("addr:street","") + " " + tags.get("addr:housenumber","")).strip(),
        })
        
        if (i+1) % 2000 == 0:
            print(f"  Processed {i+1}/{len(ways)}...")
    
    print(f"Valid buildings: {len(buildings)}")
    
    # Sort by height descending
    buildings.sort(key=lambda b: -b["height"])
    
    # Output
    output = {
        "meta": {
            "source": "OpenStreetMap",
            "city": "武汉 (Wuhan)",
            "bbox": [30.44,114.12,30.70,114.44],
            "center": [CITY_LAT, CITY_LON],
            "scale": SCALE,
            "total_buildings": len(buildings),
            "generated": __import__("time").strftime("%Y-%m-%d %H:%M:%S"),
        },
        "buildings": buildings,
    }
    
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    size = os.path.getsize(OUT_FILE)
    print(f"\nSaved: {OUT_FILE} ({size/1024:.1f} KB)")
    
    # Stats
    heights = [b["height"] for b in buildings]
    if heights:
        print(f"\nStats:")
        print(f"  Avg height: {sum(heights)/len(heights):.1f}m")
        print(f"  Max: {max(heights):.1f}m")
        by_type = {}
        for b in buildings:
            t = b["type"]; by_type[t] = by_type.get(t,0)+1
        for t,c in sorted(by_type.items(), key=lambda x:-x[1])[:8]:
            print(f"    {t}: {c}")
    
    return buildings

if __name__ == "__main__":
    process()
