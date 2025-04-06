# Finland Train Tracker

A real-time web application that displays the current locations of trains across Finland using the GTFS-RT data from the Finnish Transport Infrastructure Agency.

![Finland Train Tracker](https://github.com/supaizjy0321/financial-risk-management/blob/main/Real-time%20Train%20Tracker.png)

## Features

- 🚆 **Real-time Train Tracking**: View the current locations of all trains in Finland
- 🔍 **Precise Search**: Find specific trains by ID with exact matching
- 🔄 **Auto-refresh**: Data updates automatically every 30 seconds
- 🗺️ **Interactive Map**: Clean and intuitive map interface with color-coded train markers

## How It Works

This application connects to the Finnish Transport Infrastructure Agency's GTFS-RT (General Transit Feed Specification - Real Time) API to fetch real-time data about train positions. The data is parsed and displayed on an interactive map, with additional information available when clicking on train markers.

- **Moving trains** are shown with **blue** markers
- **Stationary trains** are shown with **red** markers

## Installation and Setup

### Prerequisites

- Python 3.7 or higher
- pip package manager

### Step 1: Clone the Repository

```bash
git clone https://github.com/supaizjy0321/Finland_train_tracker_python.git
cd Finland_train_tracker_python
```

### Step 2: Create a Virtual Environment (Recommended)

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# For Windows:
venv\Scripts\activate

# For macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

Or install packages individually:

```bash
pip install dash plotly pandas requests gtfs-realtime-bindings
```

### Step 4: Run the Application

```bash
python train_tracker.py
```

### Step 5: Access the Application

Open your web browser and go to:
```
http://127.0.0.1:8050/
```

## Using the Application

1. **View All Trains**: When you first load the application, you'll see all active trains on the map
2. **Understand the Colors**: Blue markers represent moving trains, red markers are stationary trains
3. **Search for Trains**: Use the search box in the sidebar to find specific trains by ID (exact matching is used for precise results)
4. **View Train Details**: Click on any train marker to see detailed information including speed and route
5. **View Statistics**: The sidebar shows total counts of trains and their status
6. **Manual Refresh**: Click the "Refresh" button to update the data immediately
7. **Auto-refresh**: Data automatically updates every 30 seconds


## Customization

You can customize various aspects of the application by modifying the following:

- **Refresh Rate**: Change the `REFRESH_INTERVAL` variable in `train_tracker.py` (default is 30 seconds)
- **Map Center**: Adjust the `FINLAND_CENTER` coordinates in `train_tracker.py`
- **Appearance**: Modify the CSS in `assets/style.css` to change colors, sizes, and layout

## Technology Stack

- **[Dash](https://dash.plotly.com/)**: Python framework for building web applications
- **[Plotly](https://plotly.com/python/)**: Interactive visualization library with MapLibre integration
- **[Pandas](https://pandas.pydata.org/)**: Data manipulation and analysis
- **[GTFS-RT](https://developers.google.com/transit/gtfs-realtime)**: Protocol Buffers for real-time transit data

## Data Source

This project uses the open data API provided by the Finland Transport Infrastructure Agency:
- **GTFS-RT API Endpoint**: https://rata.digitraffic.fi/api/v1/trains/gtfs-rt-locations

## License

This project is open source and available under the MIT License.

## Acknowledgements

- Finnish Transport Infrastructure Agency for providing the open data API
- The Dash and Plotly communities for their excellent documentation

---

For questions or feedback, please open an issue on GitHub or contact the repository owner.
