import dash
from dash import html, dcc
import plotly.graph_objects as go
from dash.dependencies import Input, Output
import requests
from google.transit import gtfs_realtime_pb2
from datetime import datetime
import pytz
import time
import json

# Initialize the Dash app
app = dash.Dash(__name__, title="Finland Train Tracker")
server = app.server

# Define the GTFS-RT API endpoint
LOCATIONS_URL = 'https://rata.digitraffic.fi/api/v1/trains/gtfs-rt-locations'

# Define map center (Finland)
FINLAND_CENTER = {"lat": 62.2426, "lon": 25.7473}

# Set the refresh interval in seconds
REFRESH_INTERVAL = 30

# Create a persistent session for requests with the exact headers known to work
session = requests.Session()
session.headers.update({
    'Accept': 'application/x-protobuf',
    'User-Agent': 'TrainTrackerTest/1.0',
    'Digitraffic-User': 'TrainTrackerTest'
})

# Track last successful request time to manage request frequency
last_request_time = 0
MIN_REQUEST_INTERVAL = 5  # Minimum seconds between requests

# Function to format timestamps properly
def format_timestamp(timestamp_str):
    if not timestamp_str or timestamp_str == "Unknown":
        return "Unknown"
    
    try:
        # Parse the timestamp with timezone information
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        
        # Convert to Finland time (EET/EEST)
        finland_tz = pytz.timezone('Europe/Helsinki')
        timestamp = timestamp.astimezone(finland_tz)
        
        # Format as HH:MM
        return timestamp.strftime('%H:%M')
    except Exception as e:
        return timestamp_str

# Function to fetch and process GTFS-RT data
def fetch_train_locations():
    global last_request_time
    
    try:
        # Enforce minimum time between requests to avoid rate limiting
        current_time = time.time()
        time_since_last_request = current_time - last_request_time
        
        if time_since_last_request < MIN_REQUEST_INTERVAL and last_request_time > 0:
            wait_time = MIN_REQUEST_INTERVAL - time_since_last_request
            print(f"Rate limit: waiting {wait_time:.2f} seconds...")
            time.sleep(wait_time)
        
        # Simple and clear request with the working headers (set in the session)
        print(f"Fetching train data...")
        response = session.get(LOCATIONS_URL, timeout=20)
        
        # Check status code explicitly
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code}")
            return [], datetime.now().strftime('%H:%M:%S') + f" (Error: {response.status_code})"
            
        # Update the time of our last successful request
        last_request_time = time.time()
        
        # Parse the protobuf message
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)
        
        # Extract train data
        train_data = []
        for entity in feed.entity:
            if entity.HasField('vehicle'):
                vehicle = entity.vehicle
                
                # Get basic information
                train_id = vehicle.vehicle.id if vehicle.vehicle.HasField('id') else "Unknown"
                
                # Get position information
                if vehicle.HasField('position'):
                    lat = vehicle.position.latitude
                    lon = vehicle.position.longitude
                    
                    # Speed might not be available for all trains
                    if vehicle.position.HasField('speed'):
                        speed_kmh = vehicle.position.speed * 3.6  # Convert m/s to km/h
                    else:
                        speed_kmh = None
                else:
                    continue  # Skip if no position data
                
                # Get timestamp
                if vehicle.HasField('timestamp'):
                    timestamp = datetime.fromtimestamp(vehicle.timestamp)
                else:
                    timestamp = None
                
                # Get trip info
                trip_id = None
                route_id = None
                if vehicle.HasField('trip'):
                    trip = vehicle.trip
                    trip_id = trip.trip_id if trip.HasField('trip_id') else None
                    route_id = trip.route_id if trip.HasField('route_id') else None
                
                # Add to train data
                train_data.append({
                    'id': train_id,
                    'lat': lat,
                    'lon': lon,
                    'speed': speed_kmh,
                    'timestamp': timestamp,
                    'trip_id': trip_id,
                    'route_id': route_id
                })
        
        return train_data, datetime.now().strftime('%H:%M:%S')
    except requests.exceptions.HTTPError as http_err:
        error_msg = f"HTTP Error occurred: {http_err}"
        print(error_msg)
        # Check specifically for rate limiting or authentication issues
        if hasattr(http_err, 'response') and http_err.response.status_code in [429, 403]:
            print("Possible rate limiting or authentication issue. Adding delay before next request.")
        return [], datetime.now().strftime('%H:%M:%S') + " (API Error)"
    except requests.exceptions.ConnectionError:
        error_msg = "Connection Error: Could not connect to the API"
        print(error_msg)
        return [], datetime.now().strftime('%H:%M:%S') + " (Connection Error)"
    except requests.exceptions.Timeout:
        error_msg = "Timeout Error: The request timed out"
        print(error_msg)
        return [], datetime.now().strftime('%H:%M:%S') + " (Timeout)"
    except requests.exceptions.RequestException as req_err:
        error_msg = f"Request Error: {req_err}"
        print(error_msg)
        return [], datetime.now().strftime('%H:%M:%S') + " (Request Error)"
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        print(error_msg)
        return [], datetime.now().strftime('%H:%M:%S') + " (Error)"

