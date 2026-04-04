#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
共生境 · 真实武汉OSM建筑数据抓取器 v2
======================================
使用 Overpass API "out body geom" 获取真实建筑轮廓+高度
"""
import subprocess, json, math, time, os, sys

OUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wuhan_buildings_3d.json")
CITY_CENTER_LAT, CITY_CENTER_LON = 30.58, 114.29
SCALE = 5000

# ── COORDINATE ──────────────────────────────────────────
def ll2xy(lat, lon):
    x = (lon - CITY_CENTER_LON) * SCALE * math.cos(math.radians(CITY_CENTER_LAT))
    y = (lat - CITY_CENTER_LAT) * SCALE
    return x, y

# ── BUILDING PARAMS ────────────────────────────────────
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

WALL_COLORS = {
    "apartments":(0.91,0.77,0.63),"residential":(0.88,0.75,0.60),"house":(0.93,0.82,0.68),
    "commercial":(0.85,0.65,0.45),"office":(0.82,0.60,0.40),"retail":(0.90,0.78,0.62),
    "industrial":(0.75,0.60,0.50),"school":(0.88,0.70,0.55),"university":(0.85,0.65,0.50),
    "hospital":(0.90,0.75,0.70),"hotel":(0.82,0.62,0.50),"church":(0.90,0.85,0.80),
    "temple":(0.80,0.50,0.40),"warehouse":(0.70,0.65,0.60),"yes":(0.88,0.72,0.58),
    "tower":(0.78,0.58,0.42),"skyscraper":(0.60,0.75,0.80),
}
def get_color(tags):
    rgb = WALL_COLORS.get(tags.get("building",""),(0.88,0.72,0.58))
    return {"r":round(rgb[0],3),"g":round(rgb[1],3),"b":round(rgb[2],3)}

# ── OVERPASS QUERY ────────────────────────────────────
def query_overpass(bbox, label=""):
    lat_min, lon_min, lat_max, lon_max = bbox
    print(f"  [{label}] bbox=({lat_min:.4f},{lon_min:.4f},{lat_max:.4f},{lon_max:.4f})")
    
    query = f'[out:json][timeout:120];\n(way["building"]({lat_min},{lon_min},{lat_max},{lon_max}););\nout body geom;'
    
    cmd = ["curl", "-s", "--max-time", "150",
           "-d", f"data={query}",
           "https://overpass-api.de/api/interpreter"]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    
    if not result.stdout.strip():
        print(f"  [{label}] 空响应，等待30秒重试...")
        time.sleep(30)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    
    try:
        data = json.loads(result.stdout)
        elements = data.get("elements", [])
        ways = [e for e in elements if e["type"] == "way" and "geometry" in e]
        print(f"  [{label}] ✅ {len(ways)} 个建筑")
        return ways
    except Exception as e:
        print(f"  [{label}] ❌ JSON解析失败: {e}")
        if result.stdout:
            print(f"  前200字符: {result.stdout[:200]}")
        return []

# ── PROCESS WAYS ──────────────────────────────────────
def process_ways(ways, max_dist=200):
    buildings = []
    skipped = 0
    
    for way in ways:
        tags = way.get("tags", {})
        geom = way.get("geometry", [])
        if len(geom) < 3:
            skipped += 1; continue
        
        # Centroid
        lats = [n["lat"] for n in geom]
        lons = [n["lon"] for n in geom]
        clat = sum(lats) / len(lats)
        clon = sum(lons) / len(lons)
        cx, cy = ll2xy(clat, clon)
        
        dist = math.sqrt(cx*cx + cy*cy)
        if dist > max_dist:
            skipped += 1; continue
        
        # Simplify polygon
        coords = [[round(x := ll2xy(n["lat"], n["lon"])[0], 1),
                   round(y := ll2xy(n["lat"], n["lon"])[1], 1)]
                  for n in geom]
        
        # Bounding box for approximate footprint
        xs = [c[0] for c in coords]; ys = [c[1] for c in coords]
        width  = round(max(abs(max(xs)-min(xs)), 1.0), 1)
        depth  = round(max(abs(max(ys)-min(ys)), 1.0), 1)
        
        height = round(get_height(tags), 1)
        color  = get_color(tags)
        bt     = tags.get("building", "yes")
        
        buildings.append({
            "id":   way["id"],
            "type": bt,
            "name": tags.get("name",""),
            "center": [round(cx,1), round(cy,1)],
            "height": height,
            "width":  width,
            "depth":  depth,
            "color":  color,
            "levels": tags.get("building:levels",""),
            "coords": coords,
            "addr":  (tags.get("addr:street","") + " " + tags.get("addr:housenumber","")).strip(),
        })
    
    return buildings, skipped

# ── MAIN ──────────────────────────────────────────────
def main():
    print("=" * 55)
    print("共生境 · 真实武汉OSM建筑数据抓取 v2")
    print("=" * 55)
    
    # 分9个区域块抓取（3×3网格）
    all_buildings = []
    total_ways = 0
    
    lat_stops = [30.44, 30.53, 30.62, 30.70]
    lon_stops = [114.12, 114.22, 114.32, 114.44]
    
    total_cells = (len(lat_stops)-1) * (len(lon_stops)-1)
    cell_num = 0
    
    for i in range(len(lat_stops)-1):
        for j in range(len(lon_stops)-1):
            cell_num += 1
            bbox = (lat_stops[i], lon_stops[j], lat_stops[i+1], lon_stops[j+1])
            label = f"{i*3+j+1}/{total_cells}"
            
            print(f"\n[{cell_num}/{total_cells}] 抓取区域 {chr(65+i)}{j+1}...")
            ways = query_overpass(bbox, label)
            
            if ways:
                bldgs, skip = process_ways(ways)
                all_buildings.extend(bldgs)
                total_ways += len(ways)
                print(f"  有效: {len(bldgs)}, 跳过: {skip}")
            
            # Rate limit protection
            if cell_num < total_cells:
                print(f"  等待10秒(防Overpass限速)...")
                time.sleep(12)
    
    print(f"\n总计: {total_ways} 原始建筑 → {len(all_buildings)} 有效建筑")
    
    # Save
    output = {
        "meta": {
            "source": "OpenStreetMap Overpass API",
            "city": "武汉 (Wuhan)",
            "bbox": [30.44,114.12,30.70,114.44],
            "center": [CITY_CENTER_LAT, CITY_CENTER_LON],
            "scale": SCALE,
            "total_buildings": len(all_buildings),
            "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "cells": total_cells,
        },
        "buildings": all_buildings,
    }
    
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    size = os.path.getsize(OUT_FILE)
    print(f"\n✅ 保存: {OUT_FILE}")
    print(f"📦 大小: {size/1024:.1f} KB")
    
    # Stats
    heights = [b["height"] for b in all_buildings]
    if heights:
        print(f"\n📊 统计:")
        print(f"  平均高度: {sum(heights)/len(heights):.1f}米")
        print(f"  最高: {max(heights):.1f}米, 最低: {min(heights):.1f}米")
        by_type = {}
        for b in all_buildings:
            t = b["type"]; by_type[t] = by_type.get(t,0)+1
        print("  类型TOP8:")
        for t,c in sorted(by_type.items(), key=lambda x:-x[1])[:8]:
            print(f"    {t}: {c}")
    
    return output

if __name__ == "__main__":
    main()
