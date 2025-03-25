"""
Dashboard layout module for Indonesian Adventure.
"""

from typing import List, Dict, Any
from dash import dcc, html
from dash.dash_table import DataTable

from config.dashboard_config import (
    CHECKS_PER_DAY_MIN, CHECKS_PER_DAY_MAX, CHECKS_PER_DAY_DEFAULT,
    COOLDOWN_MULTIPLIER_MIN, COOLDOWN_MULTIPLIER_MAX, COOLDOWN_MULTIPLIER_STEP, COOLDOWN_MULTIPLIER_DEFAULT,
    DEFAULT_BASE_GOLD_PER_SEC, DEFAULT_EARN_COEFFICIENT,
    DEFAULT_STARTING_GOLD, DEFAULT_STARTING_XP, DEFAULT_STARTING_KEYS,
    STYLE_SECTION, STYLE_CONTAINER, STYLE_SIDEBAR, STYLE_MAIN_CONTENT, 
    STYLE_HEADER, STYLE_BUTTON,
    BASE_GOLD, STARTING_GOLD, STARTING_XP, STARTING_KEYS, EARN_COEFFICIENT, LOCATION_COUNT,
    DEFAULT_GAME_DURATION, DEFAULT_CHECK_SCHEDULE,
    DEFAULT_MAX_ENERGY, DEFAULT_TAP_SPEED, DEFAULT_TAP_COEF, DEFAULT_IS_TAPPING,
    TAPPING_COLORS, TAPPING_GRAPH_LAYOUT, LEVEL_PROGRESS_COLORS, DEFAULT_FIGURE_LAYOUT
)
from models.config import SimulationAlgorithm
from simulator import Simulator

