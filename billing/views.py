from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Plan, Subscription, CreditTransaction

@login_required
def billing_home(request):
    # Get user's current plan
    try:
        subscription = Subscription.objects.get(user=request.user, is_active=True)
        current_plan = subscription.plan
    except Subscription.DoesNotExist:
        current_plan = None
    
    # Get credit balance
    credit_transactions = CreditTransaction.objects.filter(user=request.user).order_by('-created_at')
    
    # Calculate credit balance
    credit_balance = 0
    for transaction in credit_transactions:
        if transaction.transaction_type in ['purchase', 'bonus']:
            credit_balance += transaction.amount
        elif transaction.transaction_type == 'usage':
            credit_balance -= transaction.amount
    
    return render(request, 'billing/home.html', {
        'current_plan': current_plan,
        'credit_balance': credit_balance,
        'credit_transactions': credit_transactions[:10]
    })

def plans(request):
    plans = Plan.objects.all()
    return render(request, 'billing/plans.html', {'plans': plans})

@login_required
def credits(request):
    credit_transactions = CreditTransaction.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'billing/credits.html', {'credit_transactions': credit_transactions})
