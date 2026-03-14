import os
import requests as http_requests
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

# ──────────────────────────────────────────────
# Paste your Gemini API key here, OR set the
# GEMINI_API_KEY environment variable.
# Get a free key at: https://aistudio.google.com/apikey
# ──────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'Gemini_API_Key')

GEMINI_URL = (
    f'https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest'
    f':generateContent?key={GEMINI_API_KEY}'
)

SYSTEM_INSTRUCTION = (
    "You are a helpful educational assistant for Swinburne University students. "
    "Answer questions clearly and concisely. Focus on academics, study tips, "
    "time management, and student life. Format your responses with clear "
    "paragraphs. If the student asks something outside the educational scope, "
    "gently redirect them."
)


@api_view(['POST'])
@permission_classes([AllowAny])
def chat(request):
    """
    POST /api/askai/chat/
    Body: { "message": "...", "history": [ { "role": "user"|"model", "text": "..." }, ... ] }
    Returns: { "reply": "..." }
    """
    user_message = request.data.get('message', '').strip()
    if not user_message:
        return Response(
            {'error': 'Message is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check API key configuration
    if GEMINI_API_KEY in ('PASTE_YOUR_API_KEY_HERE', ''):
        return Response(
            {'error': 'Gemini API key is not configured. Please set GEMINI_API_KEY.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Build conversation history for multi-turn
    history = request.data.get('history', [])
    contents = []

    # Add system instruction as the first user turn (Gemini REST API pattern)
    contents.append({
        'role': 'user',
        'parts': [{'text': SYSTEM_INSTRUCTION}],
    })
    contents.append({
        'role': 'model',
        'parts': [{'text': 'Understood! I\'m ready to help Swinburne students. How can I assist you today?'}],
    })

    # Add conversation history
    for msg in history:
        role = 'user' if msg.get('role') == 'user' else 'model'
        contents.append({
            'role': role,
            'parts': [{'text': msg.get('text', '')}],
        })

    # Add the current user message
    contents.append({
        'role': 'user',
        'parts': [{'text': user_message}],
    })

    payload = {
        'contents': contents,
        'generationConfig': {
            'temperature': 0.7,
            'topP': 0.95,
            'maxOutputTokens': 2048,
        },
    }

    try:
        resp = http_requests.post(GEMINI_URL, json=payload, timeout=30)

        if resp.status_code != 200:
            error_detail = resp.json().get('error', {}).get('message', resp.text)
            return Response(
                {'error': f'Gemini API error: {error_detail}'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        data = resp.json()
        # Extract the text from Gemini's response
        candidates = data.get('candidates', [])
        if not candidates:
            return Response(
                {'error': 'No response from Gemini.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        parts = candidates[0].get('content', {}).get('parts', [])
        reply_text = ''.join(part.get('text', '') for part in parts)

        return Response({'reply': reply_text})

    except http_requests.exceptions.Timeout:
        return Response(
            {'error': 'The AI is taking too long to respond. Please try again.'},
            status=status.HTTP_504_GATEWAY_TIMEOUT,
        )
    except http_requests.exceptions.ConnectionError:
        return Response(
            {'error': 'Cannot connect to the AI service. Check your internet connection.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    except Exception as e:
        return Response(
            {'error': f'Unexpected error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
