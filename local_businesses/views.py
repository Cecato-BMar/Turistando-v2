from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Avg
from django.contrib.auth.models import User
from .models import Business, BusinessCategory, BusinessPhoto, BusinessHours, Review, BusinessPlan, Booking, TimeSlot, Notification, PlanUpgradeRequest
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
    
    # Verificar limite de negócios baseado no plano do usuário
    user_businesses = request.user.businesses.all()
    
    # Definir limites por plano (valores padrão)
    max_businesses = 1  # Free plan
    
    # Verificar se o usuário tem algum negócio com plano Pro ou Premium
    user_plans = BusinessPlan.objects.filter(business__user=request.user)
    if user_plans.filter(plan_type='premium').exists():
        max_businesses = 10
    elif user_plans.filter(plan_type='pro').exists():
        max_businesses = 3
    elif user_plans.filter(plan_type='free').exists():
        max_businesses = 1
    
    # Verificar se o usuário atingiu o limite de negócios
    if user_businesses.count() >= max_businesses:
        messages.error(request, f'Você atingiu o limite de {max_businesses} negócios para seu plano atual. '
                                f'Faça um upgrade para cadastrar mais negócios.')
        return redirect('local_businesses:business_list')
    
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
                max_photos=1,
                max_businesses=1
            )
            
            messages.success(request, 'Negócio registrado com sucesso!')
            return redirect('local_businesses:business_dashboard')
    else:
        form = BusinessRegistrationForm()
    
    context = {
        'form': form,
        'max_businesses': max_businesses,
        'current_businesses': user_businesses.count(),
    }
    return render(request, 'local_businesses/register.html', context)

