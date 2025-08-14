# Personal Portfolio Website

A modern portfolio website built with Flask, featuring visitor analytics, career advice blog, and responsive design.

## 📁 Project Structure

```
ResumeForThanh/
├── 📁 src/                    # Source code
│   ├── 📁 templates/          # HTML templates
│   │   ├── index.html         # Main portfolio page
│   │   ├── career-advice.html # Career advice blog
│   │   ├── traffic.html       # Analytics dashboard
│   │   └── *.html            # Other pages
│   ├── 📁 static/            # Static assets
│   │   ├── 📁 css/           # Stylesheets
│   │   ├── 📁 js/            # JavaScript files
│   │   ├── 📁 img/           # Images and media
│   │   └── 📁 vendor/        # Third-party libraries
│   └── 📁 forms/             # Form handling scripts
├── 📁 docs/                  # Documentation
│   ├── 📁 cv-resumes/        # CV and resume files
│   ├── 📁 job-applications/  # Job application tracker
│   └── *.md, *.txt          # Documentation files
├── 📁 database/              # Database files
│   └── visitor_count.db     # SQLite database
├── 📁 scripts/               # Utility scripts
│   ├── morse_code.py         # Morse code converter
│   └── process_docx.py       # Document processing
├── 📁 tests/                 # Test files
│   ├── test_*.py             # Unit tests
│   └── test_local.py         # Local testing
├── 📁 config/                # Configuration files
│   ├── requirements.txt      # Python dependencies
│   └── profile_content.json  # Profile data
├── app.py                    # Main Flask application
└── README.md                 # This file
```

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r config/requirements.txt
   ```

2. **Run the Application**
   ```bash
   python app.py
   ```

3. **Access the Website**
   - Main Portfolio: `http://localhost:8000`
   - Career Advice: `http://localhost:8000/career-advice.html`
   - Analytics: `http://localhost:8000/traffic.html`

## 🛠️ Technology Stack

- **Backend**: Python Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **Database**: SQLite
- **Libraries**: Bootstrap 5, React (CDN), GSAP, AOS
- **Email**: Flask-Mail with Gmail SMTP

## 📊 Features

- **Portfolio Showcase**: Interactive project gallery
- **Career Advice Blog**: LaTeX, Markdown, and plain text support
- **Visitor Analytics**: Real-time tracking and statistics
- **Contact Form**: Email integration with form validation
- **Responsive Design**: Mobile-first approach
- **Animations**: Smooth GSAP-powered animations

## 📝 Configuration

- Update email settings in `app.py`
- Modify profile data in `config/profile_content.json`
- Customize styling in `src/static/css/main.css`

## 🔧 Development

- **Templates**: Located in `src/templates/`
- **Static Files**: Located in `src/static/`
- **Database**: SQLite file in `database/`
- **Tests**: Run tests from `tests/` directory

## 📄 License

Personal portfolio project - All rights reserved.
