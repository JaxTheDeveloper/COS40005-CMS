import os
import requests as http_requests
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_URL = (
    f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash'
    f':generateContent?key={GEMINI_API_KEY}'
)


def _get_n8n_workflow():
    """Return active N8NWorkflow for student.ask trigger, or None."""
    try:
        from django.apps import apps
        N8NWorkflow = apps.get_model('users', 'N8NWorkflow')
        return N8NWorkflow.objects.filter(trigger_event='student.ask', is_active=True).first()
    except Exception:
        return None


def _resolve_webhook_url(wf) -> str:
    config = wf.configuration or {}
    if config.get('use_test_url'):
        return config.get('webhook_url_test') or config.get('webhook_url', '')
    return config.get('webhook_url', '')


def _get_student_context(user) -> str:
    """
    Build a grounding context string from the student's live DB records.
    Injected into the Gemini system prompt so the AI can give personalised advice.
    """
    from django.utils import timezone
    from src.backend.enrollment.models import Enrollment, Transcript
    from src.backend.core.models import Event, Notification

    lines = [
        f"Student: {user.get_full_name() or user.email}",
        f"Email: {user.email}",
        f"Department: {user.department or 'Not set'}",
    ]

    # ── Social Gold ──────────────────────────────────────────────────────
    try:
        from src.backend.social.models import SocialGold
        sg = SocialGold.objects.filter(student=user).first()
        if sg:
            lines.append(f"Social Gold balance: {sg.current_balance} (lifetime earned: {sg.lifetime_earned})")
        else:
            lines.append("Social Gold balance: 0 (no record yet)")
    except Exception:
        pass

    # ── Current Enrollments ──────────────────────────────────────────────
    try:
        enrollments = (
            Enrollment.objects.filter(student=user, status__in=['ENROLLED', 'enrolled'])
            .select_related('offering__unit')
            .order_by('-offering__year', 'offering__semester')[:10]
        )
        if enrollments:
            lines.append("\nCurrent enrollments:")
            for e in enrollments:
                unit = e.offering.unit
                lines.append(
                    f"  - {unit.code} {unit.name} "
                    f"({e.offering.semester} {e.offering.year}) "
                    f"[{e.status}]"
                    + (f" Grade: {e.grade}" if e.grade else "")
                )
        else:
            lines.append("\nNo active enrollments found.")
    except Exception:
        pass

    # ── Academic Transcript ──────────────────────────────────────────────
    try:
        transcripts = (
            Transcript.objects.filter(student=user)
            .order_by('-year', 'semester')[:10]
        )
        if transcripts:
            lines.append("\nAcademic transcript (recent):")
            for t in transcripts:
                lines.append(
                    f"  - {t.unit_code} {t.unit_name} "
                    f"({t.semester} {t.year}): "
                    f"Grade {t.grade or 'N/A'}, "
                    f"Marks {t.marks or 'N/A'}/100, "
                    f"Status: {t.status}"
                )
    except Exception:
        pass

    # ── Upcoming Events targeted at this student ─────────────────────────
    try:
        from django.db.models import Q
        now = timezone.now()
        events = (
            Event.objects.filter(
                Q(target_all_students=True) | Q(target_students=user),
                start__gte=now,
                generation_status='ready',
            )
            .order_by('start')[:5]
        )
        if events:
            lines.append("\nUpcoming events for you:")
            for ev in events:
                lines.append(
                    f"  - {ev.title} on {ev.start.strftime('%d %b %Y')} "
                    f"at {ev.location or 'TBA'}"
                )
    except Exception:
        pass

    # ── Unread Notifications ─────────────────────────────────────────────
    try:
        notifs = Notification.objects.filter(recipient=user, unread=True).order_by('-created_at')[:5]
        if notifs:
            lines.append("\nUnread notifications:")
            for n in notifs:
                lines.append(f"  - {n.verb}")
    except Exception:
        pass

    return "\n".join(lines)


