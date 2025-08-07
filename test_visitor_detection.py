#!/usr/bin/env python3
"""
Test script for visitor detection system
Demonstrates how the system differentiates between human and automated visitors
"""

import requests
import time
import json
import pytz
from datetime import datetime

def test_human_visitor():
    """Simulate a human visitor with proper headers"""
    print("🧪 Testing Human Visitor Detection")
    print("=" * 50)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Referer': 'https://www.google.com/',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        response = requests.get('http://localhost:8000/', headers=headers)
        print(f"✅ Human visitor request successful: {response.status_code}")
        print(f"📋 Headers sent: {json.dumps(headers, indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Human visitor test failed: {e}")
        return False

def test_bot_visitor():
    """Simulate a bot/cron job visitor"""
    print("\n🤖 Testing Bot Visitor Detection")
    print("=" * 50)
    
    headers = {
        'User-Agent': 'curl/7.68.0',
        'Accept': '*/*'
    }
    
    try:
        response = requests.get('http://localhost:8000/', headers=headers)
        print(f"✅ Bot visitor request successful: {response.status_code}")
        print(f"📋 Headers sent: {json.dumps(headers, indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Bot visitor test failed: {e}")
        return False

def test_python_script():
    """Simulate a Python script visitor"""
    print("\n🐍 Testing Python Script Detection")
    print("=" * 50)
    
    headers = {
        'User-Agent': 'python-requests/2.25.1',
        'Accept': '*/*'
    }
    
    try:
        response = requests.get('http://localhost:8000/', headers=headers)
        print(f"✅ Python script request successful: {response.status_code}")
        print(f"📋 Headers sent: {json.dumps(headers, indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Python script test failed: {e}")
        return False

def test_localhost_visitor():
    """Test localhost visitor (should be treated as human for local development)"""
    print("\n🏠 Testing Localhost Visitor Detection")
    print("=" * 50)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        # Missing some headers but should be allowed for localhost
    }
    
    try:
        response = requests.get('http://localhost:8000/', headers=headers)
        print(f"✅ Localhost visitor request successful: {response.status_code}")
        print(f"📋 Headers sent: {json.dumps(headers, indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Localhost visitor test failed: {e}")
        return False

def test_missing_headers():
    """Simulate a visitor with missing headers (non-localhost)"""
    print("\n🚫 Testing Missing Headers Detection")
    print("=" * 50)
    
    headers = {
        'User-Agent': 'Some Bot/1.0'
        # Missing Accept-Language and Accept-Encoding
    }
    
    try:
        response = requests.get('http://localhost:8000/', headers=headers)
        print(f"✅ Missing headers request successful: {response.status_code}")
        print(f"📋 Headers sent: {json.dumps(headers, indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Missing headers test failed: {e}")
        return False

def check_visitor_stats():
    """Check the visitor statistics after testing"""
    print("\n📊 Checking Visitor Statistics")
    print("=" * 50)
    
    try:
        response = requests.get('http://localhost:8000/api/visitor-stats')
        if response.status_code == 200:
            stats = response.json()
            print("✅ Visitor statistics retrieved successfully")
            print(f"📈 Human visitors: {stats.get('human_visitors', 0)}")
            print(f"🤖 Automated visitors: {stats.get('automated_visitors', 0)}")
            print(f"📊 Total visitors: {stats.get('total_visitors', 0)}")
            print(f"📅 Today's human visitors: {stats.get('today_human_visitors', 0)}")
            
            if stats.get('recent_activity'):
                print("\n🕒 Recent Activity (Sydney Time):")
                sydney_tz = pytz.timezone('Australia/Sydney')
                for activity in stats['recent_activity'][:3]:  # Show last 3
                    ip, page, timestamp, visitor_type, reasons = activity
                    # Convert to Sydney time
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        sydney_time = dt.astimezone(sydney_tz).strftime('%Y-%m-%d %I:%M:%S %p')
                    except:
                        sydney_time = timestamp
                    print(f"   {sydney_time} - {visitor_type} from {ip} visited {page}")
                    if reasons and reasons != 'None':
                        print(f"      Detection: {reasons}")
            
            return True
        else:
            print(f"❌ Failed to get visitor stats: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Visitor stats check failed: {e}")
        return False

def main():
    """Run all visitor detection tests"""
    print("🧪 Visitor Detection System Test")
    print("=" * 60)
    print("This script tests the visitor detection system by simulating")
    print("different types of visitors (human vs automated).")
    print("Make sure your Flask server is running on localhost:8000")
    print()
    
    # Wait a moment for server to be ready
    time.sleep(1)
    
    # Run tests
    tests = [
        test_human_visitor,
        test_localhost_visitor,
        test_bot_visitor,
        test_python_script,
        test_missing_headers
    ]
    
    successful_tests = 0
    for test in tests:
        if test():
            successful_tests += 1
        time.sleep(1)  # Wait between tests
    
    print(f"\n📋 Test Results: {successful_tests}/{len(tests)} tests passed")
    
    # Check final statistics
    print("\n" + "=" * 60)
    check_visitor_stats()
    
    print("\n🎯 Next Steps:")
    print("1. Visit http://localhost:8000/traffic.html")
    print("2. Check the 'Live Activity Feed' to see visitor types")
    print("3. Look at the 'Visitor Type Distribution' section")
    print("4. Notice how different requests are classified!")

if __name__ == "__main__":
    main() 