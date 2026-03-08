# ============================================================
# CITADEL — Critical Infrastructure Vulnerability Scanner
# Geospatial defense engine with 210 simulated SCADA assets.
# ============================================================

import dash
from dash import dcc, html, callback_context
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import random
import datetime
import requests
import json
import os
import time

# ==========================================
# 1. SYSTEM CONFIGURATION
# ==========================================
SYSTEM_CONFIG = {
    "SECTOR_NAME": "US NATIONAL GRID (MULTI-SECTOR)",
    "MAP_CENTER": {"lat": 39.0, "lon": -98.0},
    "INITIAL_BLOCKS": 0,
    "THREAT_PROBABILITY": 0.15,
    "INITIAL_STABILITY": 99.9,
    "DEFCON_LEVEL": 5
}

# ==========================================
# 2. GENERATE 200+ SIMULATED SCADA ASSETS
# ==========================================

# Infrastructure Asset Types and Subtypes
ASSET_TYPES = {
    "GENERATION": {"subtypes": ["Nuclear Plant", "Coal Plant", "Gas Turbine", "Hydro Dam", "Solar Farm", "Wind Farm"], "icon": "circle", "base_color": "#3fb950"},
    "TRANSMISSION": {"subtypes": ["HV Substation", "Transformer Station", "Switching Station", "HVDC Converter"], "icon": "circle", "base_color": "#58a6ff"},
    "DISTRIBUTION": {"subtypes": ["Distribution Sub", "Feeder Station", "Metro Grid Hub", "Industrial Feeder"], "icon": "circle", "base_color": "#d2a8ff"},
    "CONTROL": {"subtypes": ["SCADA Master", "Control Center", "RTU Gateway", "DCS Controller"], "icon": "diamond", "base_color": "#ffd60a"},
    "STORAGE": {"subtypes": ["Battery Array", "Pumped Storage", "Flywheel Station", "Compressed Air"], "icon": "circle", "base_color": "#f0883e"},
}

REGIONS = [
    {"name": "Pacific Northwest", "lat_range": (42, 49), "lon_range": (-125, -117), "state_codes": ["WA", "OR"]},
    {"name": "California", "lat_range": (32, 42), "lon_range": (-125, -114), "state_codes": ["CA"]},
    {"name": "Southwest", "lat_range": (31, 37), "lon_range": (-115, -103), "state_codes": ["AZ", "NM", "NV"]},
    {"name": "Mountain", "lat_range": (37, 49), "lon_range": (-117, -104), "state_codes": ["CO", "UT", "WY", "MT", "ID"]},
    {"name": "Central", "lat_range": (30, 42), "lon_range": (-104, -90), "state_codes": ["TX", "OK", "KS", "NE"]},
    {"name": "Midwest", "lat_range": (37, 49), "lon_range": (-96, -82), "state_codes": ["IL", "IN", "OH", "MI", "WI", "MN", "IA", "MO"]},
    {"name": "Southeast", "lat_range": (25, 37), "lon_range": (-90, -75), "state_codes": ["FL", "GA", "AL", "SC", "NC", "TN", "VA"]},
    {"name": "Northeast", "lat_range": (38, 45), "lon_range": (-80, -70), "state_codes": ["NY", "PA", "NJ", "CT", "MA", "MD"]},
]

# SCADA equipment manufacturers
VENDOR_PRODUCTS = [
    {"vendor": "Siemens", "product": "SIMATIC S7", "cpe": "cpe:2.3:h:siemens:simatic_s7"},
    {"vendor": "Siemens", "product": "WinCC", "cpe": "cpe:2.3:a:siemens:wincc"},
    {"vendor": "Schneider Electric", "product": "Modicon M340", "cpe": "cpe:2.3:h:schneider-electric:modicon_m340"},
    {"vendor": "Schneider Electric", "product": "EcoStruxure", "cpe": "cpe:2.3:a:schneider-electric:ecostruxure"},
    {"vendor": "ABB", "product": "AC800M", "cpe": "cpe:2.3:h:abb:ac800m"},
    {"vendor": "ABB", "product": "Ability Symphony Plus", "cpe": "cpe:2.3:a:abb:symphony_plus"},
    {"vendor": "Rockwell", "product": "ControlLogix", "cpe": "cpe:2.3:h:rockwellautomation:controllogix"},
    {"vendor": "Rockwell", "product": "FactoryTalk", "cpe": "cpe:2.3:a:rockwellautomation:factorytalk"},
    {"vendor": "Honeywell", "product": "Experion PKS", "cpe": "cpe:2.3:a:honeywell:experion_pks"},
    {"vendor": "GE", "product": "Mark VIe", "cpe": "cpe:2.3:h:ge:mark_vie"},
    {"vendor": "Emerson", "product": "DeltaV", "cpe": "cpe:2.3:a:emerson:deltav"},
    {"vendor": "Yokogawa", "product": "CENTUM VP", "cpe": "cpe:2.3:a:yokogawa:centum_vp"},
]


