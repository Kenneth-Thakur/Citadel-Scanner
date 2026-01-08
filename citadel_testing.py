import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import random
import datetime

# ==========================================
# 1. SYSTEM CONFIGURATION
# ==========================================
SYSTEM_CONFIG = {
    "SECTOR_NAME": "CALIFORNIA (ISO-CA)",
    # Centered specifically on California
    "MAP_CENTER": {"lat": 37.2, "lon": -119.5},
    "INITIAL_BLOCKS": 0,
    "THREAT_PROBABILITY": 0.15,
    "INITIAL_STABILITY": 99.9,
    "DEFCON_LEVEL": 5
}

ASSETS = [
    {"id": "SHA", "name": "Shasta Dam Hydro", "type": "GENERATION", "lat": 40.717, "lon": -122.417},
    {"id": "SAC", "name": "Sacramento Control HQ", "type": "COMMAND", "lat": 38.581, "lon": -121.494},
    {"id": "SFO", "name": "San Francisco Substation", "type": "DISTRIBUTION", "lat": 37.774, "lon": -122.419},
    {"id": "FRE", "name": "Fresno Solar Farm", "type": "GENERATION", "lat": 36.746, "lon": -119.772},
    {"id": "DIA", "name": "Diablo Canyon Nuclear", "type": "GENERATION", "lat": 35.211, "lon": -120.855},
    {"id": "LAX", "name": "Los Angeles Metro Grid", "type": "DISTRIBUTION", "lat": 34.052, "lon": -118.243},
    {"id": "SAN", "name": "San Onofre Plant (Decom)", "type": "STORAGE", "lat": 33.369, "lon": -117.555},
    {"id": "LAS", "name": "Nevada Interconnect", "type": "EXTERNAL", "lat": 36.169, "lon": -115.139},
]

CONNECTIONS = [
    ("SHA", "SAC"), ("SAC", "SFO"), ("SAC", "FRE"),
    ("FRE", "DIA"), ("DIA", "LAX"), ("FRE", "LAS"),
    ("LAX", "SAN"), ("LAS", "LAX")
]

THREAT_GROUPS = [
    {"org": "APT-29 (RUSSIA)", "origin": "RUS"},
    {"org": "APT-1 (CHINA)", "origin": "CHN"},
    {"org": "LAZARUS (N. KOREA)", "origin": "DPRK"},
    {"org": "SANDWORM (RUSSIA)", "origin": "RUS"},
    {"org": "CHARMING KITTEN (IRAN)", "origin": "IRN"},
    {"org": "VOLT TYPHOON (CHINA)", "origin": "CHN"}
]