# Get initial data
initial_data, initial_time = fetch_train_locations()

# App layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1([html.I(className="fas fa-train"), " Real-Time Train Tracker"]),
        html.Div([
            html.Button("Refresh", id="refresh-button", n_clicks=0),
            html.Div([
                "Last update: ", 
                html.Span(id="update-time", children=initial_time),
                html.Span(f" (Auto-refresh: {REFRESH_INTERVAL}s)", className="refresh-info")
            ])
        ], className="controls")
    ], className="header"),
    
    # Main content
    html.Div([
        # Map
        html.Div([
            dcc.Graph(
                id='train-map',
                figure={},
                style={'height': '100%'}
            ),
            # Legend for map markers
            html.Div([
                html.Div([
                    html.Div(className="marker-dot moving"),
                    html.Span("Moving")
                ], className="legend-item"),
                html.Div([
                    html.Div(className="marker-dot stopped"),
                    html.Span("Stopped")
                ], className="legend-item")
            ], className="map-legend")
        ], className="map-container"),
        
        # Sidebar
        html.Div([
            html.Div([
                html.H2("Active Trains"),
                dcc.Input(id="train-search", type="text", placeholder="Search by train ID..."),
                html.Div("Enter exact train number for precise results", className="search-hint"),
            ], className="sidebar-header"),
            
            html.Div(id="train-list", className="train-list")
        ], className="sidebar")
    ], className="main-content"),
    
    # Footer
    html.Footer([
        html.P("Data from Finnish Transport Infrastructure Agency GTFS-RT feed")
    ]),
    
    # Interval for auto-refresh (30 seconds)
    dcc.Interval(
        id='interval-component',
        interval=REFRESH_INTERVAL*1000,  # in milliseconds
        n_intervals=0
    ),
    
    # Store component to hold train data
    dcc.Store(id='train-data-store'),
    
    # Load Font Awesome
    html.Link(
        rel="stylesheet",
        href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
    )
], className="app-container")

# Callback to update train data periodically or on refresh button click
@app.callback(
    [Output('train-data-store', 'data'),
     Output('update-time', 'children')],
    [Input('interval-component', 'n_intervals'),
     Input('refresh-button', 'n_clicks')]
)
def update_data(n_intervals, n_clicks):
    train_data, update_time = fetch_train_locations()
    
    # Convert to format suitable for storage
    serializable_data = []
    for train in train_data:
        train_dict = dict(train)
        if train_dict['timestamp']:
            train_dict['timestamp'] = train_dict['timestamp'].isoformat()
        serializable_data.append(train_dict)
    
    return serializable_data, update_time

# Function to process search query (without pandas)
def filter_trains(trains, search_query):
    if not search_query:
        return trains
    
    search_query = search_query.strip()
    
    # First try exact match
    exact_matches = [train for train in trains if str(train['id']) == search_query]
    if exact_matches:
        return exact_matches
    
    # Then try contains match
    contains_matches = [train for train in trains if search_query in str(train['id'])]
    return contains_matches

