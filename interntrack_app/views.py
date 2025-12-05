from urllib import request
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from interntrack_app.models import AdminProfile, Attendance, StudentProfile
from interntrack_app.serializers import AdminProfileSerializer, BaseUserSerializer, CustomTokenObtainPairSerializer, StudentProfileSerializer, AttendanceSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework import status, renderers
from django.utils.decorators import method_decorator
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from django.views.decorators.csrf import csrf_exempt
from interntrack_app.utils import normalize_admin_data, normalize_student_data
from .models import StudentProfile, Attendance, Evaluation  # adjust model imports as needed
from django.db import models
from django.core.paginator import Paginator
from django.db.models import Q

#Creates & authenticates users via HTML forms
#Handles the logic (HTML forms or API requests)
User = get_user_model()

# LOGIN(Handles login)
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    renderer_classes = [renderers.TemplateHTMLRenderer, renderers.JSONRenderer]
    template_name = 'login.html'

    def get(self, request):
        # Render login page
        return Response({}, template_name=self.template_name)

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        # Validate input
        if not username or not password:
            messages.error(request, "Please enter both username and password")
            return Response({}, template_name=self.template_name, status=status.HTTP_400_BAD_REQUEST)

        # Authenticate user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)  # ✅ Logs the user in (session created)
            messages.success(request, f"Welcome back")

            # ✅ Return a proper HTTP redirect (so session persists)
            response = redirect('dashboard')
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            return response

        # Invalid credentials
        messages.error(request, "Invalid credentials")
        return Response({}, template_name=self.template_name, status=status.HTTP_401_UNAUTHORIZED)

class AdminRegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    renderer_classes = [renderers.TemplateHTMLRenderer, renderers.JSONRenderer]
    template_name = 'admin_register.html'

    def get(self, request):
        """Render admin registration page for browser users."""
        return Response({}, template_name=self.template_name)

    def post(self, request):
        data = request.data
        username = data.get("username")
        email = data.get("email")
        password1 = data.get("password1")
        password2 = data.get("password2")

        # Password check
        if password1 != password2:
            return Response(
                {"error": "Passwords do not match"},
                status=status.HTTP_400_BAD_REQUEST,
                template_name=self.template_name
            )
        
        if len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters long!')
            return render(request, 'admin_register.html')

        # Username and email checks
        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Username already taken"},
                status=status.HTTP_400_BAD_REQUEST,
                template_name=self.template_name
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "Email already registered"},
                status=status.HTTP_400_BAD_REQUEST,
                template_name=self.template_name
            )

        # Create the user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            birthdate=data.get("birthdate"),
            user_type="admin"
        )

        # Create AdminProfile
        admin_data = normalize_admin_data(data)
        AdminProfile.objects.create(
            user=user,
            department=admin_data.get("department"),
            position=admin_data.get("position"),
            employee_id=admin_data.get("employee_id")
        )

        # Redirect browser, or respond JSON
        if request.accepted_renderer.format == 'html':
            return redirect("login")

        return Response(
            {"message": "Admin account created successfully! Please log in."},
            status=status.HTTP_201_CREATED
        )


#Handle User Registration
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    renderer_classes = [renderers.TemplateHTMLRenderer, renderers.JSONRenderer]
    template_name = 'register.html'

    def get(self, request):
        """Render the registration form for browsers."""
        return Response({}, template_name=self.template_name)

    def post(self, request):
        data = request.data
        username = data.get("username")
        email = data.get("email")
        password1 = data.get("password1")
        password2 = data.get("password2")

        # Password check
        if password1 != password2:
            return Response(
                {"error": "Passwords do not match"},
                status=status.HTTP_400_BAD_REQUEST,
                template_name=self.template_name
            )
        
        if len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters long!')
            return render(request, 'register.html')

        # Username and email checks
        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Username already taken"},
                status=status.HTTP_400_BAD_REQUEST,
                template_name=self.template_name
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "Email already registered"},
                status=status.HTTP_400_BAD_REQUEST,
                template_name=self.template_name
            )

        # Create the user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            birthdate=data.get("birthdate"),
            user_type="student"
        )

        # Normalize and create StudentProfile
        student_data = normalize_student_data(data)
        StudentProfile.objects.create(
            user=user,
            year_level=student_data.get("year_level"),
            program=student_data.get("program"),
            student_id=student_data.get("student_id")
        )

        # Respond with success message
        Response(
            {"message": "Account created successfully! Please log in."},
            status=status.HTTP_201_CREATED,
            template_name=self.template_name
        )
        
        return redirect("login")

