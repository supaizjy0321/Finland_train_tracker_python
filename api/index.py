# Import the app from the parent directory
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now import the app
from train_tracker import app

# Vercel needs this variable for serverless deployment
app_instance = app.server