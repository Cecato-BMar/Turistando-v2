from django.urls import path
from . import views

app_name = 'billing'
urlpatterns = [
    path('', views.billing_home, name='home'),
    path('plans/', views.plans, name='plans'),
    path('credits/', views.credits, name='credits'),
]