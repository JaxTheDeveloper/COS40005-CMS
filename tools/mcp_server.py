"""Lightweight MCP server exposing CMS tools for Agentation.

Run with `python tools/mcp_server.py` (requires fastapi & uvicorn in requirements).
The server will initialize Django and then listen on port 8001 by default.

Security: set MCP_SERVICE_TOKEN environment variable and include
Authorization: Token <value> header on all requests. If unset, no auth is enforced.

Endpoints:
* GET  /get_student_profile?email=...
* POST /award_social_gold (json: student_id, amount, reason)
* GET  /list_available_units?course_code=...
* GET  /get_event_content?event_id=...

These call into Django ORM directly (or via an internal REST call for award).
"""
import os
import django
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Header, Depends, Request
from pydantic import BaseModel

# ensure DJANGO_SETTINGS_MODULE is set correctly for this project
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.backend.settings")

# initialize Django
django.setup()

from django.contrib.auth import get_user_model
from src.backend.enrollment.models import Enrollment
from src.backend.academic.models import Unit
from src.backend.core.models import Event

User = get_user_model()

# read configuration
API_BASE = os.environ.get('MCP_API_BASE', 'http://localhost:8000/api')
SERVICE_TOKEN = os.environ.get('MCP_SERVICE_TOKEN')

app = FastAPI(title="SwinCMS MCP Server")


def verify_token(authorization: Optional[str] = Header(None)):
    if SERVICE_TOKEN:
        if not authorization or authorization.split()[-1] != SERVICE_TOKEN:
            raise HTTPException(status_code=401, detail="Invalid service token")
    # if SERVICE_TOKEN is unset, allow all
    return True


@app.get("/tools")
def list_tools(request: Request, _: bool = Depends(verify_token)):
    """Return minimal tool definitions so that Agentation can introspect available actions."""
    # Agentation expects a list of {name, description, parameters}
    return [
        {
            "name": "get_student_profile",
            "description": "Lookup a student by email along with their enrollments.",
            "parameters": {"email": "string"},
            "method": "GET",
            "path": "/get_student_profile"
        },
        {
            "name": "award_social_gold",
            "description": "Award social gold to a student.",
            "parameters": {"student_id": "integer", "amount": "number", "reason": "string"},
            "method": "POST",
            "path": "/award_social_gold"
        },
        {
            "name": "list_available_units",
            "description": "List units available for a given course code.",
            "parameters": {"course_code": "string"},
            "method": "GET",
            "path": "/list_available_units"
        },
        {
            "name": "get_event_content",
            "description": "Retrieve generated content and status for an event.",
            "parameters": {"event_id": "integer"},
            "method": "GET",
            "path": "/get_event_content"
        },
    ]


@app.get("/get_student_profile")
def get_student_profile(email: str, _: bool = Depends(verify_token)):
    usr = User.objects.filter(email=email).first()
    if not usr:
        raise HTTPException(status_code=404, detail="student not found")
    enrollments = (
        Enrollment.objects.filter(student=usr)
        .select_related('offering__unit')
        .values(
            'offering__unit__code',
            'offering__year',
            'offering__semester',
            'status',
        )
    )
    return {"user": {"id": usr.id, "email": usr.email, "user_type": usr.user_type},
            "enrollments": list(enrollments)}


class GoldPayload(BaseModel):
    student_id: int
    amount: float
    reason: Optional[str] = None


@app.post("/award_social_gold")
def award_social_gold(payload: GoldPayload, _: bool = Depends(verify_token)):
    # this tool simply proxies to the existing REST endpoint /users/{id}/award-gold/
    import requests
    token = os.environ.get('MCP_BACKEND_TOKEN')
    headers = {}
    if token:
        headers['Authorization'] = f"Token {token}"
    url = f"{API_BASE}/users/{payload.student_id}/award-gold/"
    resp = requests.post(url, json=payload.dict(), headers=headers)
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


@app.get("/list_available_units")
def list_available_units(course_code: str, _: bool = Depends(verify_token)):
    units = Unit.objects.filter(course_units__course__code=course_code).values('code', 'name')
    return {"units": list(units)}


@app.get("/get_event_content")
def get_event_content(event_id: int, _: bool = Depends(verify_token)):
    ev = Event.objects.filter(id=event_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="event not found")
    return {
        "generated_content": ev.generated_content,
        "generation_status": ev.generation_status,
    }


if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get('MCP_PORT', 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
