"""
URL configuration for task_manager project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from tasks import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path("create_team/", views.create_team, name="create_team"),
    path("create_invite/", views.InviteView.as_view(), name="create_invite"),
    path("remove_member/", views.remove_member, name="remove_member"),
    path("press_invite/", views.press_invite, name="press_invite"),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('log_in/', views.LogInView.as_view(), name='log_in'),
    path('log_out/', views.log_out, name='log_out'),
    path('password/', views.PasswordView.as_view(), name='password'),
    path('profile/', views.ProfileUpdateView.as_view(), name='profile'),
    path('sign_up/', views.SignUpView.as_view(), name='sign_up'),
    path('task_create/', views.CreateTaskView.as_view(), name='task_create'),
    path('task_search/', views.task_search, name='task_search'),
    path('task_delete/<str:task_name>/', views.DeleteTaskView.as_view(), name='task_delete'),
    path('task_update/<str:task_name>/', views.TaskView.as_view(), name = 'task_update'),
    path('lane_delete/<int:lane_id>/', views.DeleteLaneView.as_view(), name='lane_delete'),
    path('move_lane_left/<int:lane_id>/', views.move_lane_left, name='move_lane_left'),
    path('move_lane_right/<int:lane_id>/', views.move_lane_right, name='move_lane_right'),
    path('my_teams/', views.my_teams, name="my_teams"),
    # path('add_lane/', views.add_lane, name="add_lane")
    path('task/<str:task_name>/move-left/', views.move_task_left, name='move_task_left'),
    path('task/<str:task_name>/move-right/', views.move_task_right, name='move_task_right'),
]
