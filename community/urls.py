from django.urls import path
from . import views

app_name = 'community'
urlpatterns = [
    path('', views.community_home, name='home'),
    path('use_cases/', views.use_cases, name='use_cases'),
    path('events/', views.events, name='events'),
]