def create_settings_panel():
    """
    Создает панель настроек симуляции.
    
    Returns:
        html.Div: Панель настроек
    """
    return html.Div([
        html.Div([
            html.H3("Simulation Settings", style={"color": "#ffffff", "marginBottom": "20px"}),
        ], style=STYLE_HEADER),
        
        # Economic parameters
        html.Div([
            html.H4("Economy Parameters", className="settings-section-title"),
            
            html.Div([
                html.Label("Base gold per second:", style={"display": "block", "marginBottom": "5px"}),
                dcc.Input(
                    id="base-gold-per-sec-input",
                    type="number",
                    value=DEFAULT_BASE_GOLD_PER_SEC,
                    step=0.01,
                    style={"width": "100%", "marginBottom": "15px", "padding": "8px"}
                ),
            ]),
            
            html.Div([
                html.Label("Gold growth coefficient:", style={"display": "block", "marginBottom": "5px"}),
                dcc.Input(
                    id="earn-coefficient-input",
                    type="number",
                    value=DEFAULT_EARN_COEFFICIENT,
                    step=0.001,
                    style={"width": "100%", "marginBottom": "15px", "padding": "8px", "border": "1px solid #ddd", "outline": "none"}
                ),
            ]),
        ], className="settings-section"),
        
        html.Hr(style={"margin": "20px 0", "opacity": "0.3"}),
        
        # Starting balance
        html.Div([
            html.H4("Starting Balance", className="settings-section-title"),
            
            html.Div([
                html.Label("Initial gold amount:", style={"display": "block", "marginBottom": "5px"}),
                dcc.Input(
                    id="starting-gold-input",
                    type="number",
                    value=DEFAULT_STARTING_GOLD,
                    step=100,
                    min=0,
                    style={"width": "100%", "marginBottom": "15px", "padding": "8px"}
                ),
            ]),
            
            html.Div([
                html.Label("Initial experience:", style={"display": "block", "marginBottom": "5px"}),
                dcc.Input(
                    id="starting-xp-input",
                    type="number",
                    value=DEFAULT_STARTING_XP,
                    step=1,
                    min=0,
                    style={"width": "100%", "marginBottom": "15px", "padding": "8px"}
                ),
            ]),
            
            html.Div([
                html.Label("Initial keys:", style={"display": "block", "marginBottom": "5px"}),
                dcc.Input(
                    id="starting-keys-input",
                    type="number",
                    value=DEFAULT_STARTING_KEYS,
                    step=1,
                    min=0,
                    style={"width": "100%", "marginBottom": "15px", "padding": "8px"}
                ),
            ]),
        ], className="settings-section"),
        
        html.Hr(style={"margin": "20px 0", "opacity": "0.3"}),
        
        # Check parameters
        html.Div([
            html.H4("Check Parameters", className="settings-section-title"),
            
            html.Div([
                html.Label("Check schedule:", style={"display": "block", "marginBottom": "10px", "fontWeight": "bold"}),
                
                # Container for dynamic time list
                html.Div(id="check-times-container", style={"marginBottom": "15px"}),
                
                # Button to add new time
                html.Button(
                    "+", 
                    id="add-check-time-button",
                    n_clicks=0,
                    style={
                        "backgroundColor": "#4CAF50",
                        "color": "white",
                        "border": "none",
                        "borderRadius": "4px",
                        "width": "30px",
                        "height": "30px",
                        "fontSize": "18px",
                        "cursor": "pointer",
                        "marginBottom": "15px"
                    }
                ),
                
                # Store for check times
                dcc.Store(id="check-times-store", data={"schedule": ["08:00", "12:00", "16:00", "20:00"]}),
                
                # Game session duration
                html.Div([
                    html.Label("Session duration in minutes:", style={"display": "block", "marginBottom": "5px", "fontWeight": "bold"}),
                    dcc.Input(
                        id="game-duration-input",
                        type="number",
                        value=15,  # Default value: 15 minutes
                        min=1,
                        max=60,
                        step=1,
                        style={"width": "100%", "padding": "8px", "borderRadius": "4px", "border": "1px solid #ddd"}
                    ),
                ], style={"marginTop": "20px"}),
            ], style={"marginBottom": "20px"}),
        ], className="settings-section"),
        
        html.Hr(style={"margin": "20px 0", "opacity": "0.3"}),
        
        # Location parameters
        html.Div([
            html.H4("Location Parameters", className="settings-section-title"),
            
            html.Div([
                html.Label("Cooldown multiplier between upgrades:", style={"display": "block", "marginBottom": "10px"}),
                dcc.Slider(
                    id="cooldown-multiplier-slider",
                    min=COOLDOWN_MULTIPLIER_MIN,
                    max=COOLDOWN_MULTIPLIER_MAX,
                    step=COOLDOWN_MULTIPLIER_STEP,
                    value=COOLDOWN_MULTIPLIER_DEFAULT,
                    marks={i/10: str(i/10) for i in range(int(COOLDOWN_MULTIPLIER_MIN*10), int(COOLDOWN_MULTIPLIER_MAX*10) + 1, 5)},
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
            ], style={"marginBottom": "20px"}),
            
            # Simulation algorithm
            html.Div([
                html.Label("Location upgrade algorithm:", style={"display": "block", "marginBottom": "10px"}),
                dcc.RadioItems(
                    id="simulation-algorithm-radio",
                    options=[
                        {'label': ' Sequential upgrade', 'value': SimulationAlgorithm.SEQUENTIAL.value},
                        {'label': ' First available upgrade', 'value': SimulationAlgorithm.FIRST_AVAILABLE.value},
                    ],
                    value=SimulationAlgorithm.SEQUENTIAL.value,
                    style={"marginBottom": "15px"},
                    inputStyle={"marginRight": "5px"},
                    labelStyle={"display": "block", "marginBottom": "10px"}
                ),
                html.Div([
                    html.P("Sequential upgrade: locations are upgraded in order, requiring full upgrade of previous locations.", 
                           className="description-text", style={"fontSize": "12px", "color": "#666"}),
                    html.P("First available upgrade: upgrades the first available location with expired cooldown.",
                           className="description-text", style={"fontSize": "12px", "color": "#666"}),
                ], style={"marginTop": "5px"})
            ], style={"marginBottom": "20px"}),
        ], className="settings-section"),
        
        html.Hr(style={"margin": "20px 0", "opacity": "0.3"}),
        
        # Tapping parameters
        html.Div([
            html.H4("Tapping Parameters", className="settings-section-title"),
            
            # Enable/disable tapping
            html.Div([
                html.Label(
                    html.Div([
                        dcc.Checklist(
                            id="is-tapping-checkbox",
                            options=[{'label': ' Enable tapping', 'value': 'is_tapping'}],
                            value=['is_tapping'] if DEFAULT_IS_TAPPING else [],
                            inputStyle={"marginRight": "5px"},
                            style={"fontWeight": "bold"}
                        ),
                        html.P(
                            "When enabled, the user will tap during game sessions, spending energy and receiving gold.",
                            style={"fontSize": "12px", "color": "#666", "marginTop": "5px", "marginLeft": "25px"}
                        )
                    ]),
                    style={"display": "block", "marginBottom": "15px"}
                ),
            ]),
            
            # Maximum energy
            html.Div([
                html.Label("Maximum energy:", style={"display": "block", "marginBottom": "5px"}),
                dcc.Input(
                    id="max-energy-input",
                    type="number",
                    value=DEFAULT_MAX_ENERGY,
                    step=50,
                    min=100,
                    max=2000,
                    style={"width": "100%", "marginBottom": "15px", "padding": "8px"}
                ),
            ]),
            
            # Tapping speed
            html.Div([
                html.Label("Tapping speed (taps per second):", style={"display": "block", "marginBottom": "5px"}),
                dcc.Input(
                    id="tap-speed-input",
                    type="number",
                    value=DEFAULT_TAP_SPEED,
                    step=0.5,
                    min=0.5,
                    max=10,
                    style={"width": "100%", "marginBottom": "15px", "padding": "8px"}
                ),
            ]),
            
            # Gold per tap
            html.Div([
                html.Label("Tap coefficient:", style={"display": "block", "marginBottom": "5px"}),
                dcc.Input(
                    id="gold-per-tap-input",
                    type="number",
                    value=DEFAULT_TAP_COEF,
                    step=0.1,
                    min=0.1,
                    max=10000,
                    style={"width": "100%", "marginBottom": "15px", "padding": "8px"}
                ),
                html.P(
                    "Multiplier for tap gold (user level * coefficient = gold per tap)",
                    style={"fontSize": "12px", "color": "#666", "marginTop": "5px"}
                ),
            ]),
            
            # Mechanics description
            html.Div([
                html.P(
                    "Energy is spent at 1 unit per tap and regenerates at 1 unit per second.",
                    style={"fontSize": "12px", "color": "#666", "marginTop": "5px"}
                ),
                html.P(
                    "If energy = 0, user stops tapping for the current session.",
                    style={"fontSize": "12px", "color": "#666", "marginTop": "5px"}
                ),
            ], style={"backgroundColor": "#f8f9fa", "padding": "10px", "borderRadius": "5px"}),
            
        ], className="settings-section"),
        
        html.Button(
            "Run Simulation", 
            id="run-simulation-button", 
            n_clicks=0,
            style=STYLE_BUTTON
        ),
        
        html.Div(id="simulation-status", style={"marginTop": "15px", "padding": "10px", "backgroundColor": "#e9ecef", "borderRadius": "5px"}),
    ], style=STYLE_SIDEBAR)

def create_overview_tab():
    """
    Creates overview tab.
    
    Returns:
        html.Div: Tab content
    """
    return html.Div([
        html.Div([
            html.H4("Key Indicators", className="tab-section-title"),
            html.Div([
                html.Div(id="completion-time", className="info-card"),
                html.Div(id="final-resources", className="info-card"),
            ], style={"display": "flex", "gap": "20px", "marginBottom": "20px"}),
        ], className="tab-section"),
        
        html.Div([
            html.H4("Key Metrics", className="tab-section-title"),
            html.Div(id="key-metrics"),
        ], className="tab-section"),
    ])

def create_progress_tab():
    """
    Creates character progress tab.
    
    Returns:
        html.Div: Tab content
    """
    return html.Div([
        html.Div([
            html.H4("Character Level Growth", className="tab-section-title"),
            dcc.Graph(id="user-level-progress"),
        ], className="tab-section"),
        
        html.Div([
            html.H4("Resource Accumulation", className="tab-section-title"),
            dcc.Graph(id="resources-over-time"),
        ], className="tab-section"),
    ])

def create_locations_tab():
    """
    Creates locations analysis tab.
    
    Returns:
        html.Div: Tab container with content
    """
    return html.Div([
        # Location costs table
        html.Div([
            html.H4("Location Costs", className="tab-section-title"),
            html.Div([
                DataTable(
                    id="locations-cost-table",
                    style_header={
                        'backgroundColor': '#f8f9fa',
                        'fontWeight': 'bold',
                        'border': '1px solid #ddd'
                    },
                    style_cell={
                        'padding': '8px 15px',
                        'textAlign': 'center',
                        'backgroundColor': 'white',
                        'border': '1px solid #ddd',
                        'minWidth': '70px',
                        'maxWidth': '100px',
                        'whiteSpace': 'normal'
                    },
                    style_table={
                        'overflowX': 'auto',
                        'maxHeight': '400px',
                        'overflowY': 'auto'
                    },
                    fixed_rows={'headers': True},
                    tooltip_delay=0,
                    tooltip_duration=None
                ),
                # Rarity color legend
                html.Div([
                    html.Div([
                        html.Span("Location rarity:", style={"marginRight": "10px", "fontWeight": "bold"}),
                        html.Span([
                            html.Span("", style={
                                "display": "inline-block", 
                                "width": "12px", 
                                "height": "12px", 
                                "backgroundColor": "#f0f8ff", 
                                "marginRight": "5px",
                                "border": "1px solid #ddd"
                            }),
                            "Common",
                        ], style={"marginRight": "10px"}),
                        html.Span([
                            html.Span("", style={
                                "display": "inline-block", 
                                "width": "12px", 
                                "height": "12px", 
                                "backgroundColor": "#f5f0ff", 
                                "marginRight": "5px",
                                "border": "1px solid #ddd"
                            }),
                            "Rare",
                        ], style={"marginRight": "10px"}),
                        html.Span([
                            html.Span("", style={
                                "display": "inline-block", 
                                "width": "12px", 
                                "height": "12px", 
                                "backgroundColor": "#fffbeb", 
                                "marginRight": "5px",
                                "border": "1px solid #ddd"
                            }),
                            "Legendary",
                        ]),
                    ], style={"display": "flex", "alignItems": "center", "fontSize": "12px", "color": "#666"})
                ], style={"marginTop": "10px", "textAlign": "right"})
            ], style={"marginBottom": "30px"}),
        ], className="tab-section"),
        
        # Location progress graph
        html.Div([
            html.H4("Location Progress", className="tab-section-title"),
            dcc.Graph(id="locations-upgrades"),
        ], className="tab-section"),
        
        # Location upgrade history table
        html.Div([
            html.H4("Location Upgrade History", className="tab-section-title"),
            DataTable(
                id="location-history-table",
                style_header={
                    'backgroundColor': '#f8f9fa',
                    'fontWeight': 'bold',
                    'border': '1px solid #ddd'
                },
                style_cell={
                    'padding': '8px 15px',
                    'textAlign': 'center',
                    'backgroundColor': 'white',
                    'border': '1px solid #ddd',
                    'minWidth': '100px',
                    'maxWidth': '180px',
                    'whiteSpace': 'normal'
                },
                style_table={
                    'overflowX': 'auto'
                }
            ),
        ], className="tab-section"),
    ])

def create_economy_tab():
    """
    Creates economy analysis tab.
    
    Returns:
        html.Div: Tab container with content
    """
    return html.Div([
        # 1. Base economy
        html.Div([
            html.H4("Base Economy", className="tab-section-title"),
            dcc.Graph(id="gold-per-sec-progression"),
            DataTable(
                id="gold-per-sec-table",
                columns=[
                    {"name": "Level", "id": "level"},
                    {"name": "Gold/sec", "id": "gold_per_sec"},
                    {"name": "Gold/hour", "id": "gold_per_hour"},
                    {"name": "Gold/day", "id": "gold_per_day"},
                    {"name": "Growth", "id": "growth"},
                ],
                style_table={"overflowX": "auto", "borderRadius": "5px", "boxShadow": "0 2px 4px rgba(0,0,0,0.05)"},
                style_header={
                    'backgroundColor': '#f8f9fa',
                    'fontWeight': 'bold',
                    'border': '1px solid #ddd'
                },
                style_cell={
                    'padding': '8px 15px',
                    'textAlign': 'center',
                    'backgroundColor': 'white',
                    'border': '1px solid #ddd'
                },
            ),
        ], className="tab-section"),
        
        # 2. Economy dynamics
        html.Div([
            html.H4("Economy Dynamics", className="tab-section-title"),
            dcc.Graph(id="economy-analysis"),
            html.Div([
                html.H5("Key Indicators", className="subsection-title"),
                html.Div(id="economy-metrics", className="metrics-container"),
            ]),
        ], className="tab-section"),
        
        # 3. Gold balance
        html.Div([
            html.H4("Gold Balance", className="tab-section-title"),
            DataTable(
                id="upgrades-history-table",
                style_header={
                    'backgroundColor': '#f8f9fa',
                    'fontWeight': 'bold',
                    'border': '1px solid #ddd'
                },
                style_cell={
                    'padding': '8px 15px',
                    'textAlign': 'center',
                    'backgroundColor': 'white',
                    'border': '1px solid #ddd'
                }
            ),
        ], className="tab-section"),
    ])

def create_pace_tab():
    """
    Creates game pace analysis tab.
    
    Returns:
        html.Div: Tab content
    """
    return html.Div([
        html.Div([
            html.H4("Time Between Upgrades Analysis", className="tab-section-title"),
            dcc.Graph(id="progression-pace"),
        ], className="tab-section"),
        
        html.Div([
            html.H4("No Upgrade Periods Analysis", className="tab-section-title"),
            dcc.Graph(id="stagnation-analysis"),
        ], className="tab-section"),
        
        html.Div([
            html.H4("Progress Statistics", className="tab-section-title"),
            html.Div(id="progression-stats", className="stats-container"),
        ], className="tab-section"),
        
        html.Div([
            html.H4("Daily Events", className="tab-section-title"),
            DataTable(
                id="daily-events-table",
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'center',
                    'padding': '10px',
                    'minWidth': '80px',
                    'maxWidth': '180px',
                    'whiteSpace': 'normal',
                },
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    }
                ],
                page_size=10,
                sort_action='native',
            ),
        ], className="tab-section"),
    ])

