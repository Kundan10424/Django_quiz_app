QuizMaster - Quiz App (Django, beginner level)
==============================================

FEATURES
- Register / Login / Logout
- Dashboard: quizzes taken, average + best score, passed count, resume unfinished quiz
- Quiz list with search + category filter + pagination
- Quiz detail page (rules, previous attempts)
- Quiz page with countdown timer (auto-submits when time ends)
- Result page: score ring, pass/fail, full answer review with explanations
- My Attempts history
- Leaderboard per quiz (best attempt of each user)
- Quiz content is managed from the Django admin (staff users see "Manage Quizzes")

FOLDER STRUCTURE
quiz_app/                  <- project root (run commands here)
  manage.py
  requirements.txt
  config/                  <- project settings (settings.py, urls.py, wsgi.py)
  quiz/                    <- the app (models, views, forms, urls, admin)
    management/commands/seed_quiz.py   <- loads 3 sample quizzes
  templates/               <- base layouts, login/register, quiz pages
  static/css/style.css     <- all styling

HOW TO RUN
1. python -m venv venv
2. Activate it:   Windows: venv\Scripts\activate     Mac/Linux: source venv/bin/activate
3. pip install -r requirements.txt
4. python manage.py makemigrations quiz
5. python manage.py migrate
6. python manage.py seed_quiz              (adds 3 sample quizzes; safe to run again)
7. python manage.py createsuperuser        (this user can add quizzes in /admin/)
8. python manage.py runserver
9. Open http://127.0.0.1:8000/

ADDING YOUR OWN QUIZ (admin)
1. Log in at /admin/ with the superuser account.
2. Quizzes -> Add quiz (set time limit and pass %).
3. Questions -> Add question, pick the quiz, then fill the choices below and tick exactly ONE correct choice.

PRODUCTION NOTES
- Set environment variables: DJANGO_SECRET_KEY, DJANGO_DEBUG=0, DJANGO_ALLOWED_HOSTS=yourdomain.com
- Run: python manage.py collectstatic   (files go to staticfiles/)
- Serve with gunicorn/uwsgi and serve static files with nginx or WhiteNoise.
