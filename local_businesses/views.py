from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Avg
from .models import Business, BusinessCategory, BusinessPhoto, BusinessHours, Review, BusinessPlan, Booking, TimeSlot, Notification
from accounts.models import Profile
from billing.models import Plan
from .forms import BusinessRegistrationForm, BusinessEditForm, PhotoForm, BusinessHoursForm, ReviewForm, BookingForm

def business_list(request):
    """Lista todos os comércios e serviços"""
    businesses = Business.objects.filter(is_active=True).select_related('category', 'businessplan')
    
    # Adicionar média de avaliações
    businesses = businesses.annotate(avg_rating=Avg('reviews__rating'))
    
    # Filtros
    query = request.GET.get('q')
    category_id = request.GET.get('category')
    business_type = request.GET.get('type')
    
    if query:
        businesses = businesses.filter(name__icontains=query) | businesses.filter(description__icontains=query)
    
    if category_id:
        businesses = businesses.filter(category_id=category_id)
    
    if business_type:
        businesses = businesses.filter(business_type=business_type)
    
    categories = BusinessCategory.objects.all()
    
    context = {
        'businesses': businesses,
        'categories': categories,
    }
    return render(request, 'local_businesses/list.html', context)

def nearby_businesses(request):
    """Lista comércios e serviços próximos (simulação)"""
    # Esta função seria expandida para usar geolocalização real
    businesses = Business.objects.filter(is_active=True).select_related('category', 'businessplan')
    businesses = businesses.annotate(avg_rating=Avg('reviews__rating'))
    
    # Ordenar por destaque (premium primeiro)
    businesses = businesses.order_by('-businessplan__is_featured', '-avg_rating')
    
    # Se tivermos coordenadas do usuário, ordenar por proximidade
    user_lat = request.GET.get('lat')
    user_lng = request.GET.get('lng')
    
    categories = BusinessCategory.objects.all()
    
    context = {
        'businesses': businesses,
        'categories': categories,
        'nearby': True,
        'user_lat': user_lat,
        'user_lng': user_lng,
    }
    return render(request, 'local_businesses/list.html', context)

def business_detail(request, business_id):
    """Detalhes de um comércio/serviço específico"""
    business = get_object_or_404(Business, id=business_id, is_active=True)
    photos = business.photos.all()
    hours = business.hours.all()
    reviews = business.reviews.all().order_by('-created_at')
    
    # Calcular média de avaliações
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    
    # Verificar se o usuário já fez uma avaliação
    user_review = None
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()
    
    context = {
        'business': business,
        'photos': photos,
        'hours': hours,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'user_review': user_review,
    }
    return render(request, 'local_businesses/detail.html', context)

@login_required
def register_business(request):
    """Registro de novo comércio/serviço"""
    profile = get_object_or_404(Profile, user=request.user)
    
    # Verificar se o usuário já tem um negócio registrado
    if hasattr(request.user, 'business'):
        messages.info(request, 'Você já possui um negócio registrado.')
        return redirect('local_businesses:business_dashboard')
    
    if request.method == 'POST':
        form = BusinessRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            business = form.save(commit=False)
            business.user = request.user
            business.save()
            
            # Criar plano gratuito por padrão
            BusinessPlan.objects.create(
                business=business,
                plan_type='free',
                max_photos=1
            )
            
            messages.success(request, 'Negócio registrado com sucesso!')
            return redirect('local_businesses:business_dashboard')
    else:
        form = BusinessRegistrationForm()
    
    context = {
        'form': form,
    }
    return render(request, 'local_businesses/register.html', context)

@login_required
def business_dashboard(request):
    """Painel do comércio/serviço"""
    business = get_object_or_404(Business, user=request.user)
    business_plan = getattr(business, 'businessplan', None)
    
    # Contar fotos atuais
    photo_count = business.photos.count()
    
    # Obter reservas recentes
    recent_bookings = business.bookings.filter(status='pending')[:5]
    
    # Calcular média de avaliações
    from django.db.models import Avg
    avg_rating = business.reviews.aggregate(Avg('rating'))['rating__avg']
    
    # Contar reservas pendentes
    pending_bookings_count = business.bookings.filter(status='pending').count()
    
    # Contar notificações não lidas
    unread_notifications_count = business.notifications.filter(is_read=False).count()
    
    context = {
        'business': business,
        'business_plan': business_plan,
        'photo_count': photo_count,
        'recent_bookings': recent_bookings,
        'avg_rating': avg_rating,
        'pending_bookings_count': pending_bookings_count,
        'unread_notifications_count': unread_notifications_count,
    }
    return render(request, 'local_businesses/dashboard.html', context)

