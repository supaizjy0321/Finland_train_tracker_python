# Train Tracker with Dash and Plotly

A Python web application to track trains in real-time using GTFS-RT data from the Finnish Transport Infrastructure Agency.

## Features

- Real-time map showing train locations
- List of active trains with search functionality
- Auto-refresh every 30 seconds
- Responsive design that works on both desktop and mobile

## Installation

1. **Clone or download this repository**

2. **Create a virtual environment** (optional but recommended):
   ```bash
   python -m venv venv
   
   # For Windows
   venv\Scripts\activate
   
   # For macOS/Linux
   source venv/bin/activate
   ```

3. **Install the required packages**:
   ```bash
   pip install dash plotly pandas requests gtfs-realtime-bindings
   ```

4. **Create the folder structure**:
   ```
   train-tracker/
   │
   ├── train_tracker.py
   ├── README.md
   └── assets/
       └── style.css
   ```

5. **Run the application**:
   ```bash
   python train_tracker.py
   ```

6. **Open your browser** and go to:
   ```
   http://127.0.0.1:8050/
   ```

## How It Works

This application uses:

- **Dash**: A Python framework for building web applications
- **Plotly**: For interactive maps and visualizations
- **GTFS-RT**: For real-time train position data
- **Pandas**: For data manipulation

The application fetches GTFS-RT data from the Finnish Transport Infrastructure Agency's API, decodes the Protocol Buffer format, and displays the data on an interactive map.

## Customization

- Modify the refresh interval by changing the `interval` value in the `dcc.Interval` component
- Adjust the map center by modifying the `FINLAND_CENTER` variable
- Change the styling by editing the `assets/style.css` file

## Deployment

To deploy this application to a production environment, you can use services like:

- [Heroku](https://dash.plotly.com/deployment)
- [AWS](https://dash.plotly.com/deployment)
- [PythonAnywhere](https://help.pythonanywhere.com/pages/DeployExistingDjangoProject/)

## License

This project is licensed under the MIT License.