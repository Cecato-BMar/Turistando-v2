import os
import django

# Configurar o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'manus_ai.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile, Team, TeamMembership
from tasks.models import Task
from billing.models import Plan
from community.models import UseCase, Event
from local_businesses.models import Business, BusinessCategory, BusinessPlan
from django.utils import timezone
from datetime import timedelta

def create_sample_data():
    # Criar usuários
    print("Criando usuários...")
    user1, created = User.objects.get_or_create(
        username='joao',
        defaults={
            'first_name': 'João',
            'last_name': 'Silva',
            'email': 'joao@example.com'
        }
    )
    
    if created:
        user1.set_password('senha123')
        user1.save()
        profile, _ = Profile.objects.get_or_create(user=user1)
        profile.credits = 1000
        profile.save()
    
    user2, created = User.objects.get_or_create(
        username='maria',
        defaults={
            'first_name': 'Maria',
            'last_name': 'Souza',
            'email': 'maria@example.com'
        }
    )
    
    if created:
        user2.set_password('senha123')
        user2.save()
        profile, _ = Profile.objects.get_or_create(user=user2)
        profile.credits = 1500
        profile.save()
    
    # Criar planos
    print("Criando planos...")
    Plan.objects.get_or_create(
        name='Básico',
        defaults={
            'price': 29.90,
            'credits_per_month': 1000,
            'max_scheduled_tasks': 5,
            'max_concurrent_tasks': 3
        }
    )
    
    Plan.objects.get_or_create(
        name='Profissional',
        defaults={
            'price': 79.90,
            'credits_per_month': 5000,
            'max_scheduled_tasks': 20,
            'max_concurrent_tasks': 10,
            'is_premium': True
        }
    )
    
    Plan.objects.get_or_create(
        name='Empresarial',
        defaults={
            'price': 199.90,
            'credits_per_month': 0,  # Ilimitado
            'max_scheduled_tasks': 0,  # Ilimitado
            'max_concurrent_tasks': 0,  # Ilimitado
            'is_premium': True
        }
    )
    
    # Criar categorias de negócios
    print("Criando categorias de negócios...")
    categories_data = [
        {'name': 'Restaurantes', 'icon': 'fa-utensils'},
        {'name': 'Hotéis', 'icon': 'fa-bed'},
        {'name': 'Lojas', 'icon': 'fa-shopping-cart'},
        {'name': 'Serviços', 'icon': 'fa-concierge-bell'},
        {'name': 'Turismo', 'icon': 'fa-mountain'},
        {'name': 'Transporte', 'icon': 'fa-bus'},
        {'name': 'Saúde', 'icon': 'fa-heartbeat'},
        {'name': 'Educação', 'icon': 'fa-graduation-cap'},
    ]
    
    for cat_data in categories_data:
        BusinessCategory.objects.get_or_create(
            name=cat_data['name'],
            defaults={'icon': cat_data['icon']}
        )
    
    # Obter categorias criadas
    restaurantes_cat = BusinessCategory.objects.get(name='Restaurantes')
    hoteis_cat = BusinessCategory.objects.get(name='Hotéis')
    lojas_cat = BusinessCategory.objects.get(name='Lojas')
    
    # Criar comércios e serviços de exemplo
    print("Criando comércios e serviços...")
    business1, created = Business.objects.get_or_create(
        user=user1,
        name='Restaurante Sabores da Terra',
        defaults={
            'description': 'Restaurante especializado em pratos da culinária brasileira, com ingredientes frescos e orgânicos.',
            'business_type': 'commerce',
            'category': restaurantes_cat,
            'address': 'Rua das Flores, 123, Centro',
            'phone': '(11) 99999-9999',
            'whatsapp': '5511999999999',
            'email': 'contato@saboresdaterra.com',
            'website': 'https://www.saboresdaterra.com',
            'is_active': True
        }
    )
    
    if created:
        # Criar plano para o negócio
        BusinessPlan.objects.create(
            business=business1,
            plan_type='premium',
            max_photos=10,
            can_show_menu=True,
            can_show_website=True,
            can_show_whatsapp=True,
            is_featured=True
        )
    
    business2, created = Business.objects.get_or_create(
        user=user2,
        name='Hotéis Vista Bela',
        defaults={
            'description': 'Hotéis com vista panorâmica para o mar, quartos confortáveis e excelente serviço.',
            'business_type': 'commerce',
            'category': hoteis_cat,
            'address': 'Avenida Beira Mar, 456, Praia',
            'phone': '(11) 88888-8888',
            'whatsapp': '5511888888888',
            'email': 'reservas@vistabela.com',
            'website': 'https://www.vistabela.com',
            'is_active': True
        }
    )
    
    if created:
        # Criar plano para o negócio
        BusinessPlan.objects.create(
            business=business2,
            plan_type='pro',
            max_photos=5,
            can_show_menu=False,
            can_show_website=True,
            can_show_whatsapp=True,
            is_featured=False
        )
    
    # Criar tarefas
    print("Criando tarefas...")
    Task.objects.get_or_create(
        title='Configurar ambiente de desenvolvimento',
        defaults={
            'description': 'Configurar o ambiente de desenvolvimento com Django e Python',
            'priority': 'high',
            'status': 'completed',
            'created_by': user1,
            'assigned_to': user1,
            'credits_used': 10
        }
    )
    
    Task.objects.get_or_create(
        title='Desenvolver API REST',
        defaults={
            'description': 'Desenvolver a API REST para o projeto Manus AI',
            'priority': 'medium',
            'status': 'in_progress',
            'created_by': user1,
            'assigned_to': user2,
            'credits_used': 25
        }
    )
    
    Task.objects.get_or_create(
        title='Criar interface do usuário',
        defaults={
            'description': 'Desenvolver a interface do usuário com React',
            'priority': 'medium',
            'status': 'pending',
            'created_by': user2,
            'assigned_to': user2,
            'credits_used': 0
        }
    )
    
    # Criar casos de uso
    print("Criando casos de uso...")
    UseCase.objects.get_or_create(
        title='Automação de documentos legais',
        defaults={
            'description': 'Como uma empresa de advocacia utiliza o Manus AI para automatizar a criação de contratos e documentos legais.',
            'category': 'Jurídico',
            'created_by': user1
        }
    )
    
    UseCase.objects.get_or_create(
        title='Gestão de contratos de RH',
        defaults={
            'description': 'Como um departamento de RH utiliza o Manus AI para gerenciar contratos de trabalho e documentos relacionados.',
            'category': 'Recursos Humanos',
            'created_by': user2
        }
    )
    
    # Criar eventos
    print("Criando eventos...")
    Event.objects.get_or_create(
        title='Workshop de Integração Manus AI',
        defaults={
            'description': 'Workshop prático sobre como integrar o Manus AI com outros sistemas.',
            'location': 'São Paulo, SP',
            'event_date': timezone.now() + timedelta(days=10),
            'created_by': user1
        }
    )
    
    Event.objects.get_or_create(
        title='Webinar: Novidades da v2.0',
        defaults={
            'description': 'Descubra as novas funcionalidades da versão 2.0 do Manus AI.',
            'location': 'Online',
            'event_date': timezone.now() + timedelta(days=20),
            'created_by': user2
        }
    )
    
    print("Dados de exemplo criados com sucesso!")

if __name__ == '__main__':
    create_sample_data()