from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import SemesterOffering, Unit, UnitResource


def available_units(request):
    # Show current and upcoming offerings
    offerings = SemesterOffering.objects.filter(is_active=True).order_by('-year', 'semester')[:50]
    return render(request, 'pages/available_units.html', {'offerings': offerings})


@login_required
def my_units(request):
    # Units convened by the current user
    units = Unit.objects.filter(convenor=request.user)
    return render(request, 'pages/my_units.html', {'units': units})


@login_required
def manage_resources(request, unit_id):
    unit = get_object_or_404(Unit, pk=unit_id)
    resources = UnitResource.objects.filter(unit=unit)
    return render(request, 'pages/manage_resources.html', {'unit': unit, 'resources': resources})
