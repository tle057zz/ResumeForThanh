#!/usr/bin/env python3
"""
Simple local development test script
Tests the website without triggering bot detection
"""

import requests
import time

def test_local_access():
    """Test basic local access to the website"""
    print("🏠 Testing Local Development Access")
    print("=" * 50)
    
    try:
        # Test main page
        response = requests.get('http://localhost:5000/')
        print(f"✅ Main page access: {response.status_code}")
        
        # Test traffic page
        response = requests.get('http://localhost:5000/traffic.html')
        print(f"✅ Traffic page access: {response.status_code}")
        
        # Test API endpoint
        response = requests.get('http://localhost:5000/api/visitor-stats')
        print(f"✅ API endpoint access: {response.status_code}")
        
        if response.status_code == 200:
            stats = response.json()
            print(f"📊 Current stats - Human: {stats.get('human_visitors', 0)}, Automated: {stats.get('automated_visitors', 0)}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to localhost:5000")
        print("   Make sure your Flask server is running: python app.py")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_browser_simulation():
    """Simulate a real browser visit"""
    print("\n🌐 Testing Browser Simulation")
    print("=" * 50)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        response = requests.get('http://localhost:5000/', headers=headers)
        print(f"✅ Browser simulation successful: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Browser simulation failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Local Development Test")
    print("=" * 60)
    print("This script tests basic access to your website")
    print("without triggering the bot detection system.")
    print()
    
    # Wait a moment for server to be ready
    time.sleep(1)
    
    # Run tests
    test_local_access()
    test_browser_simulation()
    
    print("\n🎯 Next Steps:")
    print("1. Open your browser and go to http://localhost:5000")
    print("2. Navigate to the Traffic page to see visitor tracking")
    print("3. Try the visitor detection tests: python test_visitor_detection.py")
    print("4. Check the database: python test_visitor_tracking.py") 