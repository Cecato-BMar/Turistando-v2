from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import Profile
from tasks.models import Task
from local_businesses.models import Business, BusinessCategory
from django.db.models import Avg

def home(request):
    # Obter comércios em destaque (simulação)
    featured_businesses = Business.objects.filter(is_active=True, businessplan__is_featured=True)[:3]
    
    # Adicionar média de avaliações
    featured_businesses = featured_businesses.annotate(avg_rating=Avg('reviews__rating'))
    
    # Obter categorias
    categories = BusinessCategory.objects.all()[:8]
    
    # Obter comércios próximos (simulação)
    nearby_businesses = Business.objects.filter(is_active=True).annotate(
        avg_rating=Avg('reviews__rating')
    ).order_by('-businessplan__is_featured', '-avg_rating')[:6]
    
    context = {
        'featured_businesses': featured_businesses,
        'categories': categories,
        'nearby_businesses': nearby_businesses,
    }
    return render(request, 'dashboard/home.html', context)

@login_required
def dashboard_home(request):
    profile = Profile.objects.get(user=request.user)
    tasks = Task.objects.filter(assigned_to=request.user)[:5]
    
    context = {
        'profile': profile,
        'tasks': tasks,
    }
    return render(request, 'dashboard/dashboard.html', context)

@login_required
def settings(request):
    profile = Profile.objects.get(user=request.user)
    
    if request.method == 'POST':
        # Atualizar configurações do perfil
        profile.plan = request.POST.get('plan', profile.plan)
        profile.save()
        messages.success(request, 'Configurações atualizadas com sucesso!')
        return redirect('dashboard:settings')
    
    context = {
        'profile': profile,
    }
    return render(request, 'dashboard/settings.html', context)