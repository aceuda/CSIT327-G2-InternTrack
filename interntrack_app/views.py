from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# ✅ LOGIN with email
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email or not password:
            messages.error(request, "Please enter both email and password")
            return render(request, 'login.html')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "No account found with that email")
            return render(request, 'login.html')

        user = authenticate(request, username=user.username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Welcome back!")
            return redirect('dashboard')
        else:
            messages.error(request, "Incorrect password")
            return render(request, 'login.html')

    return render(request, 'login.html')


# ✅ REGISTER with new fields
def register_view(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        suffix = request.POST.get("suffix") or ""
        birthdate = request.POST.get("birthdate")
        year_level = request.POST.get("year_level")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return redirect("register")

        # Generate a username from email (or use any unique logic)
        username = email.split("@")[0]
        counter = 1
        original_username = username
        while User.objects.filter(username=username).exists():
            username = f"{original_username}{counter}"
            counter += 1

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name
        )

        # Optional: store extra fields (suffix, birthdate, year_level) — needs profile model
        # For now, just show a success message
        messages.success(request, "Account created successfully! Please log in.")
        return redirect("login")

    return render(request, "register.html")


# ✅ Protected Dashboard
@login_required
def dashboard_view(request):
    return render(request, "dashboard.html")


# ✅ Logout
def logout_view(request):
    logout(request)
    return render(request, "logout.html")
    return redirect("login")
