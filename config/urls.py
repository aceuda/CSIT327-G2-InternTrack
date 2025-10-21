"""
URL configuration for interntrack_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from interntrack_app import views
from interntrack_app.views import AdminRegisterView, AttendanceAPIView, CustomTokenView, DashboardView, LoginView, RegisterView, StudentProfileView, profile_page

from .router import router
from django.conf.urls.static import static

#Define endpoints for both HTML pages and API routes
urlpatterns = [
    path('admin/', admin.site.urls), 
    path('auth/login/', CustomTokenView.as_view(), name='token_obtain_pair'),
    path('login/', LoginView.as_view(), name='login'),   # include your app urls
    path("register/", RegisterView.as_view(), name="register"),
    path('register/admin/', AdminRegisterView.as_view(), name='admin_register'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('attendance/', AttendanceAPIView.as_view(), name='attendance'),
    path('company-details/', views.company_details_view, name='company_details'),
    path('progress-tracker/', views.progress_tracker_view, name='progress_tracker'),
    path('evaluation-results/', views.evaluation_results_view, name='evaluation_results'),
    path('profile/', StudentProfileView.as_view(), name='student-profile-api'),
    path('profile/view/', profile_page, name='student-profile-page'),
    path('log-hours/', views.log_hours_view, name='log_hours'),
    path('submit-report/', views.submit_report_view, name='submit_report'),
    path('download-forms/', views.download_forms_view, name='download_forms'),
    path('contact-supervisor/', views.contact_supervisor_view, name='contact_supervisor'),
    path('logout/', views.logout_view, name='logout'),

    # redirect root URL to login
    path('', lambda request: redirect('login')),  
    path('', include(router.urls)),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(), name='schema_swagger_ui'),
    
] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

