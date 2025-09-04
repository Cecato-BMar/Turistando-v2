from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Task, ScheduledTask
from .forms import TaskForm

@login_required
def task_list(request):
    tasks = Task.objects.filter(created_by=request.user).order_by('-created_at')
    return render(request, 'tasks/list.html', {'tasks': tasks})

@login_required
def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            messages.success(request, 'Task created successfully')
            return redirect('tasks:task_detail', task_id=task.id)
    else:
        form = TaskForm()
    return render(request, 'tasks/create.html', {'form': form})

@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id, created_by=request.user)
    return render(request, 'tasks/detail.html', {'task': task})

@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, created_by=request.user)
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted successfully')
        return redirect('tasks:task_list')
    return render(request, 'tasks/confirm_delete.html', {'task': task})

@login_required
def scheduled_tasks(request):
    scheduled_tasks = ScheduledTask.objects.filter(task__created_by=request.user)
    return render(request, 'tasks/scheduled.html', {'scheduled_tasks': scheduled_tasks})
