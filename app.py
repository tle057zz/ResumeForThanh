from flask import Flask, request, jsonify, send_from_directory
from flask_mail import Mail, Message

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
import datetime
import threading

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
        time.sleep(13 * 60)  # 15 minutes in seconds



@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory('.', path)

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
    # Start the ping cron job in a separate daemon thread
    ping_thread = threading.Thread(target=run_ping_cron, daemon=False)
    ping_thread.start()
    print("Ping cron job started in background thread")
    
    # Start the Flask app
    app.run(debug=True)