def generate_scada_telemetry():
    """Generate realistic SCADA sensor readings (voltage, frequency, load, temperature, pressure)."""
    return {
        "voltage_kv": round(random.gauss(230, 8), 1),
        "frequency_hz": round(random.gauss(60.0, 0.05), 3),
        "load_mw": round(random.uniform(50, 950), 1),
        "temperature_c": round(random.gauss(45, 12), 1),
        "pressure_psi": round(random.gauss(150, 20), 1),
        "flow_rate_gpm": round(random.uniform(100, 5000), 0),
        "rate_per_minute": round(random.gauss(3600, 50), 0),
        "comms_latency_ms": round(random.expovariate(1/15), 1),
    }


def generate_assets(count=210):
    """Generate 210 simulated SCADA assets across 8 US regions with vendor assignments."""
    print(f"[*] GENERATING {count} SIMULATED SCADA ASSETS...")
    assets = []
    asset_id = 0

    # Create each asset with a random region, type, vendor, and location
    for index in range(count):
        region = random.choice(REGIONS)
        asset_type = random.choice(list(ASSET_TYPES.keys()))
        type_info = ASSET_TYPES[asset_type]
        subtype = random.choice(type_info["subtypes"])
        vendor_info = random.choice(VENDOR_PRODUCTS)

        lat = round(random.uniform(*region["lat_range"]), 4)
        lon = round(random.uniform(*region["lon_range"]), 4)

        asset_id_str = f"{asset_type[:3]}-{region['name'][:3].upper()}-{asset_id:04d}"

        assets.append({
            "id": asset_id_str,
            "name": f"{subtype} ({region['name']})",
            "type": asset_type,
            "subtype": subtype,
            "region": region["name"],
            "lat": lat,
            "lon": lon,
            "vendor": vendor_info["vendor"],
            "product": vendor_info["product"],
            "cpe": vendor_info["cpe"],
            "firmware_version": f"v{random.randint(2,8)}.{random.randint(0,9)}.{random.randint(0,99)}",
            "telemetry": generate_scada_telemetry(),
            "cves": [],
            "cvss_max": 0,
            "patch_priority": "LOW",
            "status": "NOMINAL",
        })
        asset_id += 1

    print(f"[*] {len(assets)} ASSETS GENERATED ACROSS {len(REGIONS)} REGIONS")
    return assets


# ==========================================
# 3. NIST NVD (National Vulnerability Database) INTEGRATION
# ==========================================
NVD_CACHE_FILE = "citadel_nvd_cache.json"
NVD_CACHE_MAX_AGE_HOURS = 24

