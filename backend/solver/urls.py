from django.urls import path
from . import views

urlpatterns = [
    path('auth/register/', views.register_view),
    path('auth/login/', views.login_view),
    path('auth/logout/', views.logout_view),
    path('auth/me/', views.me_view),
    path('tasks/', views.tasks_view),
    path('tasks/<int:pk>/cancel/', views.cancel_task_view),
    path('monitor/', views.monitor_view),
]