from flask import Flask, request, jsonify, send_from_directory
from flask_mail import Mail, Message
import sqlite3
import datetime
import json

app = Flask(__name__)

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
    conn = sqlite3.connect('visitor_count.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS visitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT,
            user_agent TEXT,
            page_visited TEXT,
            visit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS page_views (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_name TEXT,
            view_count INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

def get_visitor_stats():
    conn = sqlite3.connect('visitor_count.db')
    cursor = conn.cursor()
    
    # Total visitors
    cursor.execute('SELECT COUNT(*) FROM visitors')
    total_visitors = cursor.fetchone()[0]
    
    # Unique visitors (by IP)
    cursor.execute('SELECT COUNT(DISTINCT ip_address) FROM visitors')
    unique_visitors = cursor.fetchone()[0]
    
    # Today's visitors
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    cursor.execute('SELECT COUNT(*) FROM visitors WHERE DATE(visit_time) = ?', (today,))
    today_visitors = cursor.fetchone()[0]
    
    # Page views
    cursor.execute('SELECT page_name, view_count FROM page_views')
    page_views = dict(cursor.fetchall())
    
    # Recent activity (last 10 visits)
    cursor.execute('''
        SELECT ip_address, page_visited, visit_time 
        FROM visitors 
        ORDER BY visit_time DESC 
        LIMIT 10
    ''')
    recent_activity = cursor.fetchall()
    
    conn.close()
    
    return {
        'total_visitors': total_visitors,
        'unique_visitors': unique_visitors,
        'today_visitors': today_visitors,
        'page_views': page_views,
        'recent_activity': recent_activity
    }

def record_visit(page_name):
    visitor_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    conn = sqlite3.connect('visitor_count.db')
    cursor = conn.cursor()
    
    # Record the visit
    cursor.execute('''
        INSERT INTO visitors (ip_address, user_agent, page_visited, visit_time) 
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    ''', (visitor_ip, user_agent, page_name))
    
    # Update page view count
    cursor.execute('''
        UPDATE page_views 
        SET view_count = view_count + 1, last_updated = CURRENT_TIMESTAMP 
        WHERE page_name = ?
    ''', (page_name,))
    
    conn.commit()
    conn.close()

URL = "https://www.thanhle.it.com/"

def ping():
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
        ping()
        time.sleep(10 * 60)  # 15 minutes in seconds



@app.route('/')
def index():
    record_visit('home')
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    # Record visits for specific pages
    if path in ['traffic.html', 'career-advice.html']:
        page_name = path.replace('.html', '')
        record_visit(page_name)
    elif path == 'index.html':
        record_visit('home')
    else:
        # For other static files, don't record visits
        pass
    
    return send_from_directory('.', path)

@app.route('/api/visitor-stats')
def visitor_stats():
    return jsonify(get_visitor_stats())

@app.route('/api/record-visit', methods=['POST'])
def record_visit_api():
    data = request.get_json()
    page_name = data.get('page', 'unknown')
    record_visit(page_name)
    return jsonify({'success': True, 'message': 'Visit recorded'})

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
    
    # Start the Flask app
    app.run(debug=True)