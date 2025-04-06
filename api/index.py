# Import from the Vercel-optimized app
from vercel_app import app

# Vercel needs this variable for serverless deployment
app_instance = app.server