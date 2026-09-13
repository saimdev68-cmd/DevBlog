from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Profile, EmailVerificationOTP


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    ordering = ['email']
    list_display = ['email', 'first_name', 'last_name', 'is_email_verified', 'is_staff', 'is_active', 'date_joined']
    list_filter = ['is_email_verified', 'is_staff', 'is_superuser', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Verification & Permissions'), {
            'fields': ('is_email_verified', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('email', 'password1', 'password2'),
            },
        ),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'website', 'github', 'linkedin', 'twitter', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'bio']


@admin.register(EmailVerificationOTP)
class EmailVerificationOTPAdmin(admin.ModelAdmin):
    list_display = ['user', 'otp_code', 'is_used', 'is_expired', 'attempts', 'created_at', 'expires_at']
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__email', 'otp_code']
    readonly_fields = ['created_at']