@method_decorator(login_required, name='dispatch')
class DashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [renderers.TemplateHTMLRenderer]

    def get(self, request):
        user = request.user

        # Admin Dashboard
        if getattr(user, "user_type", None) == 'admin':
            admin_profile = getattr(user, "admin_profile", None)
            
            # Live intern count
            total_interns = StudentProfile.objects.count()
            
            # Attendance statistics (all interns, today)
            today = timezone.now().date()
            today_attendance = Attendance.objects.filter(date=today)
            
            present_count = today_attendance.filter(
                time_in__isnull=False,
                time_out__isnull=False
            ).count()
            absent_count = today_attendance.filter(time_in__isnull=True).count()
            pending_count = today_attendance.filter(
                time_in__isnull=False,
                time_out__isnull=True
            ).count()
            
            # Pending evaluations count
            pending_evaluations = Evaluation.objects.filter(
                remarks__isnull=True
            ).count()
            
            # Overall attendance rate (all time)
            total_attendance_days = Attendance.objects.count()
            present_days = Attendance.objects.filter(
                time_in__isnull=False,
                time_out__isnull=False
            ).count()
            attendance_rate = (present_days / total_attendance_days * 100) if total_attendance_days > 0 else 0
            
            # Recent activities (last 10 attendance records or evaluations)
            recent_activities = []
            
            # Get recent evaluations
            recent_evals = Evaluation.objects.select_related('student__user').order_by('-date_evaluated')[:5]
            for eval_record in recent_evals:
                recent_activities.append({
                    'intern_name': eval_record.student.full_name,
                    'company': eval_record.student.program,  # Using program as placeholder
                    'action': 'Evaluation Submitted',
                    'date': eval_record.date_evaluated.strftime('%b %d'),
                    'type': 'evaluation',
                })
            
            # Get recent attendance changes (time_out logged)
            recent_attendance = Attendance.objects.select_related('student__user').filter(
                time_out__isnull=False
            ).order_by('-date')[:5]
            for att_record in recent_attendance:
                recent_activities.append({
                    'intern_name': att_record.student.full_name,
                    'company': att_record.student.program,
                    'action': 'Attendance Logged',
                    'date': att_record.date.strftime('%b %d'),
                    'type': 'attendance',
                })
            
            # Sort and limit to 5 most recent
            recent_activities = sorted(recent_activities, key=lambda x: x['date'], reverse=True)[:5]

            # Prepare recent evaluations list for template (last 5)
            recent_evals_list = [
                {
                    'intern_name': r.student.full_name,
                    'date': r.date_evaluated.strftime('%b %d'),
                    'id': r.id
                }
                for r in recent_evals[:5]
            ]

            # Total evaluations count
            evaluation_count = Evaluation.objects.count()
            
            # Weekly attendance trends (past 4 weeks)
            from datetime import timedelta as td
            weekly_data = []
            for week_offset in range(4):
                week_start = today - td(days=(week_offset * 7) + 7)
                week_end = today - td(days=week_offset * 7)
                
                week_attendance = Attendance.objects.filter(
                    date__gte=week_start,
                    date__lt=week_end
                )
                
                week_present = week_attendance.filter(
                    time_in__isnull=False,
                    time_out__isnull=False
                ).count()
                week_total = week_attendance.count()
                week_rate = (week_present / week_total * 100) if week_total > 0 else 0
                
                weekly_data.insert(0, {
                    'week': f"Week {5 - week_offset}",
                    'start_date': week_start.strftime('%b %d'),
                    'end_date': week_end.strftime('%b %d'),
                    'present': week_present,
                    'total': week_total,
                    'rate': round(week_rate, 1),
                })
            
            return Response(
                {
                    "user": user,
                    "admin_profile": admin_profile,
                    "total_interns": total_interns,
                    "present_count": present_count,
                    "absent_count": absent_count,
                    "pending_count": pending_count,
                    "pending_evaluations": pending_evaluations,
                    "attendance_rate": round(attendance_rate, 1),
                    "recent_activities": recent_activities,
                    "recent_evals": recent_evals_list,
                    "evaluation_count": evaluation_count,
                    "weekly_data": weekly_data,
                },
                template_name="admin_dashboard.html"
            )

        # Student Dashboard
        profile = StudentProfile.objects.filter(user=user).first()

        recent_logs = []
        if profile:
            attendance_qs = Attendance.objects.filter(student=profile).order_by('-date')[:5]
            for log in attendance_qs:
                if not log.time_in:
                    status = 'Absent'
                elif not log.time_out:
                    status = 'Pending'
                else:
                    status = 'Present'
                recent_logs.append({
                    "date": log.date,
                    "hours": log.hours_rendered,
                    "status": status,
                })

        # Attendance rate
        if profile:
            total_days = Attendance.objects.filter(student=profile).count()
            present_days = Attendance.objects.filter(
                student=profile,
                time_in__isnull=False,
                time_out__isnull=False
            ).count()
        else:
            total_days = present_days = 0

        attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0

        # OJT hours
        if profile:
            hours_agg = Attendance.objects.filter(student=profile).aggregate(total=models.Sum('hours_rendered'))
            completed_hours = hours_agg.get('total') or 0
        else:
            completed_hours = 0

        total_hours = 400
        progress_percentage = (completed_hours / total_hours * 100) if total_hours > 0 else 0

        # Evaluation
        evaluation = None
        overall_score = None
        evaluation_remarks = None
        if profile:
            evaluation = Evaluation.objects.filter(student=profile).order_by('-date_evaluated').first()
            if evaluation:
                overall_score = getattr(evaluation, 'score', None)
                evaluation_remarks = getattr(evaluation, 'remarks', '')

        evaluation_status = "Completed" if evaluation else "Pending"

        context = {
            "user": user,
            "student_profile": profile,
            "attendance_rate": round(attendance_rate, 1),
            "recent_logs": recent_logs,
            "completed_hours": int(completed_hours),
            "total_hours": total_hours,
            "progress_percentage": int(progress_percentage),
            "evaluation_status": evaluation_status,
            "overall_score": overall_score,
            "evaluation_remarks": evaluation_remarks,
        }

        return Response(context, template_name="dashboard.html")

