from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import StudentAchievement, Achievement

@login_required
def my_achievements(request):
    achs = StudentAchievement.objects.filter(student=request.user).select_related('achievement')
    return render(request, 'pages/my_achievements.html', {'achievements': achs})
