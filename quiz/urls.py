from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import LoginForm

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    # Authentication
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        authentication_form=LoginForm,
        redirect_authenticated_user=True), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),

    # Quizzes
    path('quizzes/', views.quiz_list, name='quiz_list'),
    path('quizzes/<int:pk>/', views.quiz_detail, name='quiz_detail'),
    path('quizzes/<int:pk>/start/', views.quiz_start, name='quiz_start'),

    # Attempts
    path('attempts/', views.attempt_history, name='attempt_history'),
    path('attempts/<int:pk>/', views.attempt_take, name='attempt_take'),
    path('attempts/<int:pk>/result/', views.attempt_result, name='attempt_result'),

    path('leaderboard/', views.leaderboard, name='leaderboard'),
]
