from django.shortcuts import render
from .models import UseCase, Event

def community_home(request):
    use_cases = UseCase.objects.all().order_by('-created_at')[:6]
    events = Event.objects.all().order_by('event_date')[:3]
    return render(request, 'community/home.html', {
        'use_cases': use_cases,
        'events': events
    })

def use_cases(request):
    use_cases = UseCase.objects.all().order_by('-created_at')
    return render(request, 'community/use_cases.html', {'use_cases': use_cases})

def events(request):
    events = Event.objects.all().order_by('event_date')
    return render(request, 'community/events.html', {'events': events})
