#!/usr/bin/env python3
"""
Test script for visitor tracking functionality
"""

import sqlite3
import datetime

def test_database():
    """Test the database connection and structure"""
    try:
        conn = sqlite3.connect('visitor_count.db')
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"✅ Database tables found: {[table[0] for table in tables]}")
        
        # Check visitors table
        cursor.execute("SELECT COUNT(*) FROM visitors")
        visitor_count = cursor.fetchone()[0]
        print(f"📊 Total visitors recorded: {visitor_count}")
        
        # Check page views
        cursor.execute("SELECT page_name, view_count FROM page_views")
        page_views = cursor.fetchall()
        print("📈 Page views:")
        for page, count in page_views:
            print(f"   {page}: {count}")
        
        # Check recent activity
        cursor.execute("""
            SELECT ip_address, page_visited, visit_time 
            FROM visitors 
            ORDER BY visit_time DESC 
            LIMIT 5
        """)
        recent = cursor.fetchall()
        print("🕒 Recent activity:")
        for ip, page, time in recent:
            print(f"   {time} - {ip} visited {page}")
        
        conn.close()
        print("✅ Database test completed successfully!")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")

def test_api_endpoints():
    """Test the API endpoints"""
    import requests
    
    base_url = "http://localhost:5000"
    
    try:
        # Test visitor stats endpoint
        response = requests.get(f"{base_url}/api/visitor-stats")
        if response.status_code == 200:
            data = response.json()
            print("✅ API endpoint /api/visitor-stats working")
            print(f"   Total visitors: {data.get('total_visitors', 0)}")
            print(f"   Today's visitors: {data.get('today_visitors', 0)}")
        else:
            print(f"❌ API endpoint failed with status: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Flask server. Make sure it's running on localhost:5000")
    except Exception as e:
        print(f"❌ API test failed: {e}")

if __name__ == "__main__":
    print("🧪 Testing Visitor Tracking System")
    print("=" * 40)
    
    test_database()
    print()
    test_api_endpoints()
    
    print("\n" + "=" * 40)
    print("🎯 To test the full system:")
    print("1. Run: python app.py")
    print("2. Visit: http://localhost:5000")
    print("3. Visit: http://localhost:5000/traffic.html")
    print("4. Check the Traffic page for real analytics data!") 