# Callback to update the map
@app.callback(
    Output('train-map', 'figure'),
    [Input('train-data-store', 'data')]
)
def update_map(train_data):
    if not train_data:
        # Create empty map with Finland centered
        fig = go.Figure(go.Scattermap())
        fig.update_layout(
            map={
                'style': "open-street-map",
                'center': {'lat': FINLAND_CENTER['lat'], 'lon': FINLAND_CENTER['lon']},
                'zoom': 5.5
            },
            margin={'l': 0, 'r': 0, 't': 0, 'b': 0}
        )
        return fig
    
    # Create the map figure
    fig = go.Figure()
    
    # Create hover text with detailed train information
    hover_texts = []
    marker_colors = []
    lats = []
    lons = []
    text_labels = []
    
    for train in train_data:
        # Get coordinates
        lats.append(train['lat'])
        lons.append(train['lon'])
        
        # Get train ID for label
        text_labels.append(train['id'])
        
        # Determine color based on speed
        speed = train.get('speed')
        is_moving = speed is not None and speed > 0
        color = 'blue' if is_moving else 'red'
        marker_colors.append(color)
        
        # Create hover text
        hover_text = f"<b>Train {train['id']}</b><br>"
        hover_text += f"Speed: {speed:.1f} km/h<br>" if speed is not None else "Speed: N/A<br>"
        hover_text += f"Position: {train['lat']:.4f}, {train['lon']:.4f}<br>"
        
        if train.get('route_id'):
            hover_text += f"Route: {train['route_id']}<br>"
        
        if train.get('trip_id'):
            hover_text += f"Trip: {train['trip_id']}"
            
        hover_texts.append(hover_text)
    
    # Add train markers with hover information
    fig.add_trace(go.Scattermap(
        lat=lats,
        lon=lons,
        mode='markers+text',
        marker=dict(
            size=12,
            color=marker_colors,
            opacity=0.8
        ),
        text=text_labels,
        textposition='top center',
        textfont=dict(
            family='Arial',
            size=10,
            color='black'
        ),
        hovertext=hover_texts,
        hoverinfo='text',
        hovertemplate='%{hovertext}<extra></extra>'  # Remove trace name from hover
    ))
    
    # Configure the map layout
    fig.update_layout(
        map={
            'style': "open-street-map",
            'center': {'lat': FINLAND_CENTER['lat'], 'lon': FINLAND_CENTER['lon']},
            'zoom': 5.5
        },
        margin={'l': 0, 'r': 0, 't': 0, 'b': 0},
        uirevision='constant',  # Preserve zoom and center position on updates
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Segoe UI, Arial"
        )
    )
    
    return fig

# Callback to update the train list
@app.callback(
    Output('train-list', 'children'),
    [Input('train-data-store', 'data'),
     Input('train-search', 'value')]
)
def update_train_list(train_data, search_value):
    if not train_data:
        return html.Div("No trains found", className="loading")
    
    # Filter trains based on search value
    if search_value:
        filtered_trains = filter_trains(train_data, search_value)
        print(f"Search: '{search_value}', found {len(filtered_trains)} matches")
    else:
        filtered_trains = train_data
    
    # Sort trains by ID
    sorted_trains = sorted(filtered_trains, key=lambda t: str(t['id']))
    
    # Create train items
    train_items = []
    for train in sorted_trains:
        # Determine train status (moving or stopped)
        speed = train.get('speed')
        is_moving = speed is not None and speed > 0
        status_class = "moving" if is_moving else "stopped"
        status_text = "Moving" if is_moving else "Stopped"
        
        train_item = html.Div([
            html.Div([
                html.Span(f"Train {train['id']}"),
                html.Span(f"{speed:.1f} km/h" if speed is not None else "N/A")
            ], className="train-item-header"),
            html.Div([
                html.Div([
                    html.I(className="fas fa-circle", style={"color": "blue" if is_moving else "red"}),
                    status_text
                ]),
                html.Div([
                    html.I(className="fas fa-map-marker-alt"),
                    f"{train['lat']:.4f}, {train['lon']:.4f}"
                ]),
                html.Div([
                    html.I(className="fas fa-route"),
                    train.get('route_id', 'N/A')
                ]) if train.get('route_id') else None
            ], className="train-item-details")
        ], className=f"train-item {status_class}")
        
        train_items.append(train_item)
    
    if not train_items:
        return html.Div("No trains match your search", className="loading")
    
    # Add summary statistics
    total_trains = len(train_data)
    moving_trains = sum(1 for train in train_data if train.get('speed') is not None and train.get('speed') > 0)
    stationary_trains = total_trains - moving_trains
    
    stats = html.Div([
        html.Div(f"Total Trains: {total_trains}", className="stat-item"),
        html.Div(f"Moving: {moving_trains}", className="stat-item moving"),
        html.Div(f"Stopped: {stationary_trains}", className="stat-item stopped"),
    ], className="train-stats")
    
    return [stats] + train_items