def fetch_nvd_cves():
    """Fetch real CVEs data from NIST NVD API for SCADA keywords. Cached for 24h."""
    # Check cache
    if os.path.exists(NVD_CACHE_FILE):
        cache_age = time.time() - os.path.getmtime(NVD_CACHE_FILE)
        if cache_age < NVD_CACHE_MAX_AGE_HOURS * 3600:
            print(f"[*] LOADING NVD CACHE: {NVD_CACHE_FILE}")
            with open(NVD_CACHE_FILE, 'r') as file:
                cached = json.load(file)
            print(f"[*] NVD CACHE LOADED: {len(cached)} CVEs")
            return cached

    print("[*] FETCHING CVE DATA FROM NIST NVD API...")
    all_cves = []
    search_keywords = ["SCADA", "Siemens SIMATIC", "Schneider Modicon", "Rockwell ControlLogix", "industrial control", "ICS"]

    for keyword in search_keywords:
        try:
            url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch={keyword}&resultsPerPage=50"
            headers = {"Accept": "application/json"}
            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code == 200:
                data = response.json()
                vulnerabilities = data.get("vulnerabilities", [])
                for vulnerability in vulnerabilities:
                    cve_data = vulnerability.get("cve", {})
                    cve_id = cve_data.get("id", "UNKNOWN")
                    descriptions = cve_data.get("descriptions", [])
                    description = next((description["value"] for description in descriptions if description["lang"] == "en"), "No description")

                    # Extract CVSS score
                    metrics = cve_data.get("metrics", {})
                    cvss_score = 0
                    cvss_severity = "UNKNOWN"

                    if "cvssMetricV31" in metrics:
                        cvss_data = metrics["cvssMetricV31"][0]["cvssData"]
                        cvss_score = cvss_data.get("baseScore", 0)
                        cvss_severity = cvss_data.get("baseSeverity", "UNKNOWN")
                    elif "cvssMetricV2" in metrics:
                        cvss_data = metrics["cvssMetricV2"][0]["cvssData"]
                        cvss_score = cvss_data.get("baseScore", 0)
                        cvss_severity = "HIGH" if cvss_score >= 7 else "MEDIUM" if cvss_score >= 4 else "LOW"

                    all_cves.append({
                        "cve_id": cve_id,
                        "description": description[:200],
                        "cvss_score": cvss_score,
                        "cvss_severity": cvss_severity,
                        "keyword": keyword,
                    })

                print(f"    [{keyword:<25}] +{len(vulnerabilities)} CVEs | Total: {len(all_cves)}")
            else:
                print(f"    [!] NVD API returned {response.status_code} for '{keyword}'")

            time.sleep(6)  # NVD rate limit: 5 requests per 30 seconds without API key

        except Exception as e:
            print(f"    [!] NVD fetch error for '{keyword}': {e}")

    # Deduplicate
    seen_cve_ids = set()
    unique_cves = []
    for cve in all_cves:
        if cve["cve_id"] not in seen_cve_ids:
            seen_cve_ids.add(cve["cve_id"])
            unique_cves.append(cve)

    # Cache
    with open(NVD_CACHE_FILE, 'w') as file:
        json.dump(unique_cves, file)
    print(f"[*] NVD DATA CACHED: {len(unique_cves)} unique CVEs")
    return unique_cves


def map_cves_to_assets(assets, cves):
    """Map CVEs to assets based on vendor matching and assign patch priority."""
    print("[*] MAPPING CVEs TO NETWORK ASSETS...")
    mapped_count = 0

    vendor_cve_map = {}
    for cve in cves:
        kw = cve["keyword"].lower()
        for vendor_product in VENDOR_PRODUCTS:
            if vendor_product["vendor"].lower() in kw or vendor_product["product"].lower().split()[0].lower() in kw:
                vendor_name = vendor_product["vendor"]
                if vendor_name not in vendor_cve_map:
                    vendor_cve_map[vendor_name] = []
                vendor_cve_map[vendor_name].append(cve)

    # Collect CVEs that apply to SCADA systems in general (not vendor-specific)
    general_cves = [cve for cve in cves if cve["keyword"].lower() in ["scada", "industrial control", "ics"]]

    for asset in assets:
        asset_cves = []

        # Vendor-specific CVEs
        if asset["vendor"] in vendor_cve_map:
            vendor_cves = vendor_cve_map[asset["vendor"]]
            num_to_assign = random.randint(0, min(5, len(vendor_cves)))
            asset_cves.extend(random.sample(vendor_cves, num_to_assign))

        # General ICS CVEs (small chance)
        if general_cves and random.random() < 0.3:
            num_general = random.randint(1, min(3, len(general_cves)))
            asset_cves.extend(random.sample(general_cves, num_general))

        # Deduplicate
        seen_ids = set()
        unique_asset_cves = []
        for cve in asset_cves:
            if cve["cve_id"] not in seen_ids:
                seen_ids.add(cve["cve_id"])
                unique_asset_cves.append(cve)

        # Save deduplicated CVEs to the asset
        asset["cves"] = unique_asset_cves

        if unique_asset_cves:
            mapped_count += 1
            max_cvss = max(cve["cvss_score"] for cve in unique_asset_cves)
            asset["cvss_max"] = max_cvss

            # Patch priority based on CVSS score
            if max_cvss >= 9.0:
                asset["patch_priority"] = "CRITICAL"
                asset["status"] = "VULNERABLE"
            elif max_cvss >= 7.0:
                asset["patch_priority"] = "HIGH"
                asset["status"] = "AT RISK"
            elif max_cvss >= 4.0:
                asset["patch_priority"] = "MEDIUM"
                asset["status"] = "MONITOR"
            else:
                asset["patch_priority"] = "LOW"
                asset["status"] = "NOMINAL"
        else:
            asset["cvss_max"] = 0
            asset["patch_priority"] = "LOW"
            asset["status"] = "NOMINAL"

    print(f"[*] CVE MAPPING COMPLETE: {mapped_count}/{len(assets)} assets have vulnerabilities")
    return assets


