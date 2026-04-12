"""
SwinCMS MCP Server — speaks the Model Context Protocol over SSE.

n8n connects to this via the MCP Client node:
  Transport: SSE
  URL: http://cos40005_mcp:8001/sse

Tools exposed:
  get_student_profile     — profile + current enrollments
  get_student_transcript  — full academic transcript with grades
  get_social_gold         — Social Gold balance + recent transactions
  get_upcoming_events     — events targeted at this student
  get_notifications       — unread notifications
  recommend_courses       — suggest next units based on transcript
  award_social_gold       — award gold to a student
  list_available_units    — units in a course
  get_event_content       — AI-generated content for an event

Run:
  python tools/mcp_server.py
  (or via Docker: cos40005_mcp container)

Security: set MCP_SERVICE_TOKEN env var. n8n must pass it as a header.
"""
import os
import sys
import django

# Ensure /app is on the path so 'config' and 'src' packages are importable
# regardless of which directory Python was launched from
_app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _app_root not in sys.path:
    sys.path.insert(0, _app_root)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from mcp.server.fastmcp import FastMCP
from django.contrib.auth import get_user_model

User = get_user_model()

mcp = FastMCP("SwinCMS", port=int(os.environ.get("MCP_PORT", 8001)))


# ── Helpers ──────────────────────────────────────────────────────────────────

def _get_user(email: str):
    usr = User.objects.filter(email=email).first()
    if not usr:
        raise ValueError(f"User not found: {email}")
    return usr


# ── Tools ────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_student_profile(email: str) -> dict:
    """
    Get a student's profile and current enrollments.
    Returns name, email, department, user_type, and list of enrolled units.
    """
    from src.backend.enrollment.models import Enrollment
    usr = _get_user(email)
    enrollments = list(
        Enrollment.objects.filter(student=usr)
        .select_related('offering__unit')
        .values(
            'offering__unit__code', 'offering__unit__name',
            'offering__year', 'offering__semester',
            'status', 'grade', 'marks',
        )
    )
    return {
        "user": {
            "id": usr.id,
            "email": usr.email,
            "name": usr.get_full_name(),
            "user_type": usr.user_type,
            "department": usr.department,
        },
        "enrollments": enrollments,
    }


@mcp.tool()
def get_student_transcript(email: str) -> dict:
    """
    Get a student's full academic transcript including grades, marks, and credit points.
    Returns all completed and in-progress units with their results.
    """
    from src.backend.enrollment.models import Transcript
    usr = _get_user(email)
    records = list(
        Transcript.objects.filter(student=usr)
        .order_by('-year', 'semester')
        .values(
            'unit_code', 'unit_name', 'semester', 'year',
            'grade', 'marks', 'grade_point', 'status', 'credit_points',
        )
    )
    total_cp = sum(
        (r['credit_points'] or 0) for r in records
        if r['status'] in ('COMPLETED', 'completed')
    )
    return {
        "transcript": records,
        "total_credit_points_completed": total_cp,
        "total_units": len(records),
    }


@mcp.tool()
def get_social_gold(email: str) -> dict:
    """
    Get a student's Social Gold balance and recent transaction history.
    Social Gold is earned through attendance, participation, and achievements.
    """
    from src.backend.social.models import SocialGold, SocialGoldTransaction
    usr = _get_user(email)
    sg = SocialGold.objects.filter(student=usr).first()
    transactions = list(
        SocialGoldTransaction.objects.filter(student=usr)
        .order_by('-created_at')
        .values('amount', 'transaction_type', 'reason', 'created_at')[:10]
    )
    return {
        "current_balance": sg.current_balance if sg else 0,
        "lifetime_earned": sg.lifetime_earned if sg else 0,
        "recent_transactions": transactions,
    }


@mcp.tool()
def get_upcoming_events(email: str) -> dict:
    """
    Get upcoming events that are targeted at this specific student.
    Only returns events the student is eligible to see based on their targeting.
    """
    from django.utils import timezone
    from django.db.models import Q
    from src.backend.core.models import Event
    usr = _get_user(email)
    now = timezone.now()
    events = list(
        Event.objects.filter(
            Q(target_all_students=True) | Q(target_students=usr),
            start__gte=now,
        )
        .exclude(visibility='staff')
        .order_by('start')
        .values('id', 'title', 'start', 'location', 'description', 'generation_status')[:10]
    )
    # Convert datetime to string for JSON serialisation
    for ev in events:
        if ev.get('start'):
            ev['start'] = ev['start'].isoformat()
    return {"upcoming_events": events, "count": len(events)}


