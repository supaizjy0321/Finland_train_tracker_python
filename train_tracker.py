import dash
from dash import html, dcc
import plotly.graph_objects as go
from dash.dependencies import Input, Output
import requests
from google.transit import gtfs_realtime_pb2
from datetime import datetime
import pandas as pd
import time

# Initialize the Dash app
app = dash.Dash(__name__, title="Real-Time Train Tracker")
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
            mapbox={
                'style': "open-street-map",
                'center': {'lat': FINLAND_CENTER['lat'], 'lon': FINLAND_CENTER['lon']},
                'zoom': 5.5
            },
            margin={'l': 0, 'r': 0, 't': 0, 'b': 0}
        )
        return fig
    
    # Create the map figure
    fig = go.Figure()
    
    # Convert to DataFrame for easier processing
    train_df = pd.DataFrame(train_data)
    
    # Create hover text with detailed train information
    hover_texts = []
    for _, train in train_df.iterrows():
        timestamp_str = train['timestamp'] if isinstance(train['timestamp'], str) else "N/A"
        if timestamp_str and timestamp_str != "N/A":
            try:
                timestamp_obj = datetime.fromisoformat(timestamp_str)
                timestamp_str = timestamp_obj.strftime("%H:%M:%S %d-%m-%Y")
            except:
                pass
            
        hover_text = f"<b>Train {train['id']}</b><br>"
        hover_text += f"Speed: {train['speed']:.1f} km/h<br>" if pd.notna(train['speed']) else "Speed: N/A<br>"
        hover_text += f"Position: {train['lat']:.4f}, {train['lon']:.4f}<br>"
        
        if pd.notna(train['route_id']):
            hover_text += f"Route: {train['route_id']}<br>"
        
        if pd.notna(train['trip_id']):
            hover_text += f"Trip: {train['trip_id']}"
            
        # Removed the "Updated: timestamp" line per user's request
        
        hover_texts.append(hover_text)
    
    # Define colors based on train movement
    marker_colors = []
    for _, train in train_df.iterrows():
        if pd.notna(train['speed']) and train['speed'] > 0:
            color = 'blue'  # Moving trains are blue
        else:
            color = 'red'   # Stopped trains are red
            
        marker_colors.append(color)
    
    # Add train markers with hover information - using Scattermap instead of deprecated Scattermapbox
    fig.add_trace(go.Scattermap(
        lat=train_df['lat'],
        lon=train_df['lon'],
        mode='markers+text',
        marker=dict(
            size=12,
            color=marker_colors,
            opacity=0.8
        ),
        text=train_df['id'],
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
    
    # Configure the map layout - using modern 'map' property instead of 'mapbox'
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
    
    # Convert to DataFrame for easier filtering and sorting
    df = pd.DataFrame(train_data)
    
    # Apply search filter if specified
    if search_value:
        search_value = search_value.strip()  # Remove leading/trailing whitespace
        
        # Check if search is a numeric value
        if search_value.isdigit():
            # For numeric searches, use exact match if it's the full number
            # This ensures "9" only matches train ID "9", not "149" or "92"
            df = df[df['id'].astype(str) == search_value]
            
            # If no exact matches found (and search is short), try word boundary search
            if df.empty and len(search_value) <= 3:
                # This will match at beginning or end of ID or as a whole number
                pattern = fr'\b{search_value}\b'
                df = df[df['id'].astype(str).str.match(pattern, case=False)]
                
                # If still no matches, then fallback to contains
                if df.empty:
                    df = df[df['id'].astype(str).str.contains(search_value, case=False)]
        else:
            # For non-numeric searches, use contains as before
            df = df[df['id'].astype(str).str.contains(search_value, case=False)]
            
        # Print diagnostic information
        print(f"Search: '{search_value}', found {len(df)} matches")
    
    # Sort by train ID
    df = df.sort_values('id')
    
    # Create list items
    train_items = []
    for _, train in df.iterrows():
        # Determine train status (moving or stopped)
        is_moving = pd.notna(train['speed']) and train['speed'] > 0
        status_class = "moving" if is_moving else "stopped"
        status_text = "Moving" if is_moving else "Stopped"
        
        train_item = html.Div([
            html.Div([
                html.Span(f"Train {train['id']}"),
                html.Span(f"{train['speed']:.1f} km/h" if pd.notna(train['speed']) else "N/A")
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
                    train['route_id'] if pd.notna(train['route_id']) else "N/A"
                ]) if 'route_id' in train and pd.notna(train['route_id']) else None
            ], className="train-item-details")
        ], className=f"train-item {status_class}")
        
        train_items.append(train_item)
    
    if not train_items:
        return html.Div("No trains match your search", className="loading")
    
    return train_items

# Run the app if executed directly
if __name__ == '__main__':
    # For local development
    app.run_server(debug=True)