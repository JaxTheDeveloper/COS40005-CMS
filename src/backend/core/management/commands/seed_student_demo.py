from datetime import date, datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from src.backend.academic.models import Course, Unit, SemesterOffering
from src.backend.core.models import Session, AttendanceRecord
from src.backend.enrollment.models import Enrollment
from src.backend.users.models import StudentProfile


User = get_user_model()


UNIT_DEFINITIONS = [
    {
        "code": "COS10001",
        "name": "Introduction to Programming",
        "description": "Foundational programming concepts using Python.",
        "credit_points": 12,
        "department": "Computer Science",
        "lecture_hours": 3,
        "prerequisites": [],
    },
    {
        "code": "COS10003",
        "name": "Computer and Logic Essentials",
        "description": "Discrete mathematics, Boolean logic, and computer fundamentals.",
        "credit_points": 12,
        "department": "Computer Science",
        "lecture_hours": 3,
        "prerequisites": [],
    },
    {
        "code": "COS20007",
        "name": "Object Oriented Programming",
        "description": "Intermediate programming with Java and design patterns.",
        "credit_points": 12,
        "department": "Computer Science",
        "lecture_hours": 3,
        "prerequisites": ["COS10001"],
    },
    {
        "code": "COS20015",
        "name": "Fundamentals of Data Science",
        "description": "Data wrangling, visualization, and introductory ML concepts.",
        "credit_points": 12,
        "department": "Computer Science",
        "lecture_hours": 4,
        "prerequisites": ["COS10001", "COS10003"],
    },
    {
        "code": "COS30043",
        "name": "Interface Design and Development",
        "description": "Front-end engineering and UX design workflow.",
        "credit_points": 12,
        "department": "Computer Science",
        "lecture_hours": 3,
        "prerequisites": ["COS20007"],
    },
]


OFFERING_PLAN = [
    {"unit": "COS10001", "year": 2024, "semester": "S1", "status": "COMPLETED", "grade": "HD", "marks": 88},
    {"unit": "COS10003", "year": 2024, "semester": "S2", "status": "COMPLETED", "grade": "D", "marks": 78},
    {"unit": "COS20007", "year": 2025, "semester": "S1", "status": "ENROLLED", "grade": None, "marks": None},
    {"unit": "COS20015", "year": 2025, "semester": "S1", "status": "ENROLLED", "grade": None, "marks": None},
    {"unit": "COS30043", "year": 2025, "semester": "S2", "status": "PENDING", "grade": None, "marks": None},
]


SEMESTER_STARTS = {
    "S1": (3, 3),
    "S2": (7, 1),
    "S3": (10, 1),
    "SS": (1, 5),
    "WS": (12, 1),
}


