import os
import django

# Configurar o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'manus_ai.settings')
django.setup()

from accounts.models import Profile
from tasks.models import Task
from billing.models import Plan
from community.models import UseCase, Event

def check_data():
    print("Verificando dados no banco de dados:")
    print(f"Profiles: {Profile.objects.count()}")
    print(f"Tasks: {Task.objects.count()}")
    print(f"Plans: {Plan.objects.count()}")
    print(f"UseCases: {UseCase.objects.count()}")
    print(f"Events: {Event.objects.count()}")

if __name__ == '__main__':
    check_data()