from django.contrib import admin
from .models import BusinessCategory, Business, BusinessPhoto, BusinessHours, Review, BusinessPlan, Booking

@admin.register(BusinessCategory)
class BusinessCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'created_at')
    search_fields = ('name',)

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'business_type', 'category', 'is_active', 'created_at')
    list_filter = ('business_type', 'category', 'is_active', 'created_at')
    search_fields = ('name', 'address')
    raw_id_fields = ('user',)

@admin.register(BusinessPhoto)
class BusinessPhotoAdmin(admin.ModelAdmin):
    list_display = ('business', 'is_primary', 'created_at')
    list_filter = ('is_primary', 'created_at')
    raw_id_fields = ('business',)

@admin.register(BusinessHours)
class BusinessHoursAdmin(admin.ModelAdmin):
    list_display = ('business', 'day_of_week', 'open_time', 'close_time', 'is_closed')
    list_filter = ('day_of_week', 'is_closed')
    raw_id_fields = ('business',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('business', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    raw_id_fields = ('business', 'user')

@admin.register(BusinessPlan)
class BusinessPlanAdmin(admin.ModelAdmin):
    list_display = ('business', 'plan_type', 'max_photos', 'expires_at')
    list_filter = ('plan_type', 'expires_at')
    raw_id_fields = ('business',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('business', 'user', 'service_name', 'booking_date', 'booking_time', 'status')
    list_filter = ('status', 'booking_date', 'created_at')
    raw_id_fields = ('business', 'user')
    search_fields = ('business__name', 'user__username', 'service_name')