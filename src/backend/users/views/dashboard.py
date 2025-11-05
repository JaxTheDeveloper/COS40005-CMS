from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def dashboard_view(request):
    context = {
        'user': request.user
    }
    return render(request, 'dashboard/dashboard.html', context)

@login_required
def student_dashboard_view(request):
    if request.user.user_type != 'student':
        return redirect('dashboard')
    context = {
        'user': request.user
    }
    return render(request, 'dashboard/student_dashboard.html', context)

@login_required
def convenor_dashboard_view(request):
    if request.user.user_type != 'unit_convenor':
        return redirect('dashboard')
    context = {
        'user': request.user
    }
    return render(request, 'dashboard/convenor_dashboard.html', context)