# ==========================================
# 4. PATCH PRIORITY REPORT
# ==========================================
def generate_patch_report(assets, cves):
    """Generate vulnerability report with patch prioritization and regional breakdown."""
    now = datetime.datetime.now(datetime.timezone.utc)
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S UTC")

    critical_assets = [asset for asset in assets if asset["patch_priority"] == "CRITICAL"]
    high_assets = [asset for asset in assets if asset["patch_priority"] == "HIGH"]
    medium_assets = [asset for asset in assets if asset["patch_priority"] == "MEDIUM"]
    low_assets = [asset for asset in assets if asset["patch_priority"] == "LOW"]
    vulnerable_assets = [asset for asset in assets if len(asset["cves"]) > 0]

    lines = []
    lines.append("=" * 80)
    lines.append("CITADEL // VULNERABILITY & PATCH PRIORITY REPORT")
    lines.append("=" * 80)
    lines.append(f"GENERATED:        {timestamp}")
    lines.append(f"DATA SOURCE:      NIST National Vulnerability Database (NVD)")
    lines.append(f"ASSETS SCANNED:   {len(assets)}")
    lines.append(f"CVEs LOADED:      {len(cves)}")
    lines.append(f"ASSETS AFFECTED:  {len(vulnerable_assets)}")
    lines.append("")
    lines.append("-" * 80)
    lines.append("1. PATCH PRIORITY SUMMARY")
    lines.append("-" * 80)
    lines.append(f"   CRITICAL:  {len(critical_assets):>4} assets (CVSS >= 9.0)")
    lines.append(f"   HIGH:      {len(high_assets):>4} assets (CVSS >= 7.0)")
    lines.append(f"   MEDIUM:    {len(medium_assets):>4} assets (CVSS >= 4.0)")
    lines.append(f"   LOW:       {len(low_assets):>4} assets (CVSS < 4.0 or no CVEs)")
    lines.append("")

    lines.append("-" * 80)
    lines.append("2. TOP 15 CRITICAL ASSETS REQUIRING IMMEDIATE PATCHING")
    lines.append("-" * 80)
    sorted_assets = sorted(assets, key=lambda x: x["cvss_max"], reverse=True)
    for rank, asset in enumerate(sorted_assets[:15], 1):
        lines.append(f"   {rank:>2}. {asset['name'][:40]:<42}")
        lines.append(f"       ID: {asset['id']} | Region: {asset['region']}")
        lines.append(f"       Vendor: {asset['vendor']} | Product: {asset['product']} | FW: {asset['firmware_version']}")
        lines.append(f"       Max CVSS: {asset['cvss_max']:.1f} | Priority: {asset['patch_priority']}")
        lines.append(f"       CVEs: {len(asset['cves'])} | Coords: {asset['lat']:.4f}, {asset['lon']:.4f}")
        if asset['cves']:
            top_cve = max(asset['cves'], key=lambda cve: cve['cvss_score'])
            lines.append(f"       Top CVE: {top_cve['cve_id']} (CVSS {top_cve['cvss_score']})")
        lines.append("")

    # Regional Summary
    lines.append("-" * 80)
    lines.append("3. REGIONAL VULNERABILITY BREAKDOWN")
    lines.append("-" * 80)
    region_stats = {}
    for asset in assets:
        region_name = asset["region"]
        if region_name not in region_stats:
            region_stats[region_name] = {"total": 0, "vulnerable": 0, "critical": 0, "avg_cvss": []}
        region_stats[region_name]["total"] += 1
        if asset["cves"]:
            region_stats[region_name]["vulnerable"] += 1
            region_stats[region_name]["avg_cvss"].append(asset["cvss_max"])
        if asset["patch_priority"] == "CRITICAL":
            region_stats[region_name]["critical"] += 1

    for region, stats in sorted(region_stats.items()):
        avg = sum(stats["avg_cvss"]) / len(stats["avg_cvss"]) if stats["avg_cvss"] else 0
        lines.append(f"   {region:<22} Assets: {stats['total']:>3} | Vulnerable: {stats['vulnerable']:>3} | Critical: {stats['critical']:>3} | Avg CVSS: {avg:.1f}")

    lines.append("")
    lines.append("=" * 80)
    lines.append("END OF REPORT")
    lines.append("=" * 80)

    # Save report to patch_reports/ folder
    report_text = "\n".join(lines)
    os.makedirs("patch_reports", exist_ok=True)
    filename = f"patch_reports/CITADEL_PATCH_{now.strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, 'w') as file:
        file.write(report_text)
    print(f"[*] PATCH REPORT SAVED: {filename}")
    return report_text, filename