def _build_system_prompt(student_context: str) -> str:
    base = (
        "You are a personalised academic advisor and student assistant for Swinburne Vietnam. "
        "You have access to the student's live academic records shown below. "
        "Use this data to give specific, actionable advice — not generic answers. "
        "You can help with: course recommendations, grade improvement, Social Gold tips, "
        "upcoming events, enrollment guidance, and general student life. "
        "Be warm, concise, and encouraging. Format responses with clear paragraphs. "
        "If asked about something outside the student's academic life, gently redirect.\n\n"
        "=== STUDENT RECORD ===\n"
    )
    return base + student_context + "\n=== END OF RECORD ==="


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat(request):
    """
    POST /api/askai/chat/
    Body: { "message": "...", "history": [ { "role": "user"|"model", "text": "..." } ] }
    Returns: { "reply": "..." }

    Routing:
      1. If a student.ask N8NWorkflow is registered → calls n8n (which uses MCP tools + Groq)
      2. Otherwise → falls back to Gemini with DB context injected into the prompt
    """
    user_message = request.data.get('message', '').strip()
    if not user_message:
        return Response({'error': 'Message is required.'}, status=status.HTTP_400_BAD_REQUEST)

    history = request.data.get('history', [])

    # ── Route 1: n8n workflow with MCP tools ─────────────────────────────────
    wf = _get_n8n_workflow()
    if wf:
        webhook_url = _resolve_webhook_url(wf)
        if webhook_url:
            try:
                resp = http_requests.post(
                    webhook_url,
                    json={
                        'event_id': None,
                        'timestamp': __import__('django.utils.timezone', fromlist=['timezone']).timezone.now().isoformat(),
                        'payload': {
                            'email': request.user.email,
                            'message': user_message,
                            'chat_history': history,
                        },
                    },
                    headers={'Content-Type': 'application/json'},
                    timeout=60,
                )
                resp.raise_for_status()
                data = resp.json()
                reply = data.get('reply') or data.get('output') or str(data)
                return Response({'reply': reply, 'source': 'n8n'})
            except Exception as exc:
                import logging
                logging.getLogger(__name__).warning('n8n student.ask failed, falling back to Gemini: %s', exc)

    # ── Route 2: Gemini with DB context injected ──────────────────────────────
    if not GEMINI_API_KEY:
        return Response(
            {'error': 'AI service not configured. Set GEMINI_API_KEY or register a student.ask n8n workflow.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    student_context = _get_student_context(request.user)
    system_prompt = _build_system_prompt(student_context)

    contents = []
    contents.append({'role': 'user', 'parts': [{'text': system_prompt}]})
    contents.append({'role': 'model', 'parts': [{'text': (
        "Understood. I have your academic records loaded and I'm ready to give you "
        "personalised advice. How can I help you today?"
    )}]})

    for msg in history:
        role = 'user' if msg.get('role') == 'user' else 'model'
        contents.append({'role': role, 'parts': [{'text': msg.get('text', '')}]})

    contents.append({'role': 'user', 'parts': [{'text': user_message}]})

    payload = {
        'contents': contents,
        'generationConfig': {'temperature': 0.7, 'topP': 0.95, 'maxOutputTokens': 2048},
    }

    try:
        resp = http_requests.post(GEMINI_URL, json=payload, timeout=30)
        if resp.status_code != 200:
            error_detail = resp.json().get('error', {}).get('message', resp.text)
            return Response({'error': f'Gemini API error: {error_detail}'}, status=status.HTTP_502_BAD_GATEWAY)

        data = resp.json()
        candidates = data.get('candidates', [])
        if not candidates:
            return Response({'error': 'No response from Gemini.'}, status=status.HTTP_502_BAD_GATEWAY)

        parts = candidates[0].get('content', {}).get('parts', [])
        reply_text = ''.join(part.get('text', '') for part in parts)
        return Response({'reply': reply_text, 'source': 'gemini'})

    except http_requests.exceptions.Timeout:
        return Response({'error': 'The AI is taking too long. Please try again.'}, status=status.HTTP_504_GATEWAY_TIMEOUT)
    except http_requests.exceptions.ConnectionError:
        return Response({'error': 'Cannot connect to the AI service.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        return Response({'error': f'Unexpected error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
