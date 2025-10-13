from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from interntrack_app.serializers import BaseUserSerializer, CustomTokenObtainPairSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import viewsets

#Creates & authenticates users via HTML forms
#Handles the logic (HTML forms or API requests)
User = get_user_model()

# LOGIN(Handles login)
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request, "Please enter both username and password")
            return render(request, 'interntrack_app/login.html')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            print("✅ User logged in:", user.username)
            login(request, user)
            messages.success(request, "Welcome back! Successfully logged in")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid credentials")
            return render(request, 'login.html')

    return render(request, 'login.html')


# REGISTER
# def register_view(request):
#     if request.method == "POST":
#         username = request.POST.get("username")
#         email = request.POST.get("username")
#         password1 = request.POST.get("password1")
#         password2 = request.POST.get("password2")

#         if password1 != password2:
#             messages.error(request, "Passwords do not match")
#             return redirect("register")

#         if User.objects.filter(username=username).exists():
#             messages.error(request, "Username already taken")
#             return redirect("register")

#         if User.objects.filter(email=email).exists():
#             messages.error(request, "Email already registered")
#             return redirect("register")

#         # Create user
#         User.objects.create_user(username=username, email=email, password=password1)
#         messages.success(request, "Account created successfully! Please log in.")
#         return redirect("login")

#     return render(request, "register.html")
#Handle User Registration
def register_view(request):
    if request.method == "POST":
        data = request.POST
        username = data.get("username")  
        email = data.get("email")
        password1 = data.get("password1")
        password2 = data.get("password2")

        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return redirect("register")

        # Create user using your custom manager
        User.objects.create_user(
            username=username,
            email = email,
            password=password1,
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            birthdate=data.get("birthdate"),
            year_level=data.get("year_level"),
            user_type="student"  # default role
        )

        messages.success(request, "Account created successfully! Please log in.")
        return redirect("login")

    return render(request, "register.html")


# DASHBOARD (protected)
# @login_required
# def dashboard_view(request):
#     #print("Logged in user:", request.user)  # ✅ This will show in your terminal
#     return render(request, "dashboard.html", {
#         "user": request.user
#     })
#Diplay the dashboard after login
@login_required
def dashboard_view(request):
    user = request.user

    if user.user_type == 'admin':
        # Redirect to admin dashboard or render a different template
        return render(request, "admin_dashboard.html", {"user": user})
    
    # Default student dashboard
    return render(request, "dashboard.html", {"user": user})



# LOGOUT
def logout_view(request):
    logout(request)
    return render(request, "logout.html")
    return redirect("login")

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