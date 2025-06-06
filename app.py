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
    app.run(debug=True) 