@mcp.tool()
def get_notifications(email: str) -> dict:
    """
    Get unread notifications for a student.
    Returns the most recent 20 unread notifications.
    """
    from src.backend.core.models import Notification
    usr = _get_user(email)
    notifs = list(
        Notification.objects.filter(recipient=usr, unread=True)
        .order_by('-created_at')
        .values('id', 'verb', 'unread', 'created_at')[:20]
    )
    for n in notifs:
        if n.get('created_at'):
            n['created_at'] = n['created_at'].isoformat()
    return {"notifications": notifs, "unread_count": len(notifs)}


@mcp.tool()
def recommend_courses(email: str) -> dict:
    """
    Recommend next units for a student to take based on their course plan
    and units already completed or enrolled in.
    Returns up to 5 recommended units with descriptions.
    """
    from src.backend.enrollment.models import Enrollment, Transcript
    from src.backend.academic.models import Unit
    usr = _get_user(email)

    completed_codes = set(
        Transcript.objects.filter(student=usr, status__in=['COMPLETED', 'completed'])
        .values_list('unit_code', flat=True)
    )
    enrolled_codes = set(
        Enrollment.objects.filter(student=usr)
        .values_list('offering__unit__code', flat=True)
    )
    taken = completed_codes | enrolled_codes

    try:
        from src.backend.users.models import StudentProfile
        profile = StudentProfile.objects.filter(user=usr).select_related('course').first()
        if profile and profile.course:
            suggestions = list(
                Unit.objects.filter(course_units__course=profile.course)
                .exclude(code__in=taken)
                .values('code', 'name', 'credit_points', 'description')[:5]
            )
        else:
            suggestions = list(
                Unit.objects.exclude(code__in=taken)
                .values('code', 'name', 'credit_points', 'description')[:5]
            )
    except Exception:
        suggestions = []

    return {
        "completed_units": list(completed_codes),
        "currently_enrolled": list(enrolled_codes),
        "recommended_next": suggestions,
    }


@mcp.tool()
def award_social_gold(student_id: int, amount: float, reason: str = "") -> dict:
    """
    Award Social Gold to a student. Used for attendance, achievements, or manual awards.
    Requires student_id (integer), amount (positive number), and optional reason string.
    """
    import requests
    api_base = os.environ.get('MCP_API_BASE', 'http://localhost:8000/api')
    token = os.environ.get('MCP_BACKEND_TOKEN', '')
    headers = {'Authorization': f'Token {token}'} if token else {}
    url = f"{api_base}/social/transactions/award/"
    resp = requests.post(url, json={
        "student_id": student_id,
        "amount": amount,
        "transaction_type": "AWARD",
        "reason": reason,
    }, headers=headers, timeout=10)
    if resp.status_code >= 400:
        raise ValueError(f"Award failed: {resp.text}")
    return resp.json()


@mcp.tool()
def list_available_units(course_code: str) -> dict:
    """
    List all units available for a given course code.
    Useful for advising students on what they can enrol in.
    """
    from src.backend.academic.models import Unit
    units = list(
        Unit.objects.filter(course_units__course__code=course_code)
        .values('code', 'name', 'credit_points', 'description')
    )
    return {"course_code": course_code, "units": units, "count": len(units)}


@mcp.tool()
def get_event_content(event_id: int) -> dict:
    """
    Get the AI-generated content for a specific event.
    Returns social post, email newsletter, recruitment ad, and Vietnamese version.
    """
    from src.backend.core.models import Event
    ev = Event.objects.filter(id=event_id).first()
    if not ev:
        raise ValueError(f"Event not found: {event_id}")
    return {
        "id": ev.id,
        "title": ev.title,
        "generation_status": ev.generation_status,
        "generated_content": ev.generated_content,
        "generation_meta": ev.generation_meta,
    }


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    # SSE transport — n8n MCP Client node connects to http://cos40005_mcp:8001/sse
    mcp.run(transport="sse")
