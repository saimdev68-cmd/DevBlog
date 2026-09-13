from django.contrib.auth import views as auth_views
from django.urls import path
from . import forms, views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('google/login/', views.google_login_view, name='google_login'),
    path('google/login/callback/', views.google_callback_view, name='google_callback'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),
    path('profile/', views.current_profile_view, name='current_profile'),
    path('profile/<int:pk>/', views.AuthorProfileView.as_view(), name='author_profile'),
    path('user/<int:pk>/', views.AuthorProfileView.as_view(), name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/update/', views.update_profile_view, name='update_profile'),
    path('profile/change-password/', views.change_password_ajax_view, name='change_password_ajax'),

    # Email Change (Dedicated Page & Verified OTP API)
    path('email-change/', views.email_change_view, name='email_change'),
    path('email-change/request/', views.request_email_change_view, name='request_email_change'),
    path('email-change/verify/', views.verify_email_change_view, name='verify_email_change'),
    path('email-change/resend/', views.resend_email_change_otp_view, name='resend_email_change_otp'),

    # Password Reset
    path('password-reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password/password_reset_done.html'
    ), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password/password_reset_complete.html'
    ), name='password_reset_complete'),

    # Password Change (Authenticated)
    path('password-change/', views.PasswordChangeView.as_view(), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password/password_change_done.html'
    ), name='password_change_done'),
]
