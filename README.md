# QuizMaster

A modern, responsive quiz application built with Python Flask and Supabase.

## Features

### User Interface

- **Clean & Modern UI**: Built with a custom design system (Vanilla CSS) featuring responsive layouts, nice typography, and smooth transitions.
- **Dynamic Quizzes**: Users can take timed quizzes with support for image-based questions.
- **Real-time Feedback**: Immediate feedback on answers (if enabled) and detailed result breakdowns.
- **Mobile Friendly**: Fully responsive design that works seamlessly on desktop and mobile devices.

### Admin Dashboard

- **Quiz Management**: Create, edit, and delete quizzes.
- **Question Management**: Add questions with images, multiple options, and correct answers.
- **Result Tracking**: View leaderboard and detailed user responses.
- **Settings**: Configure quiz duration, reattempt limits, and score visibility.

## Tech Stack

- **Backend**: Python (Flask)
- **Database & Storage**: Supabase (PostgreSQL)
- **Frontend**: HTML5, Vanilla CSS, JavaScript, Jinja2 Templates
- **Authentication**: Custom Admin Login (Env-based) + User Session Management

## Setup Instructions

### Prerequisites

- Python 3.8+
- A Supabase account

### Installation

1. **Clone the repository** (or download the files):

   ```bash
   git clone https://github.com/pardhiv-sai/simple_quiz.git
   cd simple_quiz
   ```
2. **Create and activate a virtual environment**:

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```
3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```
4. **Database Setup**:

   - Log in to your Supabase dashboard.
   - Go to the **SQL Editor**.
   - Run the contents of `schema.sql` to create the necessary tables (`users`, `quizzes`, `questions`, `options`, `results`, `user_answers`).
5. **Environment Variables**:

   - Create a `.env` file in the root directory.
   - Add the following variables:
     ```env
     SUPABASE_URL=your_supabase_project_url
     SUPABASE_KEY=your_supabase_anon_key
     ADMIN_USERNAME=admin_username
     ADMIN_PASSWORD=your_secure_password
     FLASK_SECRET_KEY=your_secret_key
     ```
6. **Run the Application**:

   ```bash
   python app.py
   ```

   The app will start at `http://127.0.0.1:8000`.

## Usage

### Admin Access

- Navigate to `/login`.
- Enter the credentials defined in your `.env` file (`ADMIN_USERNAME` / `ADMIN_PASSWORD`).
- Access `/admin/dashboard` to manage the system.

### Taking a Quiz

- Navigate to `/` (Home).
- Enter a username to start (accounts are auto-created for new usernames).
- Select a quiz and begin!

## Project Structure

- `app.py`: Main Flask application logic.
- `db.py`: Supabase client initialization.
- `schema.sql`: Database schema definitions.
- `templates/`: HTML templates (Jinja2).
- `static/`: CSS styles and JavaScript files.
- `requirements.txt`: Python package dependencies.