@login_required
def edit_business(request):
    """Editar informações do comércio/serviço"""
    business = get_object_or_404(Business, user=request.user)
    
    if request.method == 'POST':
        form = BusinessEditForm(request.POST, instance=business)
        if form.is_valid():
            form.save()
            messages.success(request, 'Informações atualizadas com sucesso!')
            return redirect('local_businesses:business_dashboard')
    else:
        form = BusinessEditForm(instance=business)
    
    context = {
        'form': form,
        'business': business,
    }
    return render(request, 'local_businesses/edit_business.html', context)

@login_required
def manage_photos(request):
    """Gerenciar fotos do comércio/serviço"""
    business = get_object_or_404(Business, user=request.user)
    business_plan = getattr(business, 'businessplan', None)
    
    # Verificar limite de fotos
    max_photos = business_plan.max_photos if business_plan else 1
    current_photos = business.photos.count()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'delete':
            # Excluir foto
            photo_id = request.POST.get('photo_id')
            photo = get_object_or_404(BusinessPhoto, id=photo_id, business=business)
            photo.delete()
            messages.success(request, 'Foto excluída com sucesso!')
            return redirect('local_businesses:manage_photos')
        elif action == 'set_primary':
            # Definir foto principal
            photo_id = request.POST.get('photo_id')
            photo = get_object_or_404(BusinessPhoto, id=photo_id, business=business)
            
            # Remover marcação de principal de outras fotos
            BusinessPhoto.objects.filter(business=business, is_primary=True).update(is_primary=False)
            
            # Marcar esta foto como principal
            photo.is_primary = True
            photo.save()
            messages.success(request, 'Foto definida como principal!')
            return redirect('local_businesses:manage_photos')
        else:
            # Adicionar nova foto
            form = PhotoForm(request.POST, request.FILES)
            if form.is_valid():
                if current_photos >= max_photos:
                    messages.error(request, f'Você atingiu o limite de {max_photos} fotos para seu plano.')
                else:
                    photo = form.save(commit=False)
                    photo.business = business
                    
                    # Se for a primeira foto, definir como principal
                    if current_photos == 0:
                        photo.is_primary = True
                    
                    photo.save()
                    messages.success(request, 'Foto adicionada com sucesso!')
                    return redirect('local_businesses:manage_photos')
            else:
                # Formulário inválido, continuar para mostrar erros
                pass
    else:
        form = PhotoForm()
    
    photos = business.photos.all()
    
    context = {
        'form': form,
        'business': business,
        'photos': photos,
        'max_photos': max_photos,
        'current_photos': current_photos,
    }
    return render(request, 'local_businesses/manage_photos.html', context)

@login_required
def manage_hours(request):
    """Gerenciar horários de funcionamento"""
    business = get_object_or_404(Business, user=request.user)
    hours = business.hours.all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'delete':
            # Excluir horário
            hour_id = request.POST.get('hour_id')
            hour = get_object_or_404(BusinessHours, id=hour_id, business=business)
            hour.delete()
            messages.success(request, 'Horário excluído com sucesso!')
            return redirect('local_businesses:manage_hours')
        else:
            # Adicionar novo horário
            form = BusinessHoursForm(request.POST)
            if form.is_valid():
                # Verificar se já existe um horário para este dia
                day_of_week = form.cleaned_data['day_of_week']
                if business.hours.filter(day_of_week=day_of_week).exists():
                    messages.error(request, f'Já existe um horário cadastrado para {form.instance.get_day_of_week_display()}.')
                else:
                    hour = form.save(commit=False)
                    hour.business = business
                    hour.save()
                    messages.success(request, 'Horário adicionado com sucesso!')
                    return redirect('local_businesses:manage_hours')
            else:
                # Formulário inválido, continuar para mostrar erros
                pass
    else:
        form = BusinessHoursForm()
    
    context = {
        'form': form,
        'business': business,
        'hours': hours,
    }
    return render(request, 'local_businesses/manage_hours.html', context)