# ==========================================
# 5. THREAT GROUPS
# ==========================================
THREAT_GROUPS = [
    {"org": "APT-29 (RUSSIA)", "origin": "RUS"},
    {"org": "APT-1 (CHINA)", "origin": "CHN"},
    {"org": "LAZARUS (N. KOREA)", "origin": "DPRK"},
    {"org": "SANDWORM (RUSSIA)", "origin": "RUS"},
    {"org": "CHARMING KITTEN (IRAN)", "origin": "IRN"},
    {"org": "VOLT TYPHOON (CHINA)", "origin": "CHN"},
    {"org": "FANCY BEAR (RUSSIA)", "origin": "RUS"},
    {"org": "HAFNIUM (CHINA)", "origin": "CHN"},
]

# ==========================================
# 6. INITIALIZE
# ==========================================
print("\n" + "=" * 60)
print("  CITADEL v2.0 // CRITICAL INFRASTRUCTURE DEFENSE")
print("=" * 60 + "\n")

ASSETS = generate_assets(210)
NVD_CVES = fetch_nvd_cves()
ASSETS = map_cves_to_assets(ASSETS, NVD_CVES)
PATCH_TEXT, PATCH_FILE = generate_patch_report(ASSETS, NVD_CVES)

# Connect each asset to its nearest neighbor in the same region (used for network topology lines on the map)
CONNECTIONS = []
for source_index, source_asset in enumerate(ASSETS):
    closest = None
    closest_distance = float('inf')
    for target_index, target_asset in enumerate(ASSETS):
        if source_index != target_index and source_asset["region"] == target_asset["region"]:
            distance = ((source_asset["lat"] - target_asset["lat"])**2 + (source_asset["lon"] - target_asset["lon"])**2)**0.5
            if distance < closest_distance:
                closest_distance = distance
                closest = target_index
    if closest is not None and closest_distance < 3.0:
        CONNECTIONS.append((source_index, closest))

print(f"[*] NETWORK TOPOLOGY: {len(CONNECTIONS)} connections mapped")
print(f"\n[*] CITADEL v2.0 — {len(ASSETS)} ASSETS | {len(NVD_CVES)} CVEs | READY\n")

