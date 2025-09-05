from django.urls import path
from . import views

app_name = 'local_businesses'

urlpatterns = [
    path('', views.business_list, name='business_list'),
    path('nearby/', views.nearby_businesses, name='nearby_businesses'),
    path('business/<int:business_id>/', views.business_detail, name='business_detail'),
    path('register/', views.register_business, name='register_business'),
    path('dashboard/', views.business_dashboard, name='business_dashboard'),
    path('dashboard/edit/', views.edit_business, name='edit_business'),
    path('dashboard/photos/', views.manage_photos, name='manage_photos'),
    path('dashboard/hours/', views.manage_hours, name='manage_hours'),
    path('dashboard/plan/', views.manage_plan, name='manage_plan'),
    path('dashboard/checkout/', views.checkout, name='checkout'),
    path('dashboard/time-slots/', views.manage_time_slots, name='manage_time_slots'),
    path('dashboard/notifications/', views.manage_notifications, name='manage_notifications'),
    path('review/<int:business_id>/', views.add_review, name='add_review'),
    path('book/<int:business_id>/', views.book_service, name='book_service'),
    path('dashboard/bookings/', views.manage_bookings, name='manage_bookings'),
    path('api/available-times/<int:business_id>/<str:date_str>/', views.get_available_times, name='available_times'),
    
    # URLs administrativas
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/approve/<int:upgrade_id>/', views.approve_upgrade, name='approve_upgrade'),
    path('admin/reject/<int:upgrade_id>/', views.reject_upgrade, name='reject_upgrade'),
]