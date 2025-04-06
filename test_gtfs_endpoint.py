import requests
from google.transit import gtfs_realtime_pb2
import time

# The specific endpoint we must use
URL = 'https://rata.digitraffic.fi/api/v1/trains/gtfs-rt-locations'

def test_endpoint_with_headers(headers):
    """Test the endpoint with different headers"""
    print(f"\nTesting with headers: {headers}")
    
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        print(f"Status code: {response.status_code}")
        print(f"Content type: {response.headers.get('Content-Type')}")
        
        if response.status_code == 200:
            print(f"Content length: {len(response.content)} bytes")
            try:
                # Try to parse as protocol buffer
                feed = gtfs_realtime_pb2.FeedMessage()
                feed.ParseFromString(response.content)
                print(f"SUCCESS! Parsed {len(feed.entity)} entities")
                return True
            except Exception as e:
                print(f"Failed to parse response as protobuf: {e}")
        
    except Exception as e:
        print(f"Request failed: {e}")
    
    return False

# Let's test with different headers
headers_to_try = [
    # Test 1: Minimal headers
    {
        'Accept': 'application/x-protobuf'
    },
    
    # Test 2: More detailed headers
    {
        'Accept': 'application/x-protobuf',
        'User-Agent': 'TrainTrackerTest/1.0'
    },
    
    # Test 3: Full headers with Digitraffic-User
    {
        'Accept': 'application/x-protobuf',
        'User-Agent': 'TrainTrackerTest/1.0',
        'Digitraffic-User': 'TrainTrackerTest'
    },
    
    # Test 4: Adding cache control
    {
        'Accept': 'application/x-protobuf',
        'User-Agent': 'TrainTrackerTest/1.0',
        'Digitraffic-User': 'TrainTrackerTest',
        'Cache-Control': 'no-cache'
    }
]

# Run the tests
successful_headers = None
for i, headers in enumerate(headers_to_try):
    print(f"\n=== Test {i+1} ===")
    if test_endpoint_with_headers(headers):
        successful_headers = headers
        print(f"Test {i+1} succeeded! We have a working configuration.")
        break
    time.sleep(2)  # Wait between tests

if successful_headers:
    print("\n=== SUCCESS! ===")
    print(f"Working headers: {successful_headers}")
else:
    print("\n=== All tests failed ===")
    print("Could not find working header configuration")