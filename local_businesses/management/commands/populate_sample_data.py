from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from local_businesses.models import BusinessCategory, Business, BusinessPlan

class Command(BaseCommand):
    help = 'Populate database with sample data for local businesses'

    def handle(self, *args, **options):
        # Create sample categories
        categories_data = [
            {'name': 'Restaurantes', 'icon': 'utensils'},
            {'name': 'Hotéis', 'icon': 'hotel'},
            {'name': 'Lojas', 'icon': 'store'},
            {'name': 'Serviços', 'icon': 'concierge-bell'},
            {'name': 'Turismo', 'icon': 'map-marked-alt'},
        ]

        for cat_data in categories_data:
            category, created = BusinessCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={'icon': cat_data['icon']}
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')
            else:
                self.stdout.write(f'Category already exists: {category.name}')

        # Create sample businesses
        businesses_data = [
            {
                'name': 'Restaurante Sabor do Mar',
                'description': 'O melhor frutos do mar da região. Especialidade em peixes frescos e frutos do mar.',
                'business_type': 'commerce',
                'address': 'Av. Beira Mar, 123 - Centro',
                'latitude': -8.0633,
                'longitude': -34.8711,
                'phone': '(81) 3232-1234',
                'whatsapp': '5581999991234',
                'email': 'contato@sabordomar.com',
                'website': 'https://www.sabordomar.com',
                'plan_type': 'premium'
            },
            {
                'name': 'Hotel Vista Mar',
                'description': 'Hotel 4 estrelas com vista para o mar. Localizado no centro da cidade.',
                'business_type': 'commerce',
                'address': 'Rua das Palmeiras, 456 - Centro',
                'latitude': -8.0622,
                'longitude': -34.8722,
                'phone': '(81) 3333-5678',
                'whatsapp': '5581999995678',
                'email': 'reservas@vistamarhotel.com',
                'website': 'https://www.vistamarhotel.com',
                'plan_type': 'premium'
            },
            {
                'name': 'Loja de Artesanato Recife',
                'description': 'Loja especializada em artesanato local. Produtos feitos por artesãos da região.',
                'business_type': 'commerce',
                'address': 'Rua do Bom Jesus, 789 - Recife Antigo',
                'latitude': -8.0644,
                'longitude': -34.8733,
                'phone': '(81) 3434-9012',
                'whatsapp': '5581999999012',
                'email': 'contato@artesanatorecife.com',
                'website': 'https://www.artesanatorecife.com',
                'plan_type': 'pro'
            },
            {
                'name': 'Guia Turístico Recife',
                'description': 'Guias turísticos especializados em mostrar os pontos turísticos da cidade.',
                'business_type': 'service',
                'address': 'Rua da Aurora, 321 - Boa Vista',
                'latitude': -8.0611,
                'longitude': -34.8744,
                'phone': '(81) 3535-3456',
                'whatsapp': '5581999993456',
                'email': 'info@guiaturisticorecife.com',
                'website': 'https://www.guiaturisticorecife.com',
                'plan_type': 'free'
            },
        ]

        # Create a sample user for businesses
        user, created = User.objects.get_or_create(
            username='business_owner',
            defaults={
                'email': 'owner@example.com',
                'first_name': 'Business',
                'last_name': 'Owner'
            }
        )
        if created:
            user.set_password('password123')
            user.save()
            self.stdout.write(f'Created user: {user.username}')

        for business_data in businesses_data:
            # Get or create category
            category = BusinessCategory.objects.get(name='Restaurantes')  # Default category
            if 'Hotéis' in business_data['name']:
                category = BusinessCategory.objects.get(name='Hotéis')
            elif 'Loja' in business_data['name']:
                category = BusinessCategory.objects.get(name='Lojas')
            elif 'Guia' in business_data['name']:
                category = BusinessCategory.objects.get(name='Turismo')

            # Create business
            business, created = Business.objects.get_or_create(
                name=business_data['name'],
                defaults={
                    'user': user,
                    'description': business_data['description'],
                    'business_type': business_data['business_type'],
                    'category': category,
                    'address': business_data['address'],
                    'latitude': business_data['latitude'],
                    'longitude': business_data['longitude'],
                    'phone': business_data['phone'],
                    'whatsapp': business_data['whatsapp'],
                    'email': business_data['email'],
                    'website': business_data['website'],
                    'is_active': True
                }
            )

            if created:
                self.stdout.write(f'Created business: {business.name}')
                
                # Create business plan
                BusinessPlan.objects.create(
                    business=business,
                    plan_type=business_data['plan_type'],
                    max_photos=10 if business_data['plan_type'] == 'premium' else (5 if business_data['plan_type'] == 'pro' else 1),
                    can_show_menu=business_data['plan_type'] == 'premium',
                    can_show_website=business_data['plan_type'] in ['pro', 'premium'],
                    can_show_whatsapp=business_data['plan_type'] in ['pro', 'premium'],
                    is_featured=business_data['plan_type'] == 'premium'
                )
                self.stdout.write(f'  Created plan: {business_data["plan_type"]}')
            else:
                self.stdout.write(f'Business already exists: {business.name}')

        self.stdout.write(
            self.style.SUCCESS('Successfully populated sample data')
        )