class Command(BaseCommand):
    help = "Seed demo data for a reference student including units, offerings, enrollments, and attendance."

    @transaction.atomic
    def handle(self, *args, **options):
        student = self.ensure_student()
        instructor = self.ensure_instructor()
        course = self.ensure_course()
        self.ensure_student_profile(student, course)

        unit_map = self.ensure_units(instructor)
        offering_map = self.ensure_offerings(unit_map)

        enrollments = self.ensure_enrollments(student, offering_map)
        self.ensure_sessions_and_attendance(student, offering_map, enrollments, instructor)

        self.stdout.write(self.style.SUCCESS("Demo student data seeded successfully."))

    def ensure_student(self):
        user_defaults = {
            "username": "thanhnhathoang",
            "first_name": "Thanh",
            "last_name": "Hoang",
            "department": "Computer Science",
            "user_type": "student",
            "is_active": True,
        }
        user, created = User.objects.get_or_create(
            email="thanhnhathoang@swin.edu.au",
            defaults=user_defaults,
        )
        if created:
            user.set_password("password123")
            user.save()
            self.stdout.write(self.style.SUCCESS("Created student user"))
        return user

    def ensure_instructor(self):
        user_defaults = {
            "username": "alexsmith",
            "first_name": "Alex",
            "last_name": "Smith",
            "department": "Computer Science",
            "position": "Senior Lecturer",
            "user_type": "staff",
            "is_staff": True,
            "is_active": True,
        }
        user, created = User.objects.get_or_create(
            email="convenor@swin.edu.au",
            defaults=user_defaults,
        )
        if created:
            user.set_password("Test@123")
            user.save()
            self.stdout.write(self.style.SUCCESS("Created instructor user"))
        return user

    def ensure_course(self):
        course, _ = Course.objects.get_or_create(
            code="B-CS",
            defaults={
                "name": "Bachelor of Computer Science",
                "description": "Undergraduate program for Computer Science.",
                "credit_points": 192,
                "department": "Computer Science",
            },
        )
        return course

    def ensure_student_profile(self, student, course):
        StudentProfile.objects.get_or_create(
            user=student,
            defaults={
                "student_id": "S-THANH001",
                "enrollment_date": date(2024, 1, 10),
                "expected_graduation": date(2027, 11, 30),
                "course": course,
                "current_gpa": 3.8,
                "academic_status": "good",
            },
        )

    def ensure_units(self, instructor):
        unit_map = {}
        for definition in UNIT_DEFINITIONS:
            unit, _ = Unit.objects.get_or_create(
                code=definition["code"],
                defaults={
                    "name": definition["name"],
                    "description": definition["description"],
                    "credit_points": definition["credit_points"],
                    "department": definition["department"],
                    "is_active": True,
                    "convenor": instructor,
                },
            )
            if not unit.convenor:
                unit.convenor = instructor
                unit.save(update_fields=["convenor"])
            unit_map[definition["code"]] = unit

        # Apply prerequisites after all units exist
        for definition in UNIT_DEFINITIONS:
            unit = unit_map[definition["code"]]
            prereq_units = [unit_map[code] for code in definition["prerequisites"]]
            unit.prerequisites.set(prereq_units)

        return unit_map

    def ensure_offerings(self, unit_map):
        offering_map = {}
        for plan in OFFERING_PLAN:
            unit = unit_map[plan["unit"]]
            semester_start = self.get_semester_start(plan["year"], plan["semester"])

            enrollment_start = timezone.make_aware(
                datetime.combine(semester_start - timedelta(days=30), time(9, 0))
            )
            enrollment_end = timezone.make_aware(
                datetime.combine(semester_start + timedelta(days=7), time(17, 0))
            )

            offering, _ = SemesterOffering.objects.get_or_create(
                unit=unit,
                year=plan["year"],
                semester=plan["semester"],
                defaults={
                    "enrollment_start": enrollment_start,
                    "enrollment_end": enrollment_end,
                    "capacity": 200,
                    "current_enrollment": 0,
                    "is_active": True,
                    "notes": f"Major: Computer Science; Category: core; Class {plan.get('lecture_hours', 3)}h/week; Mon 09:00",
                },
            )
            offering_map[(plan["unit"], plan["year"], plan["semester"])] = {
                "offering": offering,
                "plan": plan,
                "semester_start": semester_start,
            }
        return offering_map

    def ensure_enrollments(self, student, offering_map):
        enrollments = {}
        for key, data in offering_map.items():
            offering = data["offering"]
            plan = data["plan"]

            enrollment_defaults = {
                "status": plan["status"],
                "grade": plan["grade"] or "",
                "marks": plan["marks"],
                "completion_date": timezone.make_aware(
                    datetime.combine(data["semester_start"] + timedelta(weeks=12), time(17, 0))
                )
                if plan["status"] == "COMPLETED"
                else None,
            }

            enrollment, _ = Enrollment.objects.update_or_create(
                student=student,
                offering=offering,
                defaults=enrollment_defaults,
            )

            if plan["status"] != "COMPLETED":
                enrollment.completion_date = None
                enrollment.grade = enrollment.grade or ""
                enrollment.marks = enrollment.marks
                enrollment.save(update_fields=["completion_date", "grade", "marks", "status"])

            enrollments[offering.id] = enrollment

            active_statuses = ["PENDING", "ENROLLED"]
            offering.current_enrollment = Enrollment.objects.filter(
                offering=offering, status__in=active_statuses
            ).count()
            offering.save(update_fields=["current_enrollment"])

        return enrollments

    def ensure_sessions_and_attendance(self, student, offering_map, enrollments, instructor):
        for data in offering_map.values():
            offering = data["offering"]
            plan = data["plan"]
            semester_start = data["semester_start"]
            lecture_hours = next(
                (definition["lecture_hours"] for definition in UNIT_DEFINITIONS if definition["code"] == plan["unit"]),
                3,
            )

            # Remove existing sessions for idempotency
            Session.objects.filter(offering=offering).delete()

            sessions = []
            for week in range(12):
                session_date = semester_start + timedelta(weeks=week)
                start_time = time(9, 0)
                end_dt = datetime.combine(session_date, start_time) + timedelta(hours=lecture_hours)
                session, _ = Session.objects.get_or_create(
                    unit=offering.unit,
                    offering=offering,
                    session_type="lecture",
                    date=session_date,
                    defaults={
                        "start_time": start_time,
                        "end_time": end_dt.time(),
                        "location": "Hanoi Campus Room 402",
                        "instructor": instructor,
                    },
                )
                if session.instructor_id != instructor.id:
                    session.instructor = instructor
                    session.save(update_fields=["instructor"])
                sessions.append(session)

            AttendanceRecord.objects.filter(
                session__in=sessions, student=student
            ).delete()

            if plan["status"] not in ["COMPLETED", "ENROLLED"]:
                continue

            for idx, session in enumerate(sessions):
                status = self.get_attendance_status(plan["status"], idx)
                AttendanceRecord.objects.create(
                    session=session,
                    student=student,
                    status=status,
                )

    def get_attendance_status(self, enrollment_status, week_index):
        if enrollment_status == "COMPLETED":
            if week_index in (8, 10):
                return "late"
            return "present"
        if enrollment_status == "ENROLLED":
            return "present" if week_index % 4 else "absent"
        return "present"

    def get_semester_start(self, year, semester_code):
        month, day = SEMESTER_STARTS.get(semester_code, (3, 3))
        return date(year, month, day)