# ==========================================
# 2. UI LAYOUT
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

            .stat-box { padding: 20px; border-bottom: 1px solid var(--border); }
            .stat-label { font-size: 11px; color: #8b949e; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
            .stat-val { font-family: 'JetBrains Mono'; font-size: 36px; font-weight: 700; color: #fff; }
            
            /* SCROLLABLE LOG BOX */
            .log-box { 
                padding: 10px; 
                font-family: 'JetBrains Mono'; 
                font-size: 11px; 
                flex: 1; 
                overflow-y: auto;
                display: flex; 
                flex-direction: column;
                justify-content: flex-start;
            }
            .log-row { margin-bottom: 6px; border-bottom: 1px solid #1f2329; padding-bottom: 3px; display: flex; justify-content: space-between; }
            
            /* CUSTOM SCROLLBAR */
            ::-webkit-scrollbar { width: 6px; }
            ::-webkit-scrollbar-track { background: #0d1117; }
            ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
            ::-webkit-scrollbar-thumb:hover { background: #3fb950; }

            .attack-row { display: flex; justify-content: space-between; padding: 10px 15px; border-bottom: 1px solid var(--border); font-size: 12px; font-family: 'JetBrains Mono'; }
            .origin-flag { color: #ff4d4d; margin-left: 5px; font-size: 10px; font-weight: bold; }
            .map-label { position: absolute; top: 15px; left: 15px; background: rgba(13, 17, 23, 0.85); padding: 6px 12px; border: 1px solid var(--border); border-radius: 4px; font-family: 'JetBrains Mono'; font-size: 11px; color: var(--green); pointer-events: none; z-index: 10; }
        </style>
    </head>
    <body> {%app_entry%} <footer> {%config%} {%scripts%} {%renderer%} </footer> </body>
</html>
'''

app.layout = html.Div(className="grid-container", children=[
    
    # --- HEADER ---
    html.Div(className="panel header", children=[
        html.Div([
            html.Div("CITADEL // CRITICAL DEFENSE", className="logo-title"),
            html.Div("Geospatial defense engine securing critical energy infrastructure.", className="logo-sub")
        ]),
        html.Div(className="clock-box", children=[
            html.Div(id='clock', className="clock-text"),
            html.Div("GRID MONITORING: ACTIVE", className="status-badge")
        ])
    ]),

    # --- LEFT SIDEBAR ---
    html.Div(className="panel", style={'gridRow': '2 / 4'}, children=[
        html.Div(className="stat-box", children=[
            html.Div("Grid Stability", className="stat-label"),
            html.Div(id="stability-text", className="stat-val", style={'color': '#3fb950'}, children=f"{SYSTEM_CONFIG['INITIAL_STABILITY']}%"),
            html.Div(style={'width': '100%', 'height': '12px', 'backgroundColor': '#1f2329', 'marginTop': '15px', 'borderRadius': '2px', 'overflow': 'hidden'}, children=[
                html.Div(id="stability-bar", style={'width': '99.9%', 'height': '100%', 'backgroundColor': '#3fb950', 'transition': 'width 0.5s ease'})
            ])
        ]),
        html.Div(className="stat-box", children=[
            html.Div("Threats Neutralized", className="stat-label"),
            html.Div(id="block-count", className="stat-val", style={'color': '#ff4d4d'}, children=str(SYSTEM_CONFIG['INITIAL_BLOCKS']))
        ]),
        html.Div(className="stat-box", style={'borderBottom': 'none'}, children=[
            html.Div("Alert Level", className="stat-label"),
            html.Div(f"DEFCON {SYSTEM_CONFIG['DEFCON_LEVEL']}", className="stat-val", style={'color': '#58a6ff', 'fontSize': '28px'}),
            html.Div("Standard Readiness", style={'fontSize': '12px', 'color': '#8b949e', 'marginTop': '5px'})
        ]),
    ]),

    # --- CENTER MAP ---
    html.Div(className="panel", style={'gridColumn': '2 / 3', 'gridRow': '2 / 3', 'backgroundColor': '#0d1117'}, children=[
        html.Div(f"SECTOR: {SYSTEM_CONFIG['SECTOR_NAME']}", className="map-label"),
        dcc.Graph(id='california-map', style={'height': '100%', 'width': '100%'}, config={'displayModeBar': False})
    ]),

    # --- RIGHT SIDEBAR (FEED) ---
    html.Div(className="panel", style={'gridRow': '2 / 4'}, children=[
        html.Div("LIVE FEED (LAST 10)", style={'padding': '15px', 'borderBottom': '1px solid #1f2329', 'fontWeight': 'bold', 'fontSize': '11px', 'color': '#8b949e'}),
        html.Div(id='attacker-feed', style={'flex': '1', 'overflow': 'hidden'})
    ]),

    # --- BOTTOM (LOGS) ---
    html.Div(className="panel", style={'gridColumn': '2 / 3', 'gridRow': '3 / 4'}, children=[
        html.Div("SCADA DIAGNOSTIC LOG", style={'padding': '10px 15px', 'borderBottom': '1px solid #1f2329', 'fontWeight': 'bold', 'fontSize': '11px', 'color': '#8b949e'}),
        html.Div(id='log-feed', className="log-box")
    ]),

    dcc.Interval(id='tick', interval=1200, n_intervals=0),
    dcc.Store(id='store', data={'logs': [], 'blocks': SYSTEM_CONFIG['INITIAL_BLOCKS'], 'attackers': [], 'stability': SYSTEM_CONFIG['INITIAL_STABILITY']})
])

# ==========================================
# 3. CALLBACKS
# ==========================================
@app.callback(
    [Output('california-map', 'figure'),
     Output('log-feed', 'children'),
     Output('attacker-feed', 'children'),
     Output('clock', 'children'),
     Output('block-count', 'children'),
     Output('stability-text', 'children'),
     Output('stability-bar', 'style'),
     Output('store', 'data')],
    [Input('tick', 'n_intervals')],
    [State('store', 'data')]
)
def update_simulation(n, data):
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S UTC")
    
    target = random.choice(ASSETS)
    is_threat = random.random() > (1.0 - SYSTEM_CONFIG['THREAT_PROBABILITY'])
    
    # --- STABILITY LOGIC ---
    current_stability = data.get('stability', 99.9)
    if is_threat:
        current_stability -= random.uniform(0.1, 0.5)
    else:
        current_stability += 0.1
    
    current_stability = max(0.0, min(100.0, current_stability))
    data['stability'] = current_stability
    
    stab_text = f"{current_stability:.1f}%"
    stab_style = {'width': f'{current_stability}%', 'height': '100%', 'backgroundColor': '#3fb950', 'transition': 'width 0.5s ease'}

    # MAP DATA
    lats, lons = [], []
    for (start, end) in CONNECTIONS:
        s = next(a for a in ASSETS if a['id'] == start)
        e = next(a for a in ASSETS if a['id'] == end)
        lats.extend([s['lat'], e['lat'], None])
        lons.extend([s['lon'], e['lon'], None])

    node_lats = [a['lat'] for a in ASSETS]
    node_lons = [a['lon'] for a in ASSETS]
    node_text = [a['name'] for a in ASSETS]
    node_cols = ['#3fb950' for _ in ASSETS]
    node_sizes = [12 for _ in ASSETS]
    
    target_idx = ASSETS.index(target)
    
    if is_threat:
        node_cols[target_idx] = '#ff4d4d' 
        node_sizes[target_idx] = 25
        data['blocks'] += 1
        
        threat_group = random.choice(THREAT_GROUPS)
        generated_ip = f"{random.randint(11,220)}.{random.randint(0,255)}.x.x"

        new_attack = html.Div(className="attack-row", children=[
            html.Div([
                html.Span("BLK", style={'color': '#ff4d4d', 'marginRight': '8px', 'fontWeight': 'bold'}), 
                html.Span(generated_ip, style={'fontFamily': 'JetBrains Mono', 'color': '#fff'})
            ]),
            html.Span(threat_group['org'], className="origin-flag", style={'color': '#ff4d4d'})
        ])
        data['attackers'].insert(0, new_attack)
        if len(data['attackers']) > 9: data['attackers'].pop()
    else:
        node_cols[target_idx] = '#ffffff'
        node_sizes[target_idx] = 18

    fig_map = go.Figure()

    # 1. CALIFORNIA SILHOUETTE
    fig_map.add_trace(go.Choropleth(
        locations=['CA'],
        z=[1],
        locationmode='USA-states',
        colorscale=[[0, '#1c2128'], [1, '#1c2128']], # Lighter charcoal fill
        showscale=False,
        marker_line_color='#484f58', # Defined, bold grey border
        marker_line_width=2,         # Thicker line for "Bold" look
        hoverinfo='skip'
    ))

    # 2. LAYER: CONNECTIONS
    fig_map.add_trace(go.Scattergeo(
        lon=lons, lat=lats, 
        mode='lines', 
        line=dict(width=1, color='#30363d'), 
        hoverinfo='none'
    ))

    # 3. LAYER: ASSETS
    fig_map.add_trace(go.Scattergeo(
        lon=node_lons, lat=node_lats, 
        mode='markers+text', 
        marker=dict(size=node_sizes, color=node_cols, line=dict(width=1, color='#000')), 
        text=node_text, 
        textposition="top center", 
        textfont=dict(family="JetBrains Mono", size=10, color="#c9d1d9"), 
        hoverinfo='none'
    ))

    # LAYOUT: "Empty" the rest of the map
    fig_map.update_layout(
        geo=dict(
            scope='usa', 
            projection_type='albers usa', 
            showland=False,         # Hides all other states (America is empty)
            showsubunits=False,     # Hides borders of invisible states
            showcoastlines=False,   # Hides coastlines
            bgcolor='rgba(0,0,0,0)', 
            center=SYSTEM_CONFIG['MAP_CENTER'], 
            # Very tight zoom to cut off empty space on right
            lataxis=dict(range=[32.0, 42.5]), 
            lonaxis=dict(range=[-125.5, -114.0]) 
        ),
        margin=dict(l=0, r=0, t=0, b=0), 
        paper_bgcolor='rgba(0,0,0,0)', 
        showlegend=False,
        dragmode=False
    )
    
    # LOGS
    status = "MALWARE SIGNATURE DETECTED" if is_threat else "OPERATIONAL"
    c_style = "#ff4d4d" if is_threat else "#3fb950"
    
    new_log = html.Div(className="log-row", children=[
        html.Span(f"[{now.split(' ')[0]}] Checking {target['id']} ({target['type']})...", style={'color': '#8b949e'}),
        html.Span(status, style={'color': c_style, 'fontWeight': 'bold'})
    ])
    
    data['logs'].append(new_log)
    if len(data['logs']) > 100: data['logs'].pop(0)

    return fig_map, data['logs'], data['attackers'], now, str(data['blocks']), stab_text, stab_style, data

# 4. SMART SCROLL
app.clientside_callback(
    """
    function(children) {
        var el = document.getElementById('log-feed');
        if (el) {
            var isAtBottom = (el.scrollHeight - el.scrollTop - el.clientHeight) < 100;
            if (isAtBottom) {
                el.scrollTop = el.scrollHeight;
            }
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('log-feed', 'id'),
    Input('log-feed', 'children')
)

if __name__ == '__main__':
    app.run(port=8096)
