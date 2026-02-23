from flask import Flask, request, jsonify, send_from_directory, render_template, make_response
from flask_compress import Compress
from flask_mail import Mail, Message
import sqlite3
import datetime
import json
from datetime import timezone
import pytz
import os

# Configure Flask app with new folder structure
app = Flask(__name__, 
            template_folder='src/templates',
            static_folder='src/static')

# Enable gzip/Brotli compression for faster first loads
Compress(app)

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'lenhothanh.nsl@gmail.com'
app.config['MAIL_PASSWORD'] = 'zqfniibwzgvziibb'
app.config['MAIL_DEFAULT_SENDER'] = 'lenhothanh.nsl@gmail.com'

mail = Mail(app)

import requests
import time
import threading

# Database functions
def create_db():
    conn = sqlite3.connect('database/visitor_count.db')
    cursor = conn.cursor()
    
    # Check if visitors table exists and has the new columns
    cursor.execute("PRAGMA table_info(visitors)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'visitors' not in [table[0] for table in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
        # Create new visitors table with all columns
        cursor.execute('''
            CREATE TABLE visitors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT,
                user_agent TEXT,
                page_visited TEXT,
                visit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                visitor_type TEXT DEFAULT 'Unknown',
                detection_reasons TEXT DEFAULT 'None'
            )
        ''')
    else:
        # Add new columns if they don't exist
        if 'visitor_type' not in columns:
            cursor.execute('ALTER TABLE visitors ADD COLUMN visitor_type TEXT DEFAULT "Unknown"')
        if 'detection_reasons' not in columns:
            cursor.execute('ALTER TABLE visitors ADD COLUMN detection_reasons TEXT DEFAULT "None"')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS page_views (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_name TEXT,
            view_count INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Career advice posts table for server-backed persistence
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS career_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            format TEXT DEFAULT 'plain',
            images TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Initialize page views if empty
    cursor.execute('SELECT COUNT(*) FROM page_views')
    if cursor.fetchone()[0] == 0:
        pages = ['home', 'about', 'resume', 'portfolio', 'contact', 'career-advice', 'traffic']
        for page in pages:
            cursor.execute('INSERT INTO page_views (page_name, view_count) VALUES (?, 0)', (page,))
    
    conn.commit()
    conn.close()

GEOLOCATION_CACHE = {}

def get_location_from_ip(ip):
    if ip in GEOLOCATION_CACHE:
        return GEOLOCATION_CACHE[ip]
    if ip in ('127.0.0.1', '::1', 'localhost'):
        GEOLOCATION_CACHE[ip] = 'Localhost'
        return 'Localhost'
    try:
        resp = requests.get(f'http://ip-api.com/json/{ip}', timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('status') == 'success':
                city = data.get('city') or ''
                region = data.get('regionName') or ''
                country = data.get('country') or ''
                location = ', '.join([part for part in [city, region, country] if part])
                GEOLOCATION_CACHE[ip] = location
                return location
        GEOLOCATION_CACHE[ip] = 'Unknown'
        return 'Unknown'
    except Exception:
        GEOLOCATION_CACHE[ip] = 'Unknown'
        return 'Unknown'

def get_visitor_stats():
    conn = sqlite3.connect('database/visitor_count.db')
    cursor = conn.cursor()
    
    # Total visitors (all types, excluding traffic page)
    cursor.execute('SELECT COUNT(*) FROM visitors WHERE page_visited != "traffic"')
    total_visitors = cursor.fetchone()[0]
    
    # Human visitors only (excluding traffic page)
    cursor.execute('SELECT COUNT(*) FROM visitors WHERE visitor_type = "Human" AND page_visited != "traffic"')
    human_visitors = cursor.fetchone()[0]
    
    # Automated visitors (excluding traffic page)
    cursor.execute('SELECT COUNT(*) FROM visitors WHERE visitor_type = "Automated" AND page_visited != "traffic"')
    automated_visitors = cursor.fetchone()[0]
    
    # Unique visitors (by IP, excluding traffic page)
    cursor.execute('SELECT COUNT(DISTINCT ip_address) FROM visitors WHERE page_visited != "traffic"')
    unique_visitors = cursor.fetchone()[0]
    
    # Today's visitors (Sydney timezone, excluding traffic page)
    sydney_tz = pytz.timezone('Australia/Sydney')
    sydney_now = datetime.datetime.now(sydney_tz)
    today = sydney_now.strftime('%Y-%m-%d')
    cursor.execute('SELECT COUNT(*) FROM visitors WHERE DATE(visit_time) = ? AND page_visited != "traffic"', (today,))
    today_visitors = cursor.fetchone()[0]
    
    # Today's human visitors (excluding traffic page)
    cursor.execute('SELECT COUNT(*) FROM visitors WHERE DATE(visit_time) = ? AND visitor_type = "Human" AND page_visited != "traffic"', (today,))
    today_human_visitors = cursor.fetchone()[0]
    
    # Current online humans (active in last 5 minutes, Sydney time, excluding traffic page)
    sydney_tz = pytz.timezone('Australia/Sydney')
    sydney_now = datetime.datetime.now(sydney_tz)
    five_minutes_ago = sydney_now - datetime.timedelta(minutes=5)
    cursor.execute('''
        SELECT COUNT(DISTINCT ip_address) FROM visitors
        WHERE visitor_type = "Human"
          AND page_visited != "traffic"
          AND visit_time >= ?
    ''', (five_minutes_ago.strftime('%Y-%m-%d %H:%M:%S'),))
    current_online_humans = cursor.fetchone()[0]
    
    # Page views (human visitors only)
    cursor.execute('SELECT page_name, view_count FROM page_views')
    page_views = dict(cursor.fetchall())
    
    # Recent activity (last 10 visits with visitor type, excluding traffic page visits)
    cursor.execute('''
        SELECT ip_address, page_visited, visit_time, visitor_type, detection_reasons
        FROM visitors 
        WHERE page_visited != 'traffic'
        ORDER BY visit_time DESC 
        LIMIT 10
    ''')
    recent_activity_raw = cursor.fetchall()
    # Geolocate each IP
    recent_activity = []
    for row in recent_activity_raw:
        ip = row[0]
        location = get_location_from_ip(ip)
        recent_activity.append(row + (location,))
    
    # Visitor type distribution (excluding traffic page)
    cursor.execute('''
        SELECT visitor_type, COUNT(*) as count 
        FROM visitors 
        WHERE page_visited != 'traffic'
        GROUP BY visitor_type
    ''')
    visitor_types = dict(cursor.fetchall())
    
    conn.close()
    
    return {
        'total_visitors': total_visitors,
        'human_visitors': human_visitors,
        'automated_visitors': automated_visitors,
        'unique_visitors': unique_visitors,
        'today_visitors': today_visitors,
        'today_human_visitors': today_human_visitors,
        'current_online_humans': current_online_humans,
        'page_views': page_views,
        'recent_activity': recent_activity,
        'visitor_types': visitor_types
    }

def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

def detect_visitor_type():
    """Detect if visitor is human or automated system"""
    visitor_ip = get_client_ip()
    user_agent = request.headers.get('User-Agent', 'Unknown')
    referer = request.headers.get('Referer', '')
    accept_language = request.headers.get('Accept-Language', '')
    accept_encoding = request.headers.get('Accept-Encoding', '')
    
    # Initialize detection flags
    is_human = True
    detection_reasons = []
    
    # 1. User-Agent Analysis
    bot_agents = ['curl', 'bot', 'python', 'wget', 'postman', 'scraper', 'spider', 'crawler', 'automation']
    user_agent_lower = user_agent.lower()
    
    for bot_agent in bot_agents:
        if bot_agent in user_agent_lower:
            is_human = False
            detection_reasons.append(f"Bot user agent detected: {bot_agent}")
            break
    
    # 2. IP Address Analysis (common automated IPs)
    # For local development, be more lenient with localhost
    automated_ips = [
        '0.0.0.0',    # broadcast
    ]
    
    # Only flag localhost as automated in production
    if visitor_ip in automated_ips:
        is_human = False
        detection_reasons.append(f"Automated IP detected: {visitor_ip}")
    elif visitor_ip in ['127.0.0.1', '::1']:
        # For localhost, just note it but don't flag as automated
        detection_reasons.append(f"Localhost IP: {visitor_ip}")
    
    # 3. Header Analysis
    # Check for missing or suspicious headers (more lenient for localhost)
    if not accept_language and visitor_ip not in ['127.0.0.1', '::1']:
        is_human = False
        detection_reasons.append("Missing Accept-Language header")
    elif not accept_language:
        detection_reasons.append("No Accept-Language header (localhost)")
    
    if not accept_encoding and visitor_ip not in ['127.0.0.1', '::1']:
        is_human = False
        detection_reasons.append("Missing Accept-Encoding header")
    elif not accept_encoding:
        detection_reasons.append("No Accept-Encoding header (localhost)")
    
    # 4. Referer Analysis
    # Note: This check is basic - home page might not have referer
    if not referer:
        # Don't immediately flag as automated, just note it
        detection_reasons.append("No referer header")
    
    # 5. Request Timing Analysis (basic)
    # This would need to be enhanced with session tracking for better accuracy
    
    return {
        'is_human': is_human,
        'visitor_type': 'Human' if is_human else 'Automated',
        'detection_reasons': detection_reasons,
        'ip_address': visitor_ip,
        'user_agent': user_agent,
        'referer': referer
    }

def record_visit(page_name):
    visitor_ip = get_client_ip()
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    # Detect visitor type
    visitor_info = detect_visitor_type()
    
    conn = sqlite3.connect('database/visitor_count.db')
    cursor = conn.cursor()
    
    # Get current UTC time for consistent timezone handling
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    
    # Record the visit with visitor type information
    cursor.execute('''
        INSERT INTO visitors (ip_address, user_agent, page_visited, visit_time, visitor_type, detection_reasons) 
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (visitor_ip, user_agent, page_name, utc_now, visitor_info['visitor_type'], 
          ', '.join(visitor_info['detection_reasons']) if visitor_info['detection_reasons'] else 'None'))
    
    # Only update page view count for human visitors
    if visitor_info['is_human']:
        cursor.execute('''
            UPDATE page_views 
            SET view_count = view_count + 1, last_updated = CURRENT_TIMESTAMP 
            WHERE page_name = ?
        ''', (page_name,))
    
    conn.commit()
    conn.close()
    
    return visitor_info

URL = "https://www.thanhle.it.com/"
# URL2 = "https://modelbasedapp.onrender.com/"
URL2 = ""
def ping(URL):
    try:
        response = requests.get(URL, timeout=10)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if response.status_code == 200:
            print(f"[{now}] ✅ App is awake - Status: {response.status_code}")
        else:
            print(f"[{now}] ⚠️  Unexpected status: {response.status_code}")
    except requests.RequestException as e:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{now}] ❌ Ping failed: {e}")

def run_ping_cron():
    """Run ping function every 15 minutes in a separate thread"""
    while True:
        ping(URL)
        ping(URL2)
        time.sleep(12 * 60)  # 15 minutes in seconds



@app.route('/')
def index():
    record_visit('home')
    return render_template('index.html')

@app.route('/index.html')
def index_html():
    record_visit('home')
    return render_template('index.html')

@app.route('/career-advice.html')
def career_advice():
    record_visit('career-advice')
    return render_template('career-advice.html')

@app.route('/traffic.html')
def traffic():
    record_visit('traffic')
    return render_template('traffic.html')

@app.route('/explore.html')
def explore():
    record_visit('explore')
    return render_template('explore.html')

@app.route('/portfolio-details.html')
def portfolio_details():
    return render_template('portfolio-details.html')

@app.route('/service-details.html')
def service_details():
    return render_template('service-details.html')

@app.route('/starter-page.html')
def starter_page():
    return render_template('starter-page.html')

@app.route('/<path:path>')
def static_proxy(path):
    # Serve static files with aggressive caching headers in production
    response = make_response(send_from_directory('src/static', path))
    # Cache static assets for 30 days; fingerprinted files will benefit most
    response.headers['Cache-Control'] = 'public, max-age=2592000, immutable'
    return response

@app.route('/api/visitor-stats')
def visitor_stats():
    return jsonify(get_visitor_stats())

@app.route('/api/record-visit', methods=['POST'])
def record_visit_api():
    data = request.get_json()
    page_name = data.get('page', 'unknown')
    record_visit(page_name)
    return jsonify({'success': True, 'message': 'Visit recorded'})

# -------------------- Career Advice Posts API --------------------
@app.route('/api/career-posts', methods=['GET', 'POST'])
def career_posts_api():
    conn = sqlite3.connect('database/visitor_count.db')
    cursor = conn.cursor()
    if request.method == 'GET':
        cursor.execute('''
            SELECT id, title, content, format, images, created_at, updated_at
            FROM career_posts
            ORDER BY datetime(created_at) DESC, id DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        posts = [
            {
                'id': r[0],
                'title': r[1],
                'content': r[2],
                'format': r[3] or 'plain',
                'images': json.loads(r[4] or '[]'),
                'createdAt': r[5],
                'updatedAt': r[6],
            }
            for r in rows
        ]
        return jsonify(posts)
    else:
        data = request.get_json() or {}
        title = (data.get('title') or '').strip()
        content = (data.get('content') or '').strip()
        fmt = (data.get('format') or 'plain').strip()
        images = data.get('images') or []
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor.execute(
            'INSERT INTO career_posts (title, content, format, images, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
            (title, content, fmt, json.dumps(images), now_iso, now_iso)
        )
        post_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'id': post_id})


@app.route('/api/career-posts/<int:post_id>', methods=['PUT', 'DELETE'])
def career_post_update_delete(post_id: int):
    conn = sqlite3.connect('database/visitor_count.db')
    cursor = conn.cursor()
    if request.method == 'PUT':
        data = request.get_json() or {}
        fields = []
        values = []
        if 'title' in data:
            fields.append('title = ?')
            values.append((data.get('title') or '').strip())
        if 'content' in data:
            fields.append('content = ?')
            values.append((data.get('content') or '').strip())
        if 'format' in data:
            fields.append('format = ?')
            values.append((data.get('format') or 'plain').strip())
        if 'images' in data:
            fields.append('images = ?')
            values.append(json.dumps(data.get('images') or []))
        # Always update timestamp
        fields.append('updated_at = ?')
        values.append(datetime.datetime.now(datetime.timezone.utc).isoformat())
        values.append(post_id)
        cursor.execute(f'UPDATE career_posts SET {", ".join(fields)} WHERE id = ?', values)
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    else:
        cursor.execute('DELETE FROM career_posts WHERE id = ?', (post_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

@app.route('/send_email', methods=['POST'])
def send_email():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    subject = data.get('subject')
    message = data.get('message')

    msg = Message(
        subject=f"Contact Form: {subject} from {name} <{email}>",
        recipients=['lenhothanh.nsl@gmail.com']  # Your displayed email
    )
    msg.body = (
        f"You have received a new message from your website contact form.\n\n"
        f"Sender Name: {name}\n"
        f"Sender Email: {email}\n"
        f"Subject: {subject}\n\n"
        f"Message:\n{message}\n"
    )

    try:
        mail.send(msg)
        return jsonify({'success': True, 'message': 'Email sent successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    # Initialize database
    create_db()
    print("Database initialized")
    
    # Start the ping cron job in a separate daemon thread
    ping_thread = threading.Thread(target=run_ping_cron, daemon=False)
    ping_thread.start()
    print("Ping cron job started in background thread")
    
    # Start the Flask app on port 8000 to avoid macOS AirPlay conflict
    app.run(debug=True, port=8000)