@login_required
def manage_plan(request):
    """Gerenciar plano do comércio/serviço"""
    business = get_object_or_404(Business, user=request.user)
    business_plan, created = BusinessPlan.objects.get_or_create(business=business)
    
    # Obter planos disponíveis do sistema de billing
    available_plans = Plan.objects.all()
    
    if request.method == 'POST':
        plan_type = request.POST.get('plan_type')
        if plan_type in ['free', 'pro', 'premium']:
            # Atualizar plano
            business_plan.plan_type = plan_type
            
            # Definir limites com base no plano
            if plan_type == 'free':
                business_plan.max_photos = 1
                business_plan.can_show_menu = False
                business_plan.can_show_website = False
                business_plan.can_show_whatsapp = False
                business_plan.is_featured = False
            elif plan_type == 'pro':
                business_plan.max_photos = 5
                business_plan.can_show_menu = False
                business_plan.can_show_website = True
                business_plan.can_show_whatsapp = True
                business_plan.is_featured = False
            elif plan_type == 'premium':
                business_plan.max_photos = 10  # ou ilimitado
                business_plan.can_show_menu = True
                business_plan.can_show_website = True
                business_plan.can_show_whatsapp = True
                business_plan.is_featured = True
                
            business_plan.save()
            messages.success(request, f'Plano atualizado para {business_plan.get_plan_type_display()}!')
            return redirect('local_businesses:manage_plan')
    
    context = {
        'business': business,
        'business_plan': business_plan,
        'available_plans': available_plans,
    }
    return render(request, 'local_businesses/manage_plan.html', context)

@login_required
def add_review(request, business_id):
    """Adicionar avaliação a um comércio/serviço"""
    business = get_object_or_404(Business, id=business_id)
    
    # Verificar se o usuário já fez uma avaliação
    existing_review = Review.objects.filter(business=business, user=request.user).first()
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.business = business
            review.user = request.user
            
            if existing_review:
                # Atualizar avaliação existente
                existing_review.rating = review.rating
                existing_review.comment = review.comment
                existing_review.save()
                messages.success(request, 'Avaliação atualizada com sucesso!')
            else:
                # Criar nova avaliação
                review.save()
                # Create notification for business owner
                Notification.objects.create(
                    business=business,
                    user=request.user,
                    notification_type='review',
                    title=f'Nova avaliação de {request.user.get_full_name() or request.user.username}',
                    message=f'{request.user.get_full_name() or request.user.username} deixou uma avaliação de {review.rating} estrelas.'
                )
                messages.success(request, 'Avaliação adicionada com sucesso!')
            
            return redirect('local_businesses:business_detail', business_id=business.id)
    else:
        # Preencher formulário com avaliação existente, se houver
        if existing_review:
            form = ReviewForm(instance=existing_review)
        else:
            form = ReviewForm()
    
    context = {
        'form': form,
        'business': business,
        'existing_review': existing_review,
    }
    return render(request, 'local_businesses/add_review.html', context)

@login_required
def book_service(request, business_id):
    """Reservar um serviço"""
    business = get_object_or_404(Business, id=business_id)
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.business = business
            booking.user = request.user
            booking.save()
            
            # Create notification for business owner
            Notification.objects.create(
                business=business,
                user=request.user,
                notification_type='booking',
                title=f'Nova reserva de {request.user.get_full_name() or request.user.username}',
                message=f'{request.user.get_full_name() or request.user.username} solicitou uma reserva para {booking.service_name} no dia {booking.booking_date} às {booking.booking_time}.'
            )
            
            messages.success(request, 'Reserva solicitada com sucesso! O estabelecimento entrará em contato para confirmação.')
            return redirect('local_businesses:business_detail', business_id=business.id)
    else:
        form = BookingForm()
    
    context = {
        'form': form,
        'business': business,
    }
    return render(request, 'local_businesses/book_service.html', context)

