#!/usr/bin/env python3
"""Download Sierra Leone roads from OSM (Overpass) into data/*.geojson + data/meta.json.
Run by hand (python scripts/build_data.py) or automatically by .github/workflows/update-data.yml.
Standard library only."""
import json, math, os, sys, time, datetime, urllib.parse, urllib.request

OVP = ["https://overpass-api.de/api/interpreter",
       "https://overpass.kumi.systems/api/interpreter",
       "https://overpass.private.coffee/api/interpreter"]
AREA = "area(id:3600192777)->.a;"          # relation 192777 = Sierra Leone
# file name -> (tier, classes). Tier 1+2 load on page open, tier 3 (local roads) on demand.
GROUPS = {"roads_t1": (1, ["motorway", "trunk", "primary"]),
          "roads_t2": (2, ["secondary", "tertiary"]),
          "roads_unclassified": (3, ["unclassified"]), "roads_residential": (3, ["residential"]),
          "roads_track": (3, ["track"]), "roads_service": (3, ["service"]), "roads_path": (3, ["path"])}
EXTRA = {"path": ["path", "footway", "cycleway", "pedestrian", "steps", "bridleway"],
         "residential": ["residential", "living_street"], "unclassified": ["unclassified", "road"]}
HW = {"living_street": "residential", "road": "unclassified", "footway": "path", "cycleway": "path",
      "pedestrian": "path", "steps": "path", "bridleway": "path"}
PAVED = set("asphalt paved concrete paving_stones sett concrete:plates concrete:lanes bricks cobblestone chipseal metal".split())

def km(c):
    d = 0
    for (x1, y1), (x2, y2) in zip(c, c[1:]):
        p = math.pi / 180
        h = math.sin((y2 - y1) * p / 2) ** 2 + math.cos(y1 * p) * math.cos(y2 * p) * math.sin((x2 - x1) * p / 2) ** 2
        d += 12742 * math.asin(math.sqrt(h))
    return round(d, 3)

def num(v):
    try: return int(str(v).split()[0])
    except Exception: return None

def feature(e, known):
    t = e.get("tags", {}); c = t.get("highway", "").replace("_link", ""); c = HW.get(c, c)
    if c not in known or "geometry" not in e: return None
    co = [[round(g["lon"], 5), round(g["lat"], 5)] for g in e["geometry"]]
    if len(co) < 2: return None
    su = t.get("surface", ""); op = lambda v: "yes" if v and v != "no" else "no"
    tt = t.get("tracktype", "")
    return {"type": "Feature", "geometry": {"type": "LineString", "coordinates": co}, "properties": {
        "id": e["id"], "cls": c, "hw": t.get("highway", ""),
        "tg": ("g" + tt[5:] if tt[:5] == "grade" and tt[5:] in "12345" and c == "track" else "none" if c == "track" else "na"),
        "name": t.get("name", ""), "ref": t.get("ref", ""), "surface": su,
        "sc": "unknown" if not su else "paved" if su in PAVED else "unpaved",
        "speed": num(t.get("maxspeed")), "lit": "unk" if "lit" not in t else "no" if t["lit"] == "no" else "yes",
        "km": km(co)}}

def overpass(query, tries=6):
    last = None
    for i in range(tries):
        url = OVP[i % len(OVP)]
        try:
            req = urllib.request.Request(url, data=urllib.parse.urlencode({"data": query}).encode(),
                                         headers={"User-Agent": "sierra-leone-roads/1.0 (31 Day OSM Challenge)"})
            j = json.load(urllib.request.urlopen(req, timeout=900))
            if "remark" in j and "error" in j["remark"].lower(): raise RuntimeError(j["remark"])
            return j["elements"]
        except Exception as ex:
            last = ex; print(f"  attempt {i+1} failed: {ex}", file=sys.stderr); time.sleep(20 * (i + 1))
    raise last

def classes_query(classes):
    tags = "|".join(x for c in classes for x in ([c, c + "_link"] if c in ("motorway", "trunk", "primary", "secondary", "tertiary") else EXTRA.get(c, [c])))
    return f'[out:json][timeout:600];{AREA}way["highway"~"^({tags})$"](area.a);out geom tags;'

def main(out_dir="data"):
    os.makedirs(out_dir, exist_ok=True)
    meta = {"updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"), "files": {"1": [], "2": [], "3": []}, "counts": {}}
    for name, (tier, classes) in GROUPS.items():
        path = os.path.join(out_dir, name + ".geojson"); print(f"{name}: {classes}")
        try:
            feats = [f for f in (feature(e, set(classes)) for e in overpass(classes_query(classes))) if f]
            feats.sort(key=lambda f: f["properties"]["id"])
            with open(path, "w") as fh:  # one feature per line keeps git diffs small
                fh.write('{"type":"FeatureCollection","features":[\n' + ",\n".join(json.dumps(f, separators=(",", ":")) for f in feats) + "\n]}")
            meta["counts"][name] = len(feats); print(f"  {len(feats)} segments, {os.path.getsize(path)/1e6:.1f} MB")
        except Exception as ex:
            print(f"  FAILED ({ex}); keeping previous file if present", file=sys.stderr)
            if not os.path.exists(path): continue
        meta["files"][str(tier)].append(name + ".geojson"); time.sleep(10)
    json.dump(meta, open(os.path.join(out_dir, "meta.json"), "w"), indent=1)

if __name__ == "__main__":
    main()