# ==========================================
# 7. DASHBOARD UI
# ==========================================
app = dash.Dash(__name__, title='CITADEL', update_title=None)

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%} <title>CITADEL</title> {%favicon%} {%css%}
        <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600&display=swap" rel="stylesheet">
        <style>
            :root { --bg-main: #0b0c10; --panel: #111418; --border: #1f2329; --text: #c9d1d9; --green: #3fb950; }
            body { background: var(--bg-main); color: var(--text); margin: 0; font-family: 'Inter', sans-serif; height: 100vh; overflow: hidden; }
            .grid-container { display: grid; grid-template-columns: 320px 1fr 320px; grid-template-rows: 70px 1fr 240px; gap: 12px; padding: 15px; height: 100vh; box-sizing: border-box; }
            .panel { background: var(--panel); border: 1px solid var(--border); border-radius: 6px; display: flex; flex-direction: column; overflow: hidden; position: relative; }
            .header { grid-column: 1 / -1; flex-direction: row; align-items: center; justify-content: space-between; padding: 0 25px; }
            .logo-title { font-family: 'JetBrains Mono'; font-weight: 700; font-size: 24px; color: #fff; letter-spacing: 2px; }
            .logo-sub { font-size: 11px; color: #8b949e; display: block; margin-top: 4px; font-family: 'Inter'; }
            .clock-box { text-align: right; }
            .clock-text { font-family: 'JetBrains Mono'; font-size: 20px; font-weight: 700; color: #fff; }
            .status-badge { font-size: 10px; color: var(--green); background: rgba(63, 185, 80, 0.1); border: 1px solid rgba(63, 185, 80, 0.3); padding: 2px 8px; border-radius: 4px; display: inline-block; margin-top: 5px; font-family: 'JetBrains Mono'; }
            .stat-box { padding: 15px 20px; border-bottom: 1px solid var(--border); }
            .stat-label { font-size: 10px; color: #8b949e; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
            .stat-val { font-family: 'JetBrains Mono'; font-size: 28px; font-weight: 700; color: #fff; }
            .log-box { padding: 10px; font-family: 'JetBrains Mono'; font-size: 11px; flex: 1; overflow-y: auto; display: flex; flex-direction: column; }
            .log-row { margin-bottom: 4px; border-bottom: 1px solid #1f2329; padding-bottom: 3px; display: flex; justify-content: space-between; }
            ::-webkit-scrollbar { width: 6px; }
            ::-webkit-scrollbar-track { background: #0d1117; }
            ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
            ::-webkit-scrollbar-thumb:hover { background: #3fb950; }
            .attack-row { display: flex; justify-content: space-between; padding: 8px 12px; border-bottom: 1px solid var(--border); font-size: 11px; font-family: 'JetBrains Mono'; }
            .map-label { position: absolute; top: 15px; left: 15px; background: rgba(13, 17, 23, 0.85); padding: 6px 12px; border: 1px solid var(--border); border-radius: 4px; font-family: 'JetBrains Mono'; font-size: 11px; color: var(--green); pointer-events: none; z-index: 10; }
            .tab-btn { background: none; border: 1px solid var(--border); color: #8b949e; padding: 4px 10px; font-family: 'JetBrains Mono'; font-size: 9px; cursor: pointer; font-weight: 700; letter-spacing: 1px; }
            .tab-btn:hover { background: #1f2329; color: #fff; }
            .tab-btn.active { background: #1f2329; color: #3fb950; border-color: #3fb950; }
        </style>
    </head>
    <body> {%app_entry%} <footer> {%config%} {%scripts%} {%renderer%} </footer> </body>
</html>
'''

total_assets = len(ASSETS)
total_cves = len(NVD_CVES)
critical_assets = len([asset for asset in ASSETS if asset["patch_priority"] == "CRITICAL"])
vulnerable_assets = len([asset for asset in ASSETS if len(asset["cves"]) > 0])

app.layout = html.Div(className="grid-container", children=[

    # HEADER
    html.Div(className="panel header", children=[
        html.Div([
            html.Div("CITADEL // CRITICAL DEFENSE", className="logo-title"),
            html.Div(f"Geospatial defense engine — {total_assets} assets | {total_cves} CVEs | NIST NVD integrated", className="logo-sub")
        ]),
        html.Div(className="clock-box", children=[
            html.Div(id='clock', className="clock-text"),
            html.Div("GRID MONITORING: ACTIVE", className="status-badge")
        ])
    ]),

    # LEFT SIDEBAR
    html.Div(className="panel", style={'gridRow': '2 / 4'}, children=[
        html.Div(className="stat-box", children=[
            html.Div("Grid Stability", className="stat-label"),
            html.Div(id="stability-text", className="stat-val", style={'color': '#3fb950', 'fontSize': '24px'}, children="99.9%"),
            html.Div(style={'width': '100%', 'height': '10px', 'backgroundColor': '#1f2329', 'marginTop': '10px', 'borderRadius': '2px', 'overflow': 'hidden'}, children=[
                html.Div(id="stability-bar", style={'width': '99.9%', 'height': '100%', 'backgroundColor': '#3fb950', 'transition': 'width 0.5s ease'})
            ])
        ]),
        html.Div(className="stat-box", children=[
            html.Div("Threats Blocked", className="stat-label"),
            html.Div(id="block-count", className="stat-val", style={'color': '#ff4d4d', 'fontSize': '24px'}, children="0")
        ]),
        html.Div(className="stat-box", children=[
            html.Div("Assets Online", className="stat-label"),
            html.Div(f"{total_assets}", className="stat-val", style={'color': '#58a6ff', 'fontSize': '24px'})
        ]),
        html.Div(className="stat-box", children=[
            html.Div("CVEs Mapped", className="stat-label"),
            html.Div(f"{total_cves}", className="stat-val", style={'color': '#ffd60a', 'fontSize': '24px'})
        ]),
        html.Div(className="stat-box", children=[
            html.Div("Critical (Patch Now)", className="stat-label"),
            html.Div(f"{critical_assets}", className="stat-val", style={'color': '#ff4d4d', 'fontSize': '24px'})
        ]),
        html.Div(className="stat-box", style={'borderBottom': 'none'}, children=[
            html.Div("Vulnerable Assets", className="stat-label"),
            html.Div(f"{vulnerable_assets}", className="stat-val", style={'color': '#f0883e', 'fontSize': '24px'})
        ]),
    ]),

    # CENTER — MAP + REPORT TABS
    html.Div(className="panel", style={'gridColumn': '2 / 3', 'gridRow': '2 / 3', 'backgroundColor': '#0d1117'}, children=[
        html.Div(style={'display': 'flex', 'gap': '8px', 'padding': '10px 15px', 'borderBottom': '1px solid #1f2329'}, children=[
            html.Button("THREAT MAP", id="tab-map", className="tab-btn active", n_clicks=1),
            html.Button("PATCH REPORT", id="tab-report", className="tab-btn", n_clicks=0),
        ]),
        html.Div(id='center-view', children=[
            dcc.Graph(id='main-map', style={'height': '100%', 'width': '100%'}, config={'displayModeBar': False})
        ], style={'flex': '1', 'position': 'relative'}),
    ]),

    # RIGHT SIDEBAR
    html.Div(className="panel", style={'gridRow': '2 / 4'}, children=[
        html.Div("LIVE THREAT FEED", style={'padding': '12px 15px', 'borderBottom': '1px solid #1f2329', 'fontWeight': 'bold', 'fontSize': '11px', 'color': '#8b949e'}),
        html.Div(id='attacker-feed', style={'flex': '1', 'overflow': 'hidden'})
    ]),

    # BOTTOM — SCADA LOG
    html.Div(className="panel", style={'gridColumn': '2 / 3', 'gridRow': '3 / 4'}, children=[
        html.Div("SCADA DIAGNOSTIC LOG", style={'padding': '8px 15px', 'borderBottom': '1px solid #1f2329', 'fontWeight': 'bold', 'fontSize': '11px', 'color': '#8b949e'}),
        html.Div(id='log-feed', className="log-box")
    ]),

    # Dash Core Components
    dcc.Interval(id='tick', interval=1200, n_intervals=0),
    dcc.Store(id='store', data={'logs': [], 'blocks': 0, 'attackers': [], 'stability': 99.9}),
    dcc.Store(id='active-center-tab', data='map'),
])


# ==========================================
# 8. Dashboard Interactivity
# ==========================================
@app.callback(
    Output('active-center-tab', 'data'),
    [Input('tab-map', 'n_clicks'), Input('tab-report', 'n_clicks')],
    prevent_initial_call=True
)
def switch_center_tab(map_clicks, report_clicks):
    context = callback_context
    if not context.triggered:
        return 'map'
    button = context.triggered[0]['prop_id'].split('.')[0]
    return 'report' if button == 'tab-report' else 'map'


@app.callback(
    [Output('center-view', 'children'),
     Output('tab-map', 'className'),
     Output('tab-report', 'className'),
     Output('log-feed', 'children'),
     Output('attacker-feed', 'children'),
     Output('clock', 'children'),
     Output('block-count', 'children'),
     Output('stability-text', 'children'),
     Output('stability-bar', 'style'),
     Output('store', 'data')],
    [Input('tick', 'n_intervals'),
     Input('active-center-tab', 'data')],
    [State('store', 'data')]
)

# Runs every 1.2 seconds — picks a random asset and simulates a possible attack
def update_simulation(tick, active_tab, data):
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S UTC")

    target = random.choice(ASSETS)
    is_threat = random.random() < SYSTEM_CONFIG['THREAT_PROBABILITY']

    # Stability
    current_stability = data.get('stability', 99.9)
    if is_threat:
        current_stability -= random.uniform(0.1, 0.5)
    else:
        current_stability += 0.1
    current_stability = max(0.0, min(100.0, current_stability))
    data['stability'] = current_stability

    stability_text = f"{current_stability:.1f}%"
    stability_color = '#3fb950' if current_stability > 95 else '#ffd60a' if current_stability > 85 else '#ff4d4d'
    stability_style = {'width': f'{current_stability}%', 'height': '100%', 'backgroundColor': stability_color, 'transition': 'width 0.5s ease'}

    # Threat feed
    if is_threat:
        data['blocks'] += 1
        threat_group = random.choice(THREAT_GROUPS)
        generated_ip = f"{random.randint(11,220)}.{random.randint(0,255)}.x.x"

        cve_text = ""
        if target["cves"]:
            cve = random.choice(target["cves"])
            cve_text = f" | {cve['cve_id']}"

        new_attack = html.Div(className="attack-row", children=[
            html.Div([
                html.Span("BLK", style={'color': '#ff4d4d', 'marginRight': '6px', 'fontWeight': 'bold'}),
                html.Span(f"{generated_ip}{cve_text}", style={'color': '#fff'})
            ]),
            html.Span(threat_group['org'], style={'color': '#ff4d4d', 'fontSize': '9px'})
        ])
        data['attackers'].insert(0, new_attack)
        if len(data['attackers']) > 15:
            data['attackers'].pop()

    # Telemetry log with real SCADA readings
    telemetry = generate_scada_telemetry()
    status = "MALWARE DETECTED" if is_threat else "NOMINAL"
    status_color = "#ff4d4d" if is_threat else "#3fb950"

    telemetry_string = f"V:{telemetry['voltage_kv']}kV F:{telemetry['frequency_hz']}Hz L:{telemetry['load_mw']}MW"

    new_log = html.Div(className="log-row", children=[
        html.Span(f"[{now.split(' ')[0]}] {target['id']} ({target['type'][:4]}) {telemetry_string}", style={'color': '#8b949e', 'fontSize': '10px'}),
        html.Span(status, style={'color': status_color, 'fontWeight': 'bold', 'fontSize': '10px'})
    ])
    data['logs'].append(new_log)
    if len(data['logs']) > 100:
        data['logs'].pop(0)

    # Tab styling
    map_class = "tab-btn active" if active_tab == 'map' else "tab-btn"
    report_class = "tab-btn active" if active_tab == 'report' else "tab-btn"

    # Center content
    if active_tab == 'report':
        center = html.Div([
            html.Pre(PATCH_TEXT, style={
                'fontSize': '10px', 'color': '#8b949e', 'fontFamily': 'JetBrains Mono, monospace',
                'background': '#0b0c10', 'padding': '20px', 'margin': '0',
                'whiteSpace': 'pre-wrap', 'lineHeight': '1.5',
                'height': '100%', 'overflowY': 'auto'
            })
        ], style={'height': '100%'})
    else:
        # Build map
        fig = go.Figure()

        # Draw lines between connected assets (only a portion to keep the map clean)
        sampled_connections = random.sample(CONNECTIONS, min(150, len(CONNECTIONS)))
        for (source_index, target_index) in sampled_connections:
            source_asset, target_asset = ASSETS[source_index], ASSETS[target_index]
            fig.add_trace(go.Scattergeo(
                lon = [source_asset['lon'], target_asset['lon']], lat=[source_asset['lat'], target_asset['lat']],
                mode = 'lines', line=dict(width=0.3, color='#21262d'),
                hoverinfo = 'none', showlegend=False,
            ))

        # Assets colored by patch priority
        priority_colors = {"CRITICAL": "#ff4d4d", "HIGH": "#ff9f0a", "MEDIUM": "#ffd60a", "LOW": "#3fb950"}
        priority_sizes = {"CRITICAL": 10, "HIGH": 7, "MEDIUM": 5, "LOW": 4}

        for priority in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            subset = [asset for asset in ASSETS if asset["patch_priority"] == priority]
            if not subset:
                continue

            # Highlight current target
            colors = []
            sizes = []
            for asset in subset:
                if asset["id"] == target["id"] and is_threat:
                    colors.append("#ffffff")
                    sizes.append(16)
                else:
                    colors.append(priority_colors[priority])
                    sizes.append(priority_sizes[priority])

            fig.add_trace(go.Scattergeo(
                lon = [asset['lon'] for asset in subset],
                lat = [asset['lat'] for asset in subset],
                mode = 'markers',
                marker = dict(size=sizes, color=colors, line=dict(width=0.5, color='#000')),
                text = [f"{asset['name']}<br>Priority: {asset['patch_priority']}<br>CVSS: {asset['cvss_max']}<br>CVEs: {len(asset['cves'])}<br>{asset['vendor']} {asset['product']}" for asset in subset],
                hoverinfo='text',
                name = priority,
                showlegend = False,
            ))

        fig.update_layout(
            geo = dict(
                scope = 'usa', projection_type='albers usa',
                showland = True, landcolor='#0d1117',
                showlakes = False, showcoastlines=True, coastlinecolor='#1f2329',
                showsubunits = True, subunitcolor='#1f2329',
                bgcolor='rgba(0,0,0,0)',
            ),
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False, dragmode=False,
        )

        center = html.Div([
            html.Div(f"ASSETS: {total_assets} | CRITICAL: {critical_assets} | CVEs: {total_cves}", className="map-label"),
            dcc.Graph(figure=fig, style={'height': '100%', 'width': '100%'}, config={'displayModeBar': False})
        ], style={'height': '100%', 'position': 'relative'})

    return center, map_class, report_class, data['logs'], data['attackers'], now, str(data['blocks']), stability_text, stability_style, data

# Auto-scroll the SCADA diagnostic log as new entries appear
app.clientside_callback(
    """function(children) { var el = document.getElementById('log-feed'); if (el) { var isAtBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 100; if (isAtBottom) el.scrollTop = el.scrollHeight; } return window.dash_clientside.no_update; }""",
    Output('log-feed', 'id'),
    Input('log-feed', 'children')
)

# Launch the dashboard
if __name__ == '__main__':
    print(f"[*] LAUNCHING DASHBOARD ON http://localhost:8096\n")
    app.run(port=8096)
