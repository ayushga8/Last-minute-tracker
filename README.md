# 🚀 Last-Minute Life Saver

A full-featured **productivity web app** built with Django that helps you manage tasks, build habits, track goals, and stay on top of deadlines — powered by AI prioritization.

![Python](https://img.shields.io/badge/Python-3.13-blue)
![Django](https://img.shields.io/badge/Django-6.0-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-purple)

## ✨ Features

- **📋 Task Management** — Create, categorize, and track tasks with deadlines, priorities, and status
- **🤖 AI Prioritization** — Gemini AI analyzes your tasks and provides smart priority recommendations
- **🔄 Habit Tracker** — Build streaks with daily/weekly habit tracking and progress visualization
- **🎯 Goal Setting** — Set long-term goals with progress bars and deadline tracking
- **📅 Calendar View** — Full interactive calendar (FullCalendar.js) showing all your tasks
- **🔔 Notifications** — In-app notification system for deadlines and reminders
- **🔐 Authentication** — Email + OTP login, Google OAuth sign-in
- **🌙 Dark Mode** — Beautiful glassmorphism UI with dark/light mode toggle
- **📊 Dashboard** — At-a-glance overview of your productivity metrics

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6.0, Python 3.13 |
| Database | PostgreSQL (Neon) |
| Auth | django-allauth, Google OAuth 2.0 |
| AI | Google Gemini API |
| Frontend | HTML, CSS (Glassmorphism), JavaScript |
| Calendar | FullCalendar.js |
| Email | Gmail SMTP |

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL database (or [Neon](https://neon.tech) for free cloud PostgreSQL)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/ayushga8/Last-minute-tracker.git
   cd Last-minute-tracker
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the server**
   ```bash
   python manage.py runserver
   ```

8. Visit `http://localhost:8000` 🎉

## 📁 Project Structure

```
lifesaver/
├── accounts/        # User auth, OTP, Google OAuth, settings
├── tasks/           # Task CRUD, AI prioritization
├── habits/          # Habit tracking, goals, streaks
├── calendar_sync/   # Calendar view with FullCalendar.js
├── notifications/   # In-app notification system
├── scheduler/       # Background task scheduling
├── lifesaver/       # Django project settings
├── static/          # CSS, JS assets
└── templates/       # Base templates
```

## 🔑 Environment Variables

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` for development |
| `DATABASE_URL` | PostgreSQL connection string |
| `GEMINI_API_KEY` | Google Gemini API key for AI features |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `EMAIL_HOST_USER` | Gmail address for SMTP |
| `EMAIL_HOST_PASSWORD` | Gmail app password |

## 📜 License

This project is open source and available under the [MIT License](LICENSE).

## 👤 Author

**Ayush Garg** — [GitHub](https://github.com/ayushga8)
