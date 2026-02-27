from collections import defaultdict
from datetime import datetime, time

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q

from .models import Enrollment, Transcript
from .serializers import EnrollmentSerializer, EnrollmentCreateSerializer, TranscriptSerializer
from src.backend.academic.models import SemesterOffering, CourseUnit
from src.backend.academic.serializers import SemesterOfferingSerializer
from src.backend.core.models import Session, AttendanceRecord



class EnrollmentViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Enrollment.objects.all()
        return Enrollment.objects.filter(student=user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return EnrollmentCreateSerializer
        return EnrollmentSerializer

    @action(detail=True, methods=['post'])
    def withdraw(self, request, pk=None):
        enrollment = self.get_object()
        if enrollment.student != request.user and not request.user.is_staff:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
            
        enrollment.status = 'WITHDRAWN'
        enrollment.save()
        return Response({'status': 'withdrawn'})

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        if not request.user.is_staff:
            return Response({'error': 'Staff only'}, status=status.HTTP_403_FORBIDDEN)
            
        enrollment = self.get_object()
        enrollment.status = 'ENROLLED'
        enrollment.save()
        return Response({'status': 'approved'})
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get enrollment dashboard data: past enrollments and available units"""
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get all enrollments for the student
        enrollments = Enrollment.objects.filter(student=user).select_related(
            'offering', 'offering__unit'
        ).order_by('-offering__year', 'offering__semester')
        
        # Separate past and current enrollments
        now = timezone.now()
        current_year = now.year
        
        # Past enrollments: completed/failed/withdrawn OR from previous years OR past semesters
        past_enrollments = enrollments.filter(
            Q(status__in=['COMPLETED', 'FAILED', 'WITHDRAWN']) |
            Q(offering__year__lt=current_year) |
            Q(offering__year=current_year, offering__enrollment_end__lt=now)
        )
        
        # Current enrollments: pending or enrolled in current/future semesters
        current_enrollments = enrollments.filter(
            status__in=['PENDING', 'ENROLLED'],
            offering__enrollment_end__gte=now
        )
        
        # Get completed unit IDs to filter available units
        completed_unit_ids = set(
            enrollments.filter(status='COMPLETED')
            .values_list('offering__unit_id', flat=True)
        )
        
        # Get enrolled unit IDs (current and past) to exclude from available
        enrolled_unit_ids = set(
            enrollments.values_list('offering__unit_id', flat=True)
        )

        # ── Major-based filtering ─────────────────────────────────────────────
        # Determine student's course (major) from StudentProfile, if any.
        student_course = None
        try:
            from src.backend.users.models import StudentProfile
            profile = StudentProfile.objects.select_related('course').get(user=user)
            student_course = profile.course
        except Exception:
            pass

        # Build sets for efficient lookup
        # course_unit_ids  → unit IDs that belong to the student's course
        # elective_unit_ids → unit IDs marked as elective on *any* course
        course_unit_ids = None   # None means "no restriction"
        elective_unit_ids = set()

        if student_course:
            cu_qs = CourseUnit.objects.filter(course=student_course).values_list('unit_id', 'is_elective')
            course_unit_ids = set()
            for unit_id, is_elec in cu_qs:
                course_unit_ids.add(unit_id)

        # Also collect elective unit IDs across all courses
        elective_unit_ids = set(
            CourseUnit.objects.filter(is_elective=True).values_list('unit_id', flat=True)
        )

        # Get available offerings (not enrolled, active, enrollment period open)
        available_offerings_qs = SemesterOffering.objects.filter(
            is_active=True,
            enrollment_start__lte=now,
            enrollment_end__gte=now
        ).exclude(
            unit_id__in=enrolled_unit_ids
        ).select_related('unit').order_by('unit__code')

        if course_unit_ids is not None:
            # Student has a major: show units in their course OR any elective unit
            available_offerings_qs = available_offerings_qs.filter(
                Q(unit_id__in=course_unit_ids) | Q(unit_id__in=elective_unit_ids)
            )

        available_offerings = list(available_offerings_qs)

        # Annotate each offering's unit with _is_elective so UnitSerializer can read it
        for offering in available_offerings:
            unit = offering.unit
            if course_unit_ids is not None:
                # True if this unit is NOT in their major's required units
                # (i.e., it's only here because it's a global elective)
                unit._is_elective = unit.id in elective_unit_ids and unit.id not in (course_unit_ids - elective_unit_ids)
            else:
                unit._is_elective = unit.id in elective_unit_ids

        
        # Check prerequisites for each available offering
        available_with_prereqs = []
        for offering in available_offerings:
            prerequisites = offering.unit.prerequisites.all()
            prerequisites_met = True
            missing_prereqs = []
            
            if prerequisites:
                for prereq in prerequisites:
                    if prereq.id not in completed_unit_ids:
                        prerequisites_met = False
                        missing_prereqs.append({
                            'code': prereq.code,
                            'name': prereq.name
                        })
            
            available_with_prereqs.append({
                'offering': offering,
                'prerequisites_met': prerequisites_met,
                'missing_prerequisites': missing_prereqs
            })
        
        # Serialize data
        past_data = EnrollmentSerializer(past_enrollments, many=True).data
        current_data = EnrollmentSerializer(current_enrollments, many=True).data
        
        available_data = []
        for item in available_with_prereqs:
            offering_data = SemesterOfferingSerializer(item['offering']).data
            offering_data['prerequisites_met'] = item['prerequisites_met']
            offering_data['missing_prerequisites'] = item['missing_prerequisites']
            available_data.append(offering_data)
        
        # Build card view for all known offerings
        enrollment_map = {enrollment.offering_id: enrollment for enrollment in enrollments}
        offering_lookup = {enrollment.offering_id: enrollment.offering for enrollment in enrollments}
        prereq_map = {item['offering'].id: item for item in available_with_prereqs}
        
        for item in available_with_prereqs:
            offering_lookup.setdefault(item['offering'].id, item['offering'])
        
        offering_ids = list(offering_lookup.keys())
        sessions = Session.objects.filter(
            offering_id__in=offering_ids
        ).select_related('offering').order_by('date')
        session_map = defaultdict(list)
        for session in sessions:
            session_map[session.offering_id].append(session)
        
        attendance_records = AttendanceRecord.objects.filter(
            session__offering_id__in=offering_ids,
            student=user
        ).select_related('session')
        attendance_map = defaultdict(lambda: {'present': 0, 'absent': 0, 'late': 0, 'excused': 0})
        attendance_marked = defaultdict(int)
        for record in attendance_records:
            attendance_map[record.session.offering_id][record.status] += 1
            attendance_marked[record.session.offering_id] += 1
        
        def calc_hours(session_list):
            if not session_list:
                return None
            session = session_list[0]
            if not session.start_time or not session.end_time:
                return None
            start_dt = datetime.combine(session.date, session.start_time)
            end_dt = datetime.combine(session.date, session.end_time)
            return round((end_dt - start_dt).total_seconds() / 3600, 1)
        
        def human_status(enrollment_status):
            mapping = {
                'COMPLETED': 'passed',
                'FAILED': 'failed',
                'ENROLLED': 'enrolled',
                'PENDING': 'selected',
                'WITHDRAWN': 'withdrawn',
            }
            return mapping.get(enrollment_status, 'available')
        
        offering_cards = []
        for offering_id, offering in offering_lookup.items():
            serialized_offering = SemesterOfferingSerializer(offering).data
            enrollment = enrollment_map.get(offering_id)
            status_label = human_status(enrollment.status) if enrollment else 'available'
            prereq_info = prereq_map.get(offering_id)
            prerequisites_met = True
            missing_prereqs = []
            if status_label == 'available' and prereq_info:
                prerequisites_met = prereq_info['prerequisites_met']
                missing_prereqs = prereq_info['missing_prerequisites']
            
            session_list = session_map.get(offering_id, [])
            hours_per_session = calc_hours(session_list)
            total_sessions = len(session_list)
            attendance_stats = attendance_map.get(offering_id, {'present': 0, 'absent': 0, 'late': 0, 'excused': 0})
            attended = attendance_stats['present'] + attendance_stats['late'] + attendance_stats['excused']
            attendance_rate = round((attended / total_sessions) * 100, 1) if total_sessions else None

            instructor_user = None
            if session_list and session_list[0].instructor:
                instructor_user = session_list[0].instructor
            elif offering.unit.convenor:
                instructor_user = offering.unit.convenor
            instructor_data = self._serialize_instructor(instructor_user)
            
            offering_cards.append({
                'offering': serialized_offering,
                'status_label': status_label,
                'enrollment_id': enrollment.id if enrollment else None,
                'grade': enrollment.grade if enrollment else '',
                'marks': enrollment.marks if enrollment else None,
                'prerequisites_met': prerequisites_met,
                'missing_prerequisites': missing_prereqs,
                'instructor': instructor_data,
                'attendance_summary': {
                    'total_sessions': total_sessions,
                    'attended_sessions': attended,
                    'present': attendance_stats['present'],
                    'late': attendance_stats['late'],
                    'absent': attendance_stats['absent'],
                    'attendance_rate': attendance_rate,
                },
                'schedule_summary': f"{total_sessions} weeks • {hours_per_session or 3}h lecture" if total_sessions else "Schedule to be announced",
                'can_enroll': status_label == 'available' and prerequisites_met,
            })
        
        return Response({
            'past_enrollments': past_data,
            'current_enrollments': current_data,
            'available_units': available_data,
            'offering_cards': offering_cards,
            'statistics': {
                'total_completed': past_enrollments.filter(status='COMPLETED').count(),
                'total_failed': past_enrollments.filter(status='FAILED').count(),
                'total_withdrawn': past_enrollments.filter(status='WITHDRAWN').count(),
                'current_enrolled': current_enrollments.filter(status='ENROLLED').count(),
                'pending_approval': current_enrollments.filter(status='PENDING').count(),
                'available_count': len([card for card in offering_cards if card['status_label'] == 'available' and card['can_enroll']])
            }
        })

    @action(detail=False, methods=['get'], url_path='teaching')
    def teaching_summary(self, request):
        """Dashboard data for instructors/staff"""
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        if not (user.is_staff or getattr(user, 'user_type', '') in ['staff', 'unit_convenor', 'admin']):
            return Response({'error': 'Instructor or staff access required'}, status=status.HTTP_403_FORBIDDEN)

        sessions = Session.objects.filter(instructor=user).select_related('offering', 'offering__unit').order_by('date')
        offering_ids = list({session.offering_id for session in sessions})

        if not offering_ids:
            return Response({
                'classes': [],
                'summary': {
                    'total_classes': 0,
                    'total_students': 0,
                    'pending_approvals': 0,
                    'average_attendance': None,
                }
            })

        offerings = SemesterOffering.objects.filter(id__in=offering_ids).select_related('unit')
        offering_map = {offering.id: offering for offering in offerings}

        enrollments = Enrollment.objects.filter(offering_id__in=offering_ids).select_related('student')
        enrollment_map = defaultdict(list)
        for enrollment in enrollments:
            enrollment_map[enrollment.offering_id].append(enrollment)

        attendance_records = AttendanceRecord.objects.filter(
            session__offering_id__in=offering_ids,
            session__instructor=user
        ).select_related('session')
        attendance_map = defaultdict(lambda: {'present': 0, 'absent': 0, 'late': 0, 'excused': 0})
        for record in attendance_records:
            attendance_map[record.session.offering_id][record.status] += 1

        session_map = defaultdict(list)
        for session in sessions:
            session_map[session.offering_id].append(session)

        classes = []
        total_students = 0
        total_attendance_rate = 0
        offerings_with_attendance = 0
        pending_total = 0

        now = timezone.now()

        for offering_id in offering_ids:
            offering = offering_map.get(offering_id)
            if not offering:
                continue
            serialized_offering = SemesterOfferingSerializer(offering).data
            enrollment_list = enrollment_map.get(offering_id, [])
            total_students += len(enrollment_list)

            status_breakdown = defaultdict(int)
            for enrollment in enrollment_list:
                status_breakdown[enrollment.status] += 1
                if enrollment.status == 'PENDING':
                    pending_total += 1

            attendance_stats = attendance_map.get(offering_id, {'present': 0, 'absent': 0, 'late': 0, 'excused': 0})
            total_sessions = attendance_stats['present'] + attendance_stats['absent'] + attendance_stats['late'] + attendance_stats['excused']
            attended = attendance_stats['present'] + attendance_stats['late'] + attendance_stats['excused']
            attendance_rate = round((attended / total_sessions) * 100, 1) if total_sessions else None
            if attendance_rate is not None:
                total_attendance_rate += attendance_rate
                offerings_with_attendance += 1

            upcoming_session = None
            for session in session_map.get(offering_id, []):
                session_dt = datetime.combine(session.date, session.start_time or time(9, 0))
                session_dt = timezone.make_aware(session_dt) if timezone.is_naive(session_dt) else session_dt
                if session_dt >= now:
                    upcoming_session = {
                        'date': session.date.isoformat(),
                        'start_time': session.start_time.isoformat() if session.start_time else None,
                        'end_time': session.end_time.isoformat() if session.end_time else None,
                        'location': session.location,
                    }
                    break

            classes.append({
                'offering': serialized_offering,
                'students_total': len(enrollment_list),
                'status_breakdown': dict(status_breakdown),
                'attendance': {
                    'present': attendance_stats['present'],
                    'late': attendance_stats['late'],
                    'absent': attendance_stats['absent'],
                    'excused': attendance_stats['excused'],
                    'attendance_rate': attendance_rate,
                },
                'upcoming_session': upcoming_session,
            })

        avg_attendance = round(total_attendance_rate / offerings_with_attendance, 1) if offerings_with_attendance else None

        return Response({
            'classes': classes,
            'summary': {
                'total_classes': len(classes),
                'total_students': total_students,
                'pending_approvals': pending_total,
                'average_attendance': avg_attendance,
            }
        })

    def _serialize_instructor(self, user):
        if not user:
            return None
        full_name = user.get_full_name().strip()
        display_name = full_name or user.username or user.email
        return {
            'id': user.id,
            'name': display_name,
            'email': user.email,
            'position': getattr(user, 'position', ''),
        }


class TranscriptViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing academic transcripts"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TranscriptSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Transcript.objects.all()
        return Transcript.objects.filter(student=user)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get transcript summary with GPA calculation"""
        user = request.user
        transcripts = Transcript.objects.filter(
            student=user,
            status='COMPLETED',
            grade_point__isnull=False
        )
        
        total_points = 0
        total_credits = 0
        
        for transcript in transcripts:
            if transcript.grade_point and transcript.credit_points:
                total_points += float(transcript.grade_point) * transcript.credit_points
                total_credits += transcript.credit_points
        
        gpa = (total_points / total_credits) if total_credits > 0 else 0
        
        return Response({
            'gpa': round(gpa, 2),
            'total_credit_points': total_credits,
            'total_units_completed': transcripts.count()
        })