@login_required
def business_dashboard(request):
    """Painel do comércio/serviço"""
    # Obter todos os negócios do usuário
    user_businesses = request.user.businesses.all()
    
    # Se o usuário não tem negócios, redirecionar para registro
    if not user_businesses.exists():
        messages.info(request, 'Você ainda não possui nenhum negócio cadastrado.')
        return redirect('local_businesses:register_business')
    
    # Verificar se foi selecionado um negócio específico
    business_id = request.GET.get('business_id')
    if business_id:
        business = get_object_or_404(Business, id=business_id, user=request.user)
    else:
        # Para manter compatibilidade, usar o primeiro negócio como principal
        business = user_businesses.first()
    
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
    
    # Contar avaliações e reservas totais
    total_reviews = business.reviews.count()
    total_bookings = business.bookings.count()
    
    # Obter solicitações de upgrade pendentes
    pending_upgrades = PlanUpgradeRequest.objects.filter(business=business, status='pending')
    
    # Definir limites por plano (valores padrão)
    max_businesses = 1  # Free plan
    
    # Verificar se o usuário tem algum negócio com plano Pro ou Premium
    user_plans = BusinessPlan.objects.filter(business__user=request.user)
    if user_plans.filter(plan_type='premium').exists():
        max_businesses = 10
    elif user_plans.filter(plan_type='pro').exists():
        max_businesses = 3
    elif user_plans.filter(plan_type='free').exists():
        max_businesses = 1
    
    context = {
        'business': business,
        'businesses': user_businesses,
        'business_plan': business_plan,
        'photo_count': photo_count,
        'recent_bookings': recent_bookings,
        'avg_rating': avg_rating,
        'pending_bookings_count': pending_bookings_count,
        'unread_notifications_count': unread_notifications_count,
        'total_reviews': total_reviews,
        'total_bookings': total_bookings,
        'pending_upgrades': pending_upgrades,
        'max_businesses': max_businesses,
        'current_businesses': user_businesses.count(),
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
    # Verificar se foi selecionado um negócio específico
    business_id = request.GET.get('business_id')
    if business_id:
        business = get_object_or_404(Business, id=business_id, user=request.user)
    else:
        # Usar o primeiro negócio do usuário
        business = get_object_or_404(Business, user=request.user)
    
    business_plan, created = BusinessPlan.objects.get_or_create(business=business)
    
    # Obter planos disponíveis do sistema de billing
    available_plans = Plan.objects.all()
    
    if request.method == 'POST':
        plan_type = request.POST.get('plan_type')
        if plan_type in ['free', 'pro', 'premium']:
            # Verificar se o plano selecionado é pago
            if plan_type in ['pro', 'premium']:
                # Redirecionar para a página de checkout
                request.session['selected_plan_type'] = plan_type
                request.session['selected_business_id'] = business.id
                return redirect('local_businesses:checkout')
            else:
                # Atualizar plano gratuito diretamente
                business_plan.plan_type = plan_type
                
                # Definir limites com base no plano
                if plan_type == 'free':
                    business_plan.max_photos = 1
                    business_plan.max_businesses = 1
                    business_plan.can_show_menu = False
                    business_plan.can_show_website = False
                    business_plan.can_show_whatsapp = False
                    business_plan.is_featured = False
                elif plan_type == 'pro':
                    business_plan.max_photos = 5
                    business_plan.max_businesses = 3
                    business_plan.can_show_menu = False
                    business_plan.can_show_website = True
                    business_plan.can_show_whatsapp = True
                    business_plan.is_featured = False
                elif plan_type == 'premium':
                    business_plan.max_photos = 10  # ou ilimitado
                    business_plan.max_businesses = 10
                    business_plan.can_show_menu = True
                    business_plan.can_show_website = True
                    business_plan.can_show_whatsapp = True
                    business_plan.is_featured = True
                    
                business_plan.save()
                messages.success(request, f'Plano atualizado para {business_plan.get_plan_type_display()}!')
                return redirect('local_businesses:manage_plan')
    
    # Obter todos os negócios do usuário para o seletor
    user_businesses = request.user.businesses.all()
    
    context = {
        'business': business,
        'businesses': user_businesses,
        'business_plan': business_plan,
        'available_plans': available_plans,
    }
    return render(request, 'local_businesses/manage_plan.html', context)

@login_required
def checkout(request):
    """Página de checkout para planos pagos"""
    # Verificar se há um negócio selecionado na sessão
    selected_business_id = request.session.get('selected_business_id')
    if selected_business_id:
        business = get_object_or_404(Business, id=selected_business_id, user=request.user)
    else:
        business = get_object_or_404(Business, user=request.user)
    
    # Verificar se há um plano selecionado na sessão
    selected_plan_type = request.session.get('selected_plan_type')
    if not selected_plan_type or selected_plan_type not in ['pro', 'premium']:
        messages.error(request, 'Nenhum plano selecionado.')
        return redirect('local_businesses:manage_plan')
    
    # Obter o plano correspondente do sistema de billing
    # Mapear planos locais para planos de billing
    plan_mapping = {
        'pro': 'Profissional',
        'premium': 'Empresarial'
    }
    
    try:
        billing_plan = Plan.objects.get(name=plan_mapping[selected_plan_type])
    except Plan.DoesNotExist:
        messages.error(request, 'Plano não encontrado.')
        return redirect('local_businesses:manage_plan')
    
    if request.method == 'POST':
        # Processar pagamento (simulação)
        # Aqui você integraria com um gateway de pagamento real
        payment_method = request.POST.get('payment_method')
        card_number = request.POST.get('card_number')
        
        # Simular processamento de pagamento
        if payment_method and card_number:
            # Criar uma solicitação de upgrade de plano em vez de aplicar diretamente
            upgrade_request = PlanUpgradeRequest.objects.create(
                business=business,
                requested_plan=selected_plan_type,
                billing_plan=billing_plan,
                payment_method=payment_method,
                payment_details=f"Cartão terminado em {card_number[-4:]}" if card_number else ""
            )
            
            # Criar notificação para o negócio
            Notification.objects.create(
                business=business,
                notification_type='plan_upgrade',
                title='Solicitação de Upgrade de Plano',
                message=f'Sua solicitação para o plano {upgrade_request.get_requested_plan_display()} foi recebida e está aguardando aprovação.'
            )
            
            # Limpar a sessão
            if 'selected_plan_type' in request.session:
                del request.session['selected_plan_type']
            if 'selected_business_id' in request.session:
                del request.session['selected_business_id']
            
            messages.info(request, f'Sua solicitação para o plano {upgrade_request.get_requested_plan_display()} foi recebida e está aguardando aprovação.')
            return redirect('local_businesses:business_dashboard')
        else:
            messages.error(request, 'Por favor, preencha todos os campos de pagamento.')
    
    context = {
        'business': business,
        'selected_plan_type': selected_plan_type,
        'billing_plan': billing_plan,
    }
    return render(request, 'local_businesses/checkout.html', context)

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
    
    # Marcar todas as notificações como lidas
    business.notifications.filter(is_read=False).update(is_read=True)
    
    context = {
        'business': business,
        'notifications': notifications,
    }
    return render(request, 'local_businesses/manage_notifications.html', context)

@login_required
def get_available_times(request, business_id, date_str):
    """API para obter horários disponíveis para reserva"""
    business = get_object_or_404(Business, id=business_id)
    
    # Esta é uma implementação simplificada
    # Em uma aplicação real, você precisaria verificar os horários já reservados
    available_times = []
    time_slots = business.time_slots.filter(is_active=True)
    
    for slot in time_slots:
        # Adicionar horários disponíveis (simplificado)
        available_times.append({
            'start_time': slot.start_time.strftime('%H:%M'),
            'end_time': slot.end_time.strftime('%H:%M'),
        })
    
    return JsonResponse({'available_times': available_times})

# Import necessário para o formulário TimeSlotForm
from .forms import TimeSlotForm

@login_required
def admin_dashboard(request):
    """Painel administrativo para controle total do sistema"""
    # Verificar se o usuário é superusuário
    if not request.user.is_superuser:
        messages.error(request, 'Acesso negado. Apenas administradores podem acessar esta página.')
        return redirect('home')
    
    # Obter estatísticas do sistema
    total_businesses = Business.objects.count()
    total_users = User.objects.count()
    total_reviews = Review.objects.count()
    total_bookings = Booking.objects.count()
    
    # Obter solicitações de upgrade pendentes
    pending_upgrades = PlanUpgradeRequest.objects.filter(status='pending').select_related('business', 'billing_plan')
    
    # Obter últimos negócios registrados
    latest_businesses = Business.objects.order_by('-created_at')[:5]
    
    # Obter últimos usuários registrados
    latest_users = User.objects.order_by('-date_joined')[:5]
    
    # Obter todos os usuários com seus negócios e planos
    # Agora um usuário pode ter múltiplos negócios, então precisamos ajustar a lógica
    users_with_plans = User.objects.prefetch_related('businesses__businessplan').order_by('username')
    
    context = {
        'total_businesses': total_businesses,
        'total_users': total_users,
        'total_reviews': total_reviews,
        'total_bookings': total_bookings,
        'pending_upgrades': pending_upgrades,
        'latest_businesses': latest_businesses,
        'latest_users': latest_users,
        'users_with_plans': users_with_plans,
    }
    return render(request, 'local_businesses/admin_dashboard.html', context)

@login_required
def approve_upgrade(request, upgrade_id):
    """Aprovar uma solicitação de upgrade de plano"""
    # Verificar se o usuário é superusuário
    if not request.user.is_superuser:
        messages.error(request, 'Acesso negado.')
        return redirect('home')
    
    # Obter a solicitação de upgrade
    upgrade_request = get_object_or_404(PlanUpgradeRequest, id=upgrade_id, status='pending')
    
    if request.method == 'POST':
        # Aprovar o upgrade
        upgrade_request.status = 'approved'
        upgrade_request.approved_by = request.user
        upgrade_request.approved_at = timezone.now()
        upgrade_request.save()
        
        # Atualizar o plano do negócio
        business_plan, created = BusinessPlan.objects.get_or_create(business=upgrade_request.business)
        business_plan.plan_type = upgrade_request.requested_plan
        
        # Definir limites com base no plano
        if upgrade_request.requested_plan == 'free':
            business_plan.max_photos = 1
            business_plan.max_businesses = 1
            business_plan.can_show_menu = False
            business_plan.can_show_website = False
            business_plan.can_show_whatsapp = False
            business_plan.is_featured = False
        elif upgrade_request.requested_plan == 'pro':
            business_plan.max_photos = 5
            business_plan.max_businesses = 3
            business_plan.can_show_menu = False
            business_plan.can_show_website = True
            business_plan.can_show_whatsapp = True
            business_plan.is_featured = False
        elif upgrade_request.requested_plan == 'premium':
            business_plan.max_photos = 10  # ou ilimitado
            business_plan.max_businesses = 10
            business_plan.can_show_menu = True
            business_plan.can_show_website = True
            business_plan.can_show_whatsapp = True
            business_plan.is_featured = True
            
        business_plan.save()
        
        # Criar notificação para o negócio
        Notification.objects.create(
            business=upgrade_request.business,
            notification_type='plan_upgrade_approved',
            title='Upgrade de Plano Aprovado',
            message=f'Seu upgrade para o plano {upgrade_request.get_requested_plan_display()} foi aprovado com sucesso!'
        )
        
        messages.success(request, f'Upgrade para o plano {upgrade_request.get_requested_plan_display()} aprovado com sucesso!')
        return redirect('local_businesses:admin_dashboard')
    
    context = {
        'upgrade_request': upgrade_request,
    }
    return render(request, 'local_businesses/approve_upgrade.html', context)

@login_required
def reject_upgrade(request, upgrade_id):
    """Rejeitar uma solicitação de upgrade de plano"""
    # Verificar se o usuário é superusuário
    if not request.user.is_superuser:
        messages.error(request, 'Acesso negado.')
        return redirect('home')
    
    # Obter a solicitação de upgrade
    upgrade_request = get_object_or_404(PlanUpgradeRequest, id=upgrade_id, status='pending')
    
    if request.method == 'POST':
        rejection_reason = request.POST.get('rejection_reason', '')
        
        # Rejeitar o upgrade
        upgrade_request.status = 'rejected'
        upgrade_request.approved_by = request.user
        upgrade_request.approved_at = timezone.now()
        upgrade_request.save()
        
        # Criar notificação para o negócio
        Notification.objects.create(
            business=upgrade_request.business,
            notification_type='plan_upgrade_rejected',
            title='Upgrade de Plano Rejeitado',
            message=f'Seu upgrade para o plano {upgrade_request.get_requested_plan_display()} foi rejeitado. Motivo: {rejection_reason}'
        )
        
        messages.success(request, f'Upgrade para o plano {upgrade_request.get_requested_plan_display()} rejeitado.')
        return redirect('local_businesses:admin_dashboard')
    
    context = {
        'upgrade_request': upgrade_request,
    }
    return render(request, 'local_businesses/reject_upgrade.html', context)

# Import necessário para timezone
from django.utils import timezone