class AttendanceAPIView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [renderers.TemplateHTMLRenderer, renderers.JSONRenderer]
    template_name = 'attendance.html'

    def get(self, request):
        """Render the attendance page with today's record."""
        try:
            student = StudentProfile.objects.get(user=request.user)
        except StudentProfile.DoesNotExist:
            return Response({"error": "Student profile not found"}, template_name=self.template_name)

        today = timezone.localdate()
        attendance = Attendance.objects.filter(student=student, date=today).first()
        recent_logs = Attendance.objects.filter(student=student).order_by('-date')[:7]  # ✅ Added this line

        return Response({
            "student_profile": student, 
            "attendance": attendance,
            "today": today,
            "recent_logs": recent_logs,  # ✅ Added this line
        }, template_name=self.template_name)

    def post(self, request):
        """Handle Time In / Time Out button clicks."""
        try:
            student = StudentProfile.objects.get(user=request.user)
        except StudentProfile.DoesNotExist:
            return Response({"error": "Student profile not found"}, template_name=self.template_name)

        today = timezone.localdate()
        now = timezone.localtime()

        attendance, _ = Attendance.objects.get_or_create(student=student, date=today)

        # Handle Time In
        if 'time_in' in request.POST and not attendance.time_in:
            attendance.time_in = now.time()
            attendance.save()
            message = "✅ Time In recorded successfully."

        # Handle Time Out
        elif 'time_out' in request.POST and attendance.time_in and not attendance.time_out:
            attendance.time_out = now.time()
            attendance.calculate_hours()
            attendance.save()
            message = "✅ Time Out recorded successfully."

        else:
            message = "⚠️ You’ve already timed out for today or invalid action."

        recent_logs = Attendance.objects.filter(student=student).order_by('-date')[:7]  # ✅ Added this line

        return Response({
            "student_profile": student, 
            "attendance": attendance,
            "today": today,
            "recent_logs": recent_logs,  # ✅ Added this line
            "message": message
        }, template_name=self.template_name)

    