def create_tapping_tab():
    """
    Creates tapping analysis tab.
    
    Returns:
        html.Div: Tab container with content
    """
    return html.Div([
        # 1. "Taps and Gold by Day" graph
        html.Div([
            html.H4("Taps and Gold by Day", className="tab-section-title"),
            dcc.Graph(id="taps-gold-by-day-graph"),
            html.Div([
                html.H5("Summary Statistics", className="subsection-title", style={"marginTop": "15px"}),
                html.Div([
                    html.Div([
                        html.P("Total taps:", style={"fontWeight": "bold", "margin": "0"}),
                        html.P(id="total-taps", className="metric-value")
                    ], className="metric-box"),
                    html.Div([
                        html.P("Total gold from taps:", style={"fontWeight": "bold", "margin": "0"}),
                        html.P(id="total-gold-from-taps", className="metric-value")
                    ], className="metric-box"),
                    html.Div([
                        html.P("Average taps per session:", style={"fontWeight": "bold", "margin": "0"}),
                        html.P(id="avg-taps-per-session", className="metric-value")
                    ], className="metric-box"),
                ], style={"display": "flex", "flexWrap": "wrap", "gap": "15px", "marginTop": "10px", "justifyContent": "space-between"})
            ]),
        ], className="tab-section"),
        
        # 2. "Energy Over Time" graph (within one session)
        html.Div([
            html.H4("Energy Over Time (within session)", className="tab-section-title"),
            dcc.Dropdown(
                id="session-select-dropdown",
                placeholder="Select session for analysis",
                style={"marginBottom": "15px"}
            ),
            dcc.Graph(id="energy-over-time-graph"),
        ], className="tab-section"),
        
        # 3. Daily statistics table
        html.Div([
            html.H4("Daily Tapping Statistics", className="tab-section-title"),
            DataTable(
                id="tapping-stats-table",
                columns=[
                    {"name": "Day", "id": "day"},
                    {"name": "Taps count", "id": "taps"},
                    {"name": "Energy spent", "id": "energy"},
                    {"name": "Gold received", "id": "gold"},
                    {"name": "User level", "id": "level"},
                    {"name": "Gold per tap", "id": "gold_per_tap"}
                ],
                style_header={
                    'backgroundColor': '#f8f9fa',
                    'fontWeight': 'bold',
                    'border': '1px solid #ddd'
                },
                style_cell={
                    'padding': '8px 15px',
                    'textAlign': 'center',
                    'backgroundColor': 'white',
                    'border': '1px solid #ddd'
                },
                style_table={
                    'overflowX': 'auto'
                }
            ),
        ], className="tab-section"),
    ])

