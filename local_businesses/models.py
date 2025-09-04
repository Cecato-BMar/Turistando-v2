from django.db import models
from django.contrib.auth.models import User
from accounts.models import Profile
from billing.models import Plan

class BusinessCategory(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True)  # Classe do Font Awesome
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Business Categories"

class Business(models.Model):
    BUSINESS_TYPES = [
        ('commerce', 'Comércio'),
        ('service', 'Serviço'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    business_type = models.CharField(max_length=20, choices=BUSINESS_TYPES)
    category = models.ForeignKey(BusinessCategory, on_delete=models.SET_NULL, null=True, blank=True)
    address = models.CharField(max_length=300)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    whatsapp = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class BusinessPhoto(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='business_photos/')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.business.name} - Photo"

class BusinessHours(models.Model):
    DAYS_OF_WEEK = [
        ('monday', 'Segunda-feira'),
        ('tuesday', 'Terça-feira'),
        ('wednesday', 'Quarta-feira'),
        ('thursday', 'Quinta-feira'),
        ('friday', 'Sexta-feira'),
        ('saturday', 'Sábado'),
        ('sunday', 'Domingo'),
    ]
    
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='hours')
    day_of_week = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    open_time = models.TimeField()
    close_time = models.TimeField()
    is_closed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.business.name} - {self.get_day_of_week_display()}"

class Review(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.business.name} - {self.user.username} - {self.rating}"

class BusinessPlan(models.Model):
    PLAN_TYPES = [
        ('free', 'Gratuito'),
        ('pro', 'Pro'),
        ('premium', 'Premium'),
    ]
    
    business = models.OneToOneField(Business, on_delete=models.CASCADE)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, default='free')
    max_photos = models.IntegerField(default=1)  # 1 para free, 5 para pro, ilimitado para premium
    can_show_menu = models.BooleanField(default=False)  # Premium
    can_show_website = models.BooleanField(default=False)  # Pro e Premium
    can_show_whatsapp = models.BooleanField(default=False)  # Pro e Premium
    is_featured = models.BooleanField(default=False)  # Premium
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.business.name} - {self.get_plan_type_display()}"

# New model for bookings/reservations
class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('confirmed', 'Confirmado'),
        ('cancelled', 'Cancelado'),
        ('completed', 'Concluído'),
    ]
    
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service_name = models.CharField(max_length=200)  # Name of the service being booked
    booking_date = models.DateField()
    booking_time = models.TimeField()
    duration = models.IntegerField(default=60)  # Duration in minutes
    number_of_people = models.IntegerField(default=1)
    special_requests = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Booking for {self.business.name} by {self.user.username}"
    
    class Meta:
        ordering = ['-booking_date', '-booking_time']
        unique_together = ['business', 'booking_date', 'booking_time']

# Model for business time slots
class TimeSlot(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='time_slots')
    day_of_week = models.CharField(max_length=10, choices=BusinessHours.DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration = models.IntegerField(default=60)  # Duration in minutes
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.business.name} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"
    
    class Meta:
        ordering = ['day_of_week', 'start_time']

# Model for notifications
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('booking', 'Nova Reserva'),
        ('booking_update', 'Atualização de Reserva'),
        ('review', 'Nova Avaliação'),
        ('general', 'Geral'),
    ]
    
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='notifications')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # User who triggered the notification
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.business.name} - {self.title}"
    
    class Meta:
        ordering = ['-created_at']