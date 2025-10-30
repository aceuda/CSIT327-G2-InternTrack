from urllib import request
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from interntrack_app.models import AdminProfile, Attendance, StudentProfile
from interntrack_app.serializers import AdminProfileSerializer, BaseUserSerializer, CustomTokenObtainPairSerializer, StudentProfileSerializer
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
        # Admin Dashboard
        if getattr(user, "user_type", None) == 'admin':
            admin_profile = getattr(user, "admin_profile", None)
            return Response(
                {"user": user, "admin_profile": admin_profile},
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
    
def admin_profile_page(request):
    """
    Render the admin_profile.html template.
    This page will interact with AdminProfileView using fetch() or AJAX.
    """
    return render(request, 'admin_profile.html')

# LOGOUT
def logout_view(request):
    logout(request)
    return render(request, "logout.html")
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

    return render(request, 'evaluation_results.html', {
        "student_profile": student_profile,  # ✅ Pass profile to template
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