#Profile Management
@method_decorator(csrf_exempt, name='dispatch')
class StudentProfileView(APIView):
    """
    APIView for managing the logged-in student's profile (CRUD).
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Retrieve the current user's profile"""
        profile = get_object_or_404(StudentProfile, user=request.user)
        serializer = StudentProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new profile (only if user doesn’t have one yet)"""
        if hasattr(request.user, 'student_profile'):
            return Response({'detail': 'Profile already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = StudentProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        """Update current user's profile (partial updates allowed)"""
        profile = get_object_or_404(StudentProfile, user=request.user)
        serializer = StudentProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Delete current user's profile"""
        profile = get_object_or_404(StudentProfile, user=request.user)
        profile.delete()
        return Response({'detail': 'Profile deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)


def profile_page(request):
    """
    Render the profile.html template.
    This page will interact with StudentProfileView using fetch() or AJAX.
    """
    return render(request, 'profile.html')


@method_decorator(csrf_exempt, name='dispatch')
class AdminProfileView(APIView):
    """
    APIView for managing the logged-in admin's profile (CRUD).
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Retrieve the current user's profile"""
        profile = get_object_or_404(AdminProfile, user=request.user)
        serializer = AdminProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new profile (only if user doesn’t have one yet)"""
        if hasattr(request.user, 'admin_profile'):
            return Response({'detail': 'Profile already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AdminProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        """Update current user's profile (partial updates allowed)"""
        profile = get_object_or_404(AdminProfile, user=request.user)
        serializer = AdminProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            print("Incoming data:", request.data)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Delete current user's profile"""
        profile = get_object_or_404(AdminProfile, user=request.user)
        profile.delete()
        return Response({'detail': 'Profile deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)
    
class AdminProfilePage(APIView):
   def get(self, request):
        return render(request, 'admin_profile.html')

# LOGOUT
def logout_view(request):
    logout(request)
    return render(request, "login.html")
    #return redirect("login")

User = get_user_model()
#Provides full CRUD API for User
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = BaseUserSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]
    
#Handles API-based login via JWT
class CustomTokenView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

#----------------------------------------------------------------------
@login_required
def attendance_log_view(request):
    return render(request, 'attendance.html')

@login_required
def company_details_view(request):
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        student_profile = None

    return render(request, 'company_details.html', {
        "student_profile": student_profile,  # ✅ Pass this to template
    })

@login_required
def progress_tracker_view(request):
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        student_profile = None

    return render(request, 'progress_tracker.html', {
        "student_profile": student_profile,  # ✅ Pass profile to template
    })

@login_required
def evaluation_results_view(request):
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        student_profile = None

    evaluation = None
    if student_profile:
        evaluation = Evaluation.objects.filter(student=student_profile).order_by('-date_evaluated').first()

    return render(request, 'evaluation_results.html', {
        "student_profile": student_profile,  # ✅ Pass profile to template
        "evaluation": evaluation,
    })

@login_required
def profile_view(request):
    return render(request, 'profile.html')

@login_required
def log_hours_view(request):
    # You can expand this later; for now, just render a placeholder
    return render(request, 'log_hours.html')

@login_required
def submit_report_view(request):
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        student_profile = None

    return render(request, 'submit_report.html', {
        "student_profile": student_profile,  # ✅ Pass profile to template
    })

@login_required
def download_forms_view(request):
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        student_profile = None

    return render(request, 'download_forms.html', {
        "student_profile": student_profile,  # ✅ Pass profile to template
    })

@login_required
def contact_supervisor_view(request):
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        student_profile = None

    return render(request, 'contact_supervisor.html', {
        "student_profile": student_profile,  # ✅ Pass profile to template
    })

@method_decorator(login_required, name='dispatch')
class ManageInternView(APIView):
    def get(self, request):
        search_query = request.GET.get('search', '')
        profiles = StudentProfile.objects.all()
        paginator = Paginator(profiles, 10)  # Show 10 interns per page
        serializer = StudentProfileSerializer(profiles, many=True)

        if search_query:
            profiles = profiles.filter(Q(full_name__icontains=search_query))

        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        return render(request, 'manage_interns.html', {'page_obj': page_obj,'search_query': search_query,'profiles': serializer.data})

    def delete(self, request, *args, **kwargs):
        student_id = request.data.get('id')
        student = get_object_or_404(StudentProfile, id=student_id)
        student.delete()
        return JsonResponse({'message': 'Intern deleted successfully'})

    # def post(self, request):
    #     data = request.data
    #     return render(request, 'manage_intern.html', {'data': data})

class EvaluationView(APIView):
    def get(self, request):
        interns = StudentProfile.objects.all()

        intern_table = []
        for intern in interns:
            evaluated = Evaluation.objects.filter(student=intern).exists()
            latest_eval = Evaluation.objects.filter(student=intern).order_by('-date_evaluated').first()
            intern_table.append({
                "id": intern.id,
                "full_name": intern.full_name,
                "program": intern.program,
                "evaluated": evaluated,
                "eval_id": latest_eval.id if latest_eval else None
            })

        return Response(
            {"interns": intern_table},
            status=status.HTTP_200_OK
        )

    def post(self, request):
        """Create a new Evaluation for a student.

        Expected JSON body:
        {
            "student_id": 1,
            "q1": 4, "q2": 5, ..., "q10": 3,
            "remarks": "..."
        }
        """
        data = request.data
        student_id = data.get('student_id')
        if not student_id:
            return Response({'error': 'student_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            student = StudentProfile.objects.get(id=student_id)
        except StudentProfile.DoesNotExist:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

        # Prevent duplicate evaluation: do not allow a student to be evaluated more than once
        if Evaluation.objects.filter(student=student).exists():
            return Response({'error': 'Student has already been evaluated'}, status=status.HTTP_400_BAD_REQUEST)

        # Collect q1..q10 safely
        q_values = {}
        for i in range(1, 11):
            key = f'q{i}'
            val = data.get(key)
            try:
                q_values[key] = int(val) if val is not None and val != '' else None
            except (ValueError, TypeError):
                q_values[key] = None

        remarks = data.get('remarks', '')

        evaluation = Evaluation.objects.create(
            student=student,
            q1=q_values.get('q1'), q2=q_values.get('q2'), q3=q_values.get('q3'), q4=q_values.get('q4'),
            q5=q_values.get('q5'), q6=q_values.get('q6'), q7=q_values.get('q7'), q8=q_values.get('q8'),
            q9=q_values.get('q9'), q10=q_values.get('q10'),
            remarks=remarks
        )

        return Response({'message': 'Evaluation saved', 'evaluation_id': evaluation.id}, status=status.HTTP_201_CREATED)

    
@method_decorator(login_required, name='dispatch')
class ManageCompanyView(APIView):
    def get(self, request):
        return render(request, 'manage_companies.html')

@method_decorator(login_required, name='dispatch')
class AttendanceRecordsView(APIView):
    def get(self, request):
        # Get search query from the GET parameters
        search_query = request.GET.get('search', '')

        # Fetch attendance records and filter based on search query
        attendance_records = Attendance.objects.all().order_by('-date')  # Order by date or any other field

        if search_query:
            # Filter by intern's full name or date
            attendance_records = attendance_records.filter(
                Q(student__full_name__icontains=search_query) |
                Q(date__icontains=search_query)
            )

        # Pagination: 10 records per page
        paginator = Paginator(attendance_records, 10)  # Show 10 records per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Prepare the attendance data to be passed to the template
        attendance_data = []
        for record in page_obj:
            # Fetch the associated student profile
            student_profile = record.student  # The related StudentProfile object
            
            attendance_data.append({
                'id': record.id,
                'intern_name': student_profile.full_name,
                'date': record.date,
                'time_in': record.time_in,
                'time_out': record.time_out,
                'status': "Present" if record.time_out else "Absent",
            })

        # Pass the paginated data, search query, and student data to the template
        return render(request, 'attendance_records.html', {
            'page_obj': page_obj,
            'attendance_data': attendance_data,  # Pass the list of attendance data to the template
            'search_query': search_query,
        })

    def delete(self, request, *args, **kwargs):
        """Delete an attendance record."""
        attendance_id = request.data.get('id')
        attendance = get_object_or_404(Attendance, id=attendance_id)
        attendance.delete()
        return JsonResponse({'message': 'Attendance record deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

@method_decorator(login_required, name='dispatch')
class EvaluationsView(APIView):
    def get(self, request):
        return render(request, 'evaluations.html')


@login_required
def evaluation_detail_view(request, eval_id):
    # Fetch evaluation or 404
    evaluation = get_object_or_404(Evaluation, id=eval_id)

    user = request.user
    # Permission: admin can view any; students can view their own evaluation
    is_admin = getattr(user, 'user_type', None) == 'admin'
    is_owner = False
    try:
        if hasattr(user, 'student_profile') and evaluation.student == user.student_profile:
            is_owner = True
    except Exception:
        is_owner = False

    if not (is_admin or is_owner):
        messages.error(request, 'You do not have permission to view this evaluation.')
        return redirect('dashboard')

    # Human-readable question labels (keep in sync with frontend questionnaire)
    questions = [
        ('q1', 'How effectively did the intern complete their tasks and meet deadlines?'),
        ('q2', 'Did the intern demonstrate a clear understanding of their responsibilities?'),
        ('q3', "How would you rate the intern's technical skills relevant to the role?"),
        ('q4', 'Did the intern show improvement in their skills during the internship?'),
        ('q5', 'How well did the intern communicate with team members and supervisors?'),
        ('q6', 'Did the intern contribute ideas or suggestions during team discussions?'),
        ('q7', 'Did the intern show a willingness to learn new skills and tasks?'),
        ('q8', 'How well did the intern take feedback and apply it to improve their work?'),
        ('q9', 'How satisfied are you with the intern’s overall performance?'),
        ('q10', 'Additional numeric question (if any)')
    ]

    # Build a list of (label, value) for template
    score_items = []
    for key, label in questions:
        score_items.append((label, getattr(evaluation, key, None)))

    return render(request, 'evaluation_detail.html', {
        'evaluation': evaluation,
        'questions': {},  # legacy; not used by template
        'score_items': score_items,
    })


@method_decorator(login_required, name='dispatch')
class ReportsView(APIView):
    def get(self, request):
        return render(request, 'reports.html')


@method_decorator(login_required, name='dispatch')
class SettingsView(APIView):
    def get(self, request):
        return render(request, 'settings.html')


class EvaluationDetailAPIView(APIView):
    """API endpoint to fetch evaluation details as JSON."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, eval_id):
        evaluation = get_object_or_404(Evaluation, id=eval_id)
        user = request.user
        is_admin = getattr(user, 'user_type', None) == 'admin'
        is_owner = False
        try:
            if hasattr(user, 'student_profile') and evaluation.student == user.student_profile:
                is_owner = True
        except Exception:
            is_owner = False
        if not (is_admin or is_owner):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        questions = [
            ('q1', 'How effectively did the intern complete their tasks and meet deadlines?'),
            ('q2', 'Did the intern demonstrate a clear understanding of their responsibilities?'),
            ('q3', "How would you rate the intern's technical skills relevant to the role?"),
            ('q4', 'Did the intern show improvement in their skills during the internship?'),
            ('q5', 'How well did the intern communicate with team members and supervisors?'),
            ('q6', 'Did the intern contribute ideas or suggestions during team discussions?'),
            ('q7', 'Did the intern show a willingness to learn new skills and tasks?'),
            ('q8', 'How well did the intern take feedback and apply it to improve their work?'),
            ('q9', 'How satisfied are you with the intern\'s overall performance?'),
            ('q10', 'Additional numeric question (if any)')
        ]
        scores = {}
        for key, label in questions:
            scores[key] = {
                'label': label,
                'value': getattr(evaluation, key, None)
            }
        return Response({
            'id': evaluation.id,
            'student_name': evaluation.student.full_name,
            'program': evaluation.student.program,
            'date_evaluated': evaluation.date_evaluated.strftime('%b %d, %Y'),
            'remarks': evaluation.remarks or 'No remarks provided.',
            'scores': scores
        }, status=status.HTTP_200_OK)


class ChangePasswordAPIView(APIView):
    """API endpoint to change user password"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        # Validate inputs
        if not current_password or not new_password:
            return Response(
                {'error': 'Current password and new password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if current password is correct
        if not user.check_password(current_password):
            return Response(
                {'error': 'Current password is incorrect.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Validate new password
        if len(new_password) < 8:
            return Response(
                {'error': 'New password must be at least 8 characters long.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Set new password
        user.set_password(new_password)
        user.save()

        return Response(
            {'message': 'Password changed successfully.'},
            status=status.HTTP_200_OK
        )