def create_tabs():
    """
    Creates tabs for displaying simulation results.
    
    Returns:
        dcc.Tabs: Tabs component
    """
    return dcc.Tabs([
        dcc.Tab(label="Overview", children=create_overview_tab(), className="custom-tab", selected_className="custom-tab--selected"),
        dcc.Tab(label="Progress", children=create_progress_tab(), className="custom-tab", selected_className="custom-tab--selected"),
        dcc.Tab(label="Locations", children=create_locations_tab(), className="custom-tab", selected_className="custom-tab--selected"),
        dcc.Tab(label="Economy", children=create_economy_tab(), className="custom-tab", selected_className="custom-tab--selected"),
        dcc.Tab(label="Pace", children=create_pace_tab(), className="custom-tab", selected_className="custom-tab--selected"),
        dcc.Tab(label="Tapping", children=create_tapping_tab(), className="custom-tab", selected_className="custom-tab--selected"),
    ], className="custom-tabs")

def create_layout(title):
    """
    Creates main dashboard layout.
    
    Args:
        title: Dashboard title
        
    Returns:
        html.Div: Dashboard layout
    """
    return html.Div([
        # Add styles through external_stylesheets
        html.Link(
            rel='stylesheet',
            href='/assets/style.css'
        ),
        
        # Title
        html.Div([
            html.H1(title, style={"margin": "0", "color": "white"})
        ], style={"backgroundColor": "#343a40", "padding": "15px 20px", "boxShadow": "0 2px 5px rgba(0,0,0,0.2)"}),
        
        # Main container (sidebar + content)
        html.Div([
            # Settings panel (left)
            create_settings_panel(),
            
            # Main content (right)
            html.Div([
                create_tabs(),
            ], style=STYLE_MAIN_CONTENT),
        ], style=STYLE_CONTAINER),
        
        # Data stores
        dcc.Store(id="simulation-data-store"),
        dcc.Store(id="user-levels-store"),
        # Add flag indicating simulation hasn't been run
        dcc.Store(id="auto-run-store", data={"auto_run": False}),
        # Store for tapping data
        dcc.Store(id="tapping-stats-store")
    ]) 