@login_required
def manage_bookings(request):
    """Gerenciar reservas (para comerciantes)"""
    business = get_object_or_404(Business, user=request.user)
    bookings = business.bookings.all().order_by('-booking_date', '-booking_time')
    
    if request.method == 'POST':
        booking_id = request.POST.get('booking_id')
        action = request.POST.get('action')
        
        booking = get_object_or_404(Booking, id=booking_id, business=business)
        
        if action == 'confirm':
            booking.status = 'confirmed'
            # Create notification for user
            Notification.objects.create(
                business=business,
                user=request.user,
                notification_type='booking_update',
                title=f'Reserva confirmada: {booking.service_name}',
                message=f'Sua reserva para {booking.service_name} no dia {booking.booking_date} às {booking.booking_time} foi confirmada.'
            )
            messages.success(request, f'Reserva para {booking.user.get_full_name() or booking.user.username} confirmada!')
        elif action == 'cancel':
            booking.status = 'cancelled'
            # Create notification for user
            Notification.objects.create(
                business=business,
                user=request.user,
                notification_type='booking_update',
                title=f'Reserva cancelada: {booking.service_name}',
                message=f'Sua reserva para {booking.service_name} no dia {booking.booking_date} às {booking.booking_time} foi cancelada.'
            )
            messages.info(request, f'Reserva para {booking.user.get_full_name() or booking.user.username} cancelada.')
        elif action == 'complete':
            booking.status = 'completed'
            # Create notification for user
            Notification.objects.create(
                business=business,
                user=request.user,
                notification_type='booking_update',
                title=f'Reserva concluída: {booking.service_name}',
                message=f'Sua reserva para {booking.service_name} no dia {booking.booking_date} às {booking.booking_time} foi concluída. Obrigado!'
            )
            messages.success(request, f'Reserva para {booking.user.get_full_name() or booking.user.username} marcada como concluída.')
        
        booking.save()
        return redirect('local_businesses:manage_bookings')
    
    context = {
        'business': business,
        'bookings': bookings,
    }
    return render(request, 'local_businesses/manage_bookings.html', context)

@login_required
def manage_time_slots(request):
    """Gerenciar horários disponíveis para reserva (para comerciantes)"""
    business = get_object_or_404(Business, user=request.user)
    time_slots = business.time_slots.all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'delete':
            # Excluir horário
            slot_id = request.POST.get('slot_id')
            slot = get_object_or_404(TimeSlot, id=slot_id, business=business)
            slot.delete()
            messages.success(request, 'Horário excluído com sucesso!')
            return redirect('local_businesses:manage_time_slots')
        else:
            # Adicionar novo horário
            form = TimeSlotForm(request.POST)
            if form.is_valid():
                slot = form.save(commit=False)
                slot.business = business
                slot.save()
                messages.success(request, 'Horário adicionado com sucesso!')
                return redirect('local_businesses:manage_time_slots')
            else:
                # Formulário inválido, continuar para mostrar erros
                pass
    else:
        form = TimeSlotForm()
    
    context = {
        'business': business,
        'time_slots': time_slots,
        'form': form,
    }
    return render(request, 'local_businesses/manage_time_slots.html', context)

@login_required
def manage_notifications(request):
    """Gerenciar notificações (para comerciantes)"""
    business = get_object_or_404(Business, user=request.user)
    notifications = business.notifications.all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'mark_as_read':
            # Marcar notificação como lida
            notification_id = request.POST.get('notification_id')
            notification = get_object_or_404(Notification, id=notification_id, business=business)
            notification.is_read = True
            notification.save()
            messages.success(request, 'Notificação marcada como lida!')
        elif action == 'mark_all_as_read':
            # Marcar todas as notificações como lidas
            notifications.filter(is_read=False).update(is_read=True)
            messages.success(request, 'Todas as notificações foram marcadas como lidas!')
        elif action == 'delete':
            # Excluir notificação
            notification_id = request.POST.get('notification_id')
            notification = get_object_or_404(Notification, id=notification_id, business=business)
            notification.delete()
            messages.success(request, 'Notificação excluída com sucesso!')
        
        return redirect('local_businesses:manage_notifications')
    
    context = {
        'business': business,
        'notifications': notifications,
    }
    return render(request, 'local_businesses/manage_notifications.html', context)

def get_available_times(request, business_id, date_str):
    """Obter horários disponíveis para reserva"""
    business = get_object_or_404(Business, id=business_id)
    
    # Esta é uma implementação simplificada
    # Em uma aplicação real, você precisaria verificar:
    # 1. Horário de funcionamento do negócio naquele dia
    # 2. Reservas já existentes naquele dia
    # 3. Duração média dos serviços
    
    # Por enquanto, vamos retornar horários fixos
    available_times = [
        '09:00', '10:00', '11:00', '12:00',
        '14:00', '15:00', '16:00', '17:00'
    ]
    
    return JsonResponse({'available_times': available_times})