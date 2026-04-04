#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
共生境 · 真实OSM建筑3D数据 → Three.js几何
=========================================
读取 wuhan_buildings_3d.json
生成 Three.js 可直接加载的 JS 模块
"""
import json, os, math

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IN_FILE = os.path.join(SCRIPT_DIR, "wuhan_buildings_3d.json")
OUT_FILE = os.path.join(SCRIPT_DIR, "osm_buildings.js")
CITY_CENTER_LAT, CITY_CENTER_LON = 30.58, 114.29
SCALE = 5000

def ll2xy(lat, lon):
    x = (lon - CITY_CENTER_LON) * SCALE * math.cos(math.radians(CITY_CENTER_LON))
    y = (lat - CITY_CENTER_LAT) * SCALE
    return x, y

def gen_threejs_code(buildings):
    """生成 Three.js JavaScript 代码"""
    
    lines = []
    lines.append("// 共生境 · 真实武汉OSM建筑3D数据")
    lines.append(f"// Generated: {__import__('time').strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"// Total buildings: {len(buildings)}")
    lines.append("")
    lines.append("const OSM_BUILDINGS_DATA = [")
    
    for b in buildings:
        bt = b["type"]
        center = b.get("center", [0, 0])
        height = b["height"]
        color = b["color"]
        coords = b.get("coords", [])
        
        # Simple box representation (center + width/depth)
        # For buildings with real polygon, use polygon
        if len(coords) >= 3 and b.get("use_polygon", False):
            # Full polygon - triangulate as simple fan
            poly_str = str(coords[:16])  # Limit vertices
        else:
            # Box representation
            cx, cy = center[0], center[1]
            w = b["width"]
            d = b["depth"]
            # Normalized polygon (4 corners)
            corners = [
                [cx - w/2, cy - d/2],
                [cx + w/2, cy - d/2],
                [cx + w/2, cy + d/2],
                [cx - w/2, cy + d/2],
            ]
            poly_str = str(corners)
        
        lines.append(f"  {{")
        lines.append(f"    id:{b['id']},")
        lines.append(f"    type:'{bt}',")
        lines.append(f"    center:{center},")
        lines.append(f"    height:{height},")
        lines.append(f"    width:{b['width']},")
        lines.append(f"    depth:{b['depth']},")
        lines.append(f"    color:{{r:{color['r']},g:{color['g']},b:{color['b']}}},")
        lines.append(f"    name:\"{b.get('name','').replace('\"','\\\"')}\",")
        lines.append(f"  }},")
    
    lines.append("];")
    lines.append("")
    lines.append(f"const OSM_BUILDINGS_META = {{")
    lines.append(f"  total: {len(buildings)},")
    lines.append(f"  city: '武汉',")
    lines.append(f"  source: 'OpenStreetMap',")
    lines.append(f"}};")
    lines.append("")
    lines.append("// Export for module usage")
    lines.append("if (typeof module !== 'undefined' && module.exports) {")
    lines.append("  module.exports = { OSM_BUILDINGS_DATA, OSM_BUILDINGS_META };")
    lines.append("}")
    
    return "\n".join(lines)

def main():
    print("Reading OSM buildings data...")
    with open(IN_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    buildings = data.get("buildings", [])
    print(f"Loaded {len(buildings)} buildings")
    
    # Filter to most important buildings
    # Keep: skyscrapers, tall buildings, landmarks, varied types
    important = []
    normal = []
    
    for b in buildings:
        if b["height"] > 25 or b["type"] in ("skyscraper","tower","commercial","office","university","hospital","church","temple"):
            important.append(b)
        elif b["height"] >= 8:
            normal.append(b)
    
    # Sort important by height descending
    important.sort(key=lambda x: -x["height"])
    
    # Take all important + representative normal (max 5000 for performance)
    MAX = 5000
    selected = important[:MAX] + normal[:max(0, MAX - len(important))]
    selected.sort(key=lambda x: -x["height"])
    
    print(f"Selected {len(selected)} buildings for 3D (from {len(buildings)})")
    
    # Generate JS
    js_code = gen_threejs_code(selected)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(js_code)
    
    size = os.path.getsize(OUT_FILE)
    print(f"Saved: {OUT_FILE} ({size/1024:.1f} KB)")
    
    return selected

if __name__ == "__main__":
    main()
