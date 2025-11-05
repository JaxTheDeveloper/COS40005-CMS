from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Enrollment, EnrollmentApproval

@login_required
def view_enrollments(request):
    enrollments = Enrollment.objects.filter(student=request.user).select_related('offering__unit')
    return render(request, 'pages/enrollments.html', {'enrollments': enrollments})


@login_required
def pending_approvals(request):
    # For convenors or admins: list pending approvals
    approvals = EnrollmentApproval.objects.filter(status='PENDING')
    return render(request, 'pages/pending_approvals.html', {'approvals': approvals})
