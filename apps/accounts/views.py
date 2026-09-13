import logging
import secrets
from urllib.parse import urlencode
import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash, views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView as BaseLoginView
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import CreateView, DetailView, UpdateView
from .emails import send_email_change_otp
from .forms import (
    EmailChangeRequestForm,
    EmailChangeVerifyForm,
    LoginForm,
    PasswordChangeForm,
    PasswordResetForm,
    ProfileUpdateForm,
    RegisterForm,
    SetPasswordForm,
    UserUpdateForm,
)
from .models import Profile, User, EmailVerificationOTP



def mask_email(email):
    """Mask email for display: e.g. j***e@example.com"""
    if not email or '@' not in email:
        return email
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        masked_local = local[0] + '*'
    else:
        masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:verify_otp')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('core:home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_email_verified = False
        user.save()

        # Generate 6-digit OTP and send email (terminal in dev)
        EmailVerificationOTP.generate_otp_for_user(user)

        # Store email in session for the verification step
        self.request.session['verify_email'] = user.email

        messages.info(
            self.request,
            f"Account created! We've sent a 6-digit verification code to {user.email}. Please enter it below to activate your account."
        )
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'redirect_url': str(self.success_url)})
        return redirect(self.success_url)

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = [str(e) for e in field_errors]
            return JsonResponse({'success': False, 'errors': errors}, status=400)
        return super().form_invalid(form)


class LoginView(BaseLoginView):
    form_class = LoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        redirect_to = self.get_redirect_url()
        if redirect_to and url_has_allowed_host_and_scheme(url=redirect_to, allowed_hosts={self.request.get_host()}):
            return redirect_to
        if self.request.user.is_staff:
            return str(reverse_lazy('dashboard:index'))
        return str(reverse_lazy('core:home'))

    def form_valid(self, form):
        user = form.get_user()
        if not getattr(user, 'is_email_verified', True):
            # Unverified account: block login until OTP verification is completed
            self.request.session['verify_email'] = user.email
            active_otp = EmailVerificationOTP.objects.filter(user=user, is_used=False).first()
            if not active_otp or active_otp.is_expired:
                EmailVerificationOTP.generate_otp_for_user(user)

            warning_message = "Your email address is not verified yet. We have sent a verification code to your email. Please verify your account to sign in."
            messages.warning(self.request, warning_message)

            if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'unverified': True,
                    'redirect_url': str(reverse_lazy('accounts:verify_otp')),
                    'errors': {'__all__': [warning_message]}
                }, status=400)
            return redirect('accounts:verify_otp')

        messages.success(self.request, "Welcome back!")
        response = super().form_valid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'redirect_url': self.get_success_url()})
        return response

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = [str(e) for e in field_errors]
            return JsonResponse({'success': False, 'errors': errors}, status=400)
        return super().form_invalid(form)


def verify_otp_view(request):
    """View to handle OTP code input and verification."""
    if request.user.is_authenticated:
        return redirect('core:home')

    email = request.session.get('verify_email') or request.POST.get('email', '').strip() or request.GET.get('email', '').strip()
    user = User.objects.filter(email__iexact=email).first() if email else None

    if not user:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': "Please enter your email or sign up to verify your account."}, status=400)
        messages.warning(request, "Please enter your email or sign up to verify your account.")
        return redirect('accounts:register')

    if user.is_email_verified:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'redirect_url': str(reverse_lazy('accounts:login')), 'message': "Your email is already verified. Please sign in."}, status=400)
        messages.info(request, "Your email is already verified. Please sign in.")
        return redirect('accounts:login')


    if request.method == 'POST':
        otp_code = request.POST.get('otp_code', '').strip()

        if not otp_code or len(otp_code) != 6 or not otp_code.isdigit():
            err = "Please enter a valid 6-digit numeric verification code."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': {'otp_code': [err]}}, status=400)
            messages.error(request, err)
            return render(request, 'accounts/verify_otp.html', {
                'email': email,
                'masked_email': mask_email(email),
                'error': err,
            })

        latest_otp = EmailVerificationOTP.objects.filter(user=user, is_used=False).first()

        if not latest_otp or latest_otp.is_expired:
            err = "Your verification code has expired. Please click 'Resend Code' to receive a new one."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': {'otp_code': [err]}}, status=400)
            messages.error(request, err)
            return render(request, 'accounts/verify_otp.html', {
                'email': email,
                'masked_email': mask_email(email),
                'error': err,
            })

        if latest_otp.otp_code != otp_code:
            latest_otp.attempts += 1
            if latest_otp.attempts >= 5:
                latest_otp.is_used = True
                latest_otp.save(update_fields=['attempts', 'is_used'])
                err = "Too many invalid attempts. This code has been invalidated. Please request a new code."
            else:
                latest_otp.save(update_fields=['attempts'])
                remaining_attempts = 5 - latest_otp.attempts
                err = f"Invalid verification code. {remaining_attempts} attempt{'s' if remaining_attempts != 1 else ''} remaining."

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': {'otp_code': [err]}}, status=400)
            messages.error(request, err)
            return render(request, 'accounts/verify_otp.html', {
                'email': email,
                'masked_email': mask_email(email),
                'error': err,
            })

        # OTP is valid!
        latest_otp.is_used = True
        latest_otp.save(update_fields=['is_used'])

        user.is_email_verified = True
        user.save(update_fields=['is_email_verified'])

        # Clean session
        request.session.pop('verify_email', None)

        # Log user in directly
        login(request, user)
        messages.success(request, "Email verified successfully! Welcome to DevBlog.")

        redirect_url = str(reverse_lazy('dashboard:index')) if user.is_staff else str(reverse_lazy('core:home'))
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'redirect_url': redirect_url})
        return redirect(redirect_url)

    return render(request, 'accounts/verify_otp.html', {
        'email': email,
        'masked_email': mask_email(email),
    })


def resend_otp_view(request):
    """View to handle resending OTP codes with 60-second cooldown."""
    if request.method != 'POST':
        return redirect('accounts:verify_otp')

    email = request.session.get('verify_email') or request.POST.get('email', '').strip()
    user = User.objects.filter(email__iexact=email).first() if email else None

    if not user:
        msg = "Unable to locate account. Please register again."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': msg}, status=400)
        messages.error(request, msg)
        return redirect('accounts:register')

    if user.is_email_verified:
        msg = "Your email is already verified. Please sign in."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': msg, 'redirect_url': str(reverse_lazy('accounts:login'))})
        messages.info(request, msg)
        return redirect('accounts:login')

    # Rate limiting: 60-second cooldown check
    latest_otp = EmailVerificationOTP.objects.filter(user=user).order_by('-created_at').first()
    if latest_otp:
        time_elapsed = (timezone.now() - latest_otp.created_at).total_seconds()
        if time_elapsed < 60:
            remaining = int(60 - time_elapsed)
            msg = f"Please wait {remaining} seconds before requesting a new code."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': msg, 'remaining_seconds': remaining}, status=429)
            messages.warning(request, msg)
            return redirect('accounts:verify_otp')

    EmailVerificationOTP.generate_otp_for_user(user)
    msg = f"A fresh 6-digit verification code has been sent to {user.email}."
    messages.success(request, msg)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': msg, 'cooldown': 60})
    return redirect('accounts:verify_otp')


def logout_view(request):
    if request.method in ('POST', 'GET'):
        logout(request)
        messages.info(request, "You have been logged out.")
    return redirect('core:home')


class PasswordResetView(auth_views.PasswordResetView):
    form_class = PasswordResetForm
    template_name = 'accounts/password/password_reset.html'
    email_template_name = 'accounts/password/password_reset_email.html'
    subject_template_name = 'accounts/password/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'redirect_url': str(self.success_url)})
        return response

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = [str(e) for e in field_errors]
            return JsonResponse({'success': False, 'errors': errors}, status=400)
        return super().form_invalid(form)


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    form_class = SetPasswordForm
    template_name = 'accounts/password/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'redirect_url': str(self.success_url)})
        return response

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = [str(e) for e in field_errors]
            return JsonResponse({'success': False, 'errors': errors}, status=400)
        return super().form_invalid(form)


class PasswordChangeView(auth_views.PasswordChangeView):
    form_class = PasswordChangeForm
    template_name = 'accounts/password/password_change.html'

    def get_success_url(self):
        return str(reverse('accounts:author_profile', kwargs={'pk': self.request.user.pk}))

    def form_valid(self, form):
        messages.success(self.request, "Your password has been changed successfully.")
        response = super().form_valid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': "Your password has been changed successfully.", 'redirect_url': self.get_success_url()})
        return response

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = [str(e) for e in field_errors]
            return JsonResponse({'success': False, 'errors': errors}, status=400)
        return super().form_invalid(form)




class AuthorProfileView(DetailView):
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'author_user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        author = self.get_object()
        context['articles'] = (
            author.posts.filter(status='PUBLISHED')
            .select_related('category', 'author', 'author__profile')
            .prefetch_related('tags')
            .with_counts()
        )
        context['articles_count'] = context['articles'].count()

        # Liked posts by this user
        from apps.blog.models import Post
        context['liked_posts'] = (
            Post.objects.filter(
                likes__user=author,
                status='PUBLISHED'
            )
            .select_related('category', 'author', 'author__profile')
            .prefetch_related('tags')
            .with_counts()
            .order_by('-likes__created_at')
        )
        context['liked_posts_count'] = context['liked_posts'].count()


        is_owner = self.request.user.is_authenticated and self.request.user.pk == author.pk
        context['is_owner'] = is_owner

        if is_owner:
            context['read_later_posts'] = (
                Post.objects.filter(
                    read_later_entries__user=author,
                    status='PUBLISHED'
                )
                .select_related('category', 'author', 'author__profile')
                .prefetch_related('tags')
                .with_counts()
                .order_by('-read_later_entries__created_at')
            )
            context['read_later_posts_count'] = context['read_later_posts'].count()

        return context



@login_required
def update_profile_view(request):
    """Handles in-place profile updates (Name, Avatar, Bio, Social links). Email is strictly non-editable here."""
    if request.method != 'POST':
        return redirect('accounts:author_profile', pk=request.user.pk)

    user = request.user
    profile = getattr(user, 'profile', None)
    if not profile:
        profile = Profile.objects.create(user=user)

    user_form = UserUpdateForm(request.POST, instance=user)
    profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if user_form.is_valid() and profile_form.is_valid():
        user_form.save()
        profile_form.save()

        avatar_url = profile.avatar.url if profile.avatar else None
        msg = "Your profile details and picture have been updated successfully."
        redirect_url = str(reverse('accounts:author_profile', kwargs={'pk': user.pk}))
        if is_ajax:
            return JsonResponse({
                'success': True,
                'message': msg,
                'full_name': user.full_name,
                'avatar_url': avatar_url,
                'redirect_url': redirect_url,
            })
        messages.success(request, msg)
        return redirect('accounts:author_profile', pk=user.pk)

    errors = {}
    for f, errs in user_form.errors.items():
        errors[f] = [str(e) for e in errs]
    for f, errs in profile_form.errors.items():
        errors[f] = [str(e) for e in errs]

    if is_ajax:
        return JsonResponse({'success': False, 'errors': errors}, status=400)

    for field, errs in errors.items():
        for err in errs:
            messages.error(request, f"{field.replace('_', ' ').title()}: {err}")
    return redirect('accounts:author_profile', pk=user.pk)


@login_required
def change_password_ajax_view(request):
    """Handles password change directly on the profile page without forcing a logout."""
    if request.method != 'POST':
        return redirect('accounts:author_profile', pk=request.user.pk)

    form = PasswordChangeForm(user=request.user, data=request.POST)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        msg = "Your password has been changed successfully."
        redirect_url = str(reverse('accounts:author_profile', kwargs={'pk': request.user.pk}))
        messages.success(request, msg)
        if is_ajax:
            return JsonResponse({'success': True, 'message': msg, 'redirect_url': redirect_url})
        return redirect('accounts:author_profile', pk=request.user.pk)

    errors = {}
    for f, errs in form.errors.items():
        errors[f] = [str(e) for e in errs]

    if is_ajax:
        return JsonResponse({'success': False, 'errors': errors}, status=400)

    for field, errs in errors.items():
        for err in errs:
            messages.error(request, f"{err}")
    return redirect('accounts:author_profile', pk=request.user.pk)


@login_required
def request_email_change_view(request):
    """Validates current password & new email, then generates and sends a 6-digit OTP to the new email."""
    if request.user.is_google_account:
        msg = "Email addresses for Google-authenticated accounts cannot be changed."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': msg}, status=403)
        messages.error(request, msg)
        return redirect('accounts:author_profile', pk=request.user.pk)

    if request.method != 'POST':
        return redirect('accounts:author_profile', pk=request.user.pk)

    form = EmailChangeRequestForm(request.user, request.POST)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if form.is_valid():
        new_email = form.cleaned_data['new_email']

        # 60s cooldown check to prevent abuse/spamming
        recent_otp = EmailVerificationOTP.objects.filter(
            user=request.user,
            is_used=False
        ).exclude(new_email__isnull=True).exclude(new_email='').order_by('-created_at').first()
        if recent_otp and (timezone.now() - recent_otp.created_at).total_seconds() < 60:
            remaining = int(60 - (timezone.now() - recent_otp.created_at).total_seconds())
            err = f"Please wait {remaining} seconds before requesting another code."
            if is_ajax:
                return JsonResponse({'success': False, 'message': err, 'cooldown': remaining}, status=429)
            messages.warning(request, err)
            return redirect('accounts:author_profile', pk=request.user.pk)

        otp = EmailVerificationOTP.generate_otp_for_user(user=request.user, new_email=new_email)
        send_email_change_otp(user=request.user, new_email=new_email, otp_code=otp.otp_code)
        request.session['pending_new_email'] = new_email

        msg = f"A 6-digit verification code has been sent to {new_email}."
        if is_ajax:
            return JsonResponse({
                'success': True,
                'message': msg,
                'new_email': new_email,
                'masked_email': mask_email(new_email),
            })
        messages.info(request, msg)
        return redirect('accounts:author_profile', pk=request.user.pk)

    errors = {}
    for f, errs in form.errors.items():
        errors[f] = [str(e) for e in errs]

    if is_ajax:
        return JsonResponse({'success': False, 'errors': errors}, status=400)

    for field, errs in errors.items():
        for err in errs:
            messages.error(request, f"{err}")
    return redirect('accounts:author_profile', pk=request.user.pk)


@login_required
def verify_email_change_view(request):
    """Verifies the 6-digit OTP sent to new email. Only upon success is the user email updated."""
    if request.user.is_google_account:
        return JsonResponse({'success': False, 'message': "Google accounts cannot modify their email."}, status=403)

    if request.method != 'POST':
        return redirect('accounts:author_profile', pk=request.user.pk)

    form = EmailChangeVerifyForm(request.POST)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if form.is_valid():
        otp_code = form.cleaned_data['otp_code']
        otp = EmailVerificationOTP.objects.filter(
            user=request.user,
            is_used=False
        ).exclude(new_email__isnull=True).exclude(new_email='').first()

        if not otp or otp.is_expired:
            err = "Your email verification code has expired. Please request a new code."
            if is_ajax:
                return JsonResponse({'success': False, 'errors': {'otp_code': [err]}}, status=400)
            messages.error(request, err)
            return redirect('accounts:author_profile', pk=request.user.pk)

        if otp.otp_code != otp_code:
            otp.attempts += 1
            if otp.attempts >= 5:
                otp.is_used = True
                otp.save(update_fields=['attempts', 'is_used'])
                err = "Too many invalid attempts. This code has been invalidated. Please request a new code."
            else:
                otp.save(update_fields=['attempts'])
                remaining = 5 - otp.attempts
                err = f"Invalid verification code. {remaining} attempt{'s' if remaining != 1 else ''} remaining."
            if is_ajax:
                return JsonResponse({'success': False, 'errors': {'otp_code': [err]}}, status=400)
            messages.error(request, err)
            return redirect('accounts:author_profile', pk=request.user.pk)

        new_email = otp.new_email
        if User.objects.filter(email__iexact=new_email).exclude(pk=request.user.pk).exists():
            err = "This email address is already registered to another account."
            if is_ajax:
                return JsonResponse({'success': False, 'errors': {'otp_code': [err]}}, status=400)
            messages.error(request, err)
            return redirect('accounts:author_profile', pk=request.user.pk)

        # Successfully verified! Apply the email change to the user
        user = request.user
        user.email = new_email
        user.is_email_verified = True
        user.save(update_fields=['email', 'is_email_verified'])

        # Mark OTP used
        otp.is_used = True
        otp.save(update_fields=['is_used'])
        request.session.pop('pending_new_email', None)

        msg = f"Your email address has been successfully updated to {new_email}!"
        messages.success(request, msg)
        redirect_url = str(reverse('accounts:author_profile', kwargs={'pk': user.pk}))
        if is_ajax:
            return JsonResponse({
                'success': True,
                'message': msg,
                'new_email': new_email,
                'redirect_url': redirect_url,
            })
        return redirect('accounts:author_profile', pk=request.user.pk)

    errors = {}
    for f, errs in form.errors.items():
        errors[f] = [str(e) for e in errs]

    if is_ajax:
        return JsonResponse({'success': False, 'errors': errors}, status=400)

    for field, errs in errors.items():
        for err in errs:
            messages.error(request, f"{err}")
    return redirect('accounts:author_profile', pk=request.user.pk)


@login_required
def resend_email_change_otp_view(request):
    """Resends a fresh 6-digit OTP code to the requested new email address."""
    if request.user.is_google_account:
        return JsonResponse({'success': False, 'message': "Google accounts cannot modify their email."}, status=403)

    if request.method != 'POST':
        return redirect('accounts:author_profile', pk=request.user.pk)

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    pending_otp = EmailVerificationOTP.objects.filter(
        user=request.user,
        is_used=False
    ).exclude(new_email__isnull=True).exclude(new_email='').first()

    new_email = request.POST.get('new_email') or request.session.get('pending_new_email')
    if not new_email and pending_otp:
        new_email = pending_otp.new_email

    if not new_email:
        err = "No pending email change request was found."
        if is_ajax:
            return JsonResponse({'success': False, 'message': err}, status=400)
        messages.error(request, err)
        return redirect('accounts:author_profile', pk=request.user.pk)

    # Cooldown check: 60 seconds
    if pending_otp and (timezone.now() - pending_otp.created_at).total_seconds() < 60:
        remaining = int(60 - (timezone.now() - pending_otp.created_at).total_seconds())
        err = f"Please wait {remaining} seconds before requesting another code."
        if is_ajax:
            return JsonResponse({'success': False, 'message': err, 'cooldown': remaining}, status=429)
        messages.warning(request, err)
        return redirect('accounts:author_profile', pk=request.user.pk)

    otp = EmailVerificationOTP.generate_otp_for_user(user=request.user, new_email=new_email)
    send_email_change_otp(user=request.user, new_email=new_email, otp_code=otp.otp_code)
    request.session['pending_new_email'] = new_email

    msg = f"A new 6-digit verification code has been sent to {new_email}."
    if is_ajax:
        return JsonResponse({'success': True, 'message': msg})
    messages.success(request, msg)
    return redirect('accounts:author_profile', pk=request.user.pk)


@login_required
def edit_profile_view(request):
    """Dedicated page to edit profile details (Name, Avatar, Bio, Social links). Email is locked."""
    user = request.user
    profile = getattr(user, 'profile', None)
    if not profile:
        profile = Profile.objects.create(user=user)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            avatar_url = profile.avatar.url if profile.avatar else None
            msg = "Your profile details have been successfully updated."
            messages.success(request, msg)
            redirect_url = str(reverse('accounts:author_profile', kwargs={'pk': user.pk}))
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': msg,
                    'full_name': user.full_name,
                    'avatar_url': avatar_url,
                    'redirect_url': redirect_url,
                })
            return redirect('accounts:author_profile', pk=user.pk)

        errors = {}
        for f, errs in user_form.errors.items():
            errors[f] = [str(e) for e in errs]
        for f, errs in profile_form.errors.items():
            errors[f] = [str(e) for e in errs]

        if is_ajax:
            return JsonResponse({'success': False, 'errors': errors}, status=400)

        for field, errs in errors.items():
            for err in errs:
                messages.error(request, f"{field.replace('_', ' ').title()}: {err}")
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = ProfileUpdateForm(instance=profile)

    return render(request, 'accounts/edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
    })


@login_required
def email_change_view(request):
    """Dedicated page for requesting and confirming an email change via OTP."""
    user = request.user
    if user.is_google_account:
        messages.warning(request, "Your email address is managed by your Google account and cannot be modified.")
        return redirect('accounts:author_profile', pk=user.pk)

    pending_otp = EmailVerificationOTP.objects.filter(
        user=user,
        is_used=False
    ).exclude(new_email__isnull=True).exclude(new_email='').first()

    pending_email = pending_otp.new_email if pending_otp and not pending_otp.is_expired else None

    request_form = EmailChangeRequestForm(user=user)
    verify_form = EmailChangeVerifyForm()

    return render(request, 'accounts/email_change.html', {
        'request_form': request_form,
        'verify_form': verify_form,
        'pending_email': pending_email,
        'pending_email_masked': mask_email(pending_email) if pending_email else '',
    })


@login_required
def current_profile_view(request):
    return redirect('accounts:author_profile', pk=request.user.pk)


logger = logging.getLogger(__name__)


def google_login_view(request):
    """
    Initiates Google OAuth 2.0 flow.
    Redirects the user to Google's authentication consent / account selection screen.
    """
    if request.user.is_authenticated:
        return redirect('core:home')

    # Security: Generate CSRF state token
    state = secrets.token_urlsafe(32)
    request.session['google_oauth_state'] = state

    # Capture optional next redirect parameter
    next_url = request.GET.get('next', '')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        request.session['google_oauth_next'] = next_url
    else:
        request.session.pop('google_oauth_next', None)

    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')
    redirect_uri = getattr(settings, 'GOOGLE_REDIRECT_URI', '') or request.build_absolute_uri(reverse('accounts:google_callback'))

    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'access_type': 'online',
        'prompt': 'select_account',
    }

    auth_url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(params)}"
    return redirect(auth_url)


def google_callback_view(request):
    """
    Handles Google OAuth 2.0 callback.
    Verifies CSRF state, exchanges authorization code for tokens, retrieves profile,
    and logs in or registers the user.
    """
    if request.user.is_authenticated:
        return redirect('core:home')

    # Handle user cancellation or denial
    error = request.GET.get('error')
    if error:
        logger.info(f"Google OAuth cancelled or returned error: {error}")
        messages.warning(request, "Google sign-in was cancelled.")
        return redirect('accounts:login')

    # Validate CSRF state parameter
    state = request.GET.get('state')
    saved_state = request.session.pop('google_oauth_state', None)
    if not state or not saved_state or not secrets.compare_digest(state, saved_state):
        logger.warning("Google OAuth state mismatch or missing token.")
        messages.error(request, "Security check failed: Invalid authentication state. Please try signing in again.")
        return redirect('accounts:login')

    code = request.GET.get('code')
    if not code:
        logger.warning("Google OAuth code parameter missing.")
        messages.error(request, "Authorization code not received from Google.")
        return redirect('accounts:login')

    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')
    client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', '')
    redirect_uri = getattr(settings, 'GOOGLE_REDIRECT_URI', '') or request.build_absolute_uri(reverse('accounts:google_callback'))

    token_url = "https://oauth2.googleapis.com/token"
    token_payload = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    }

    try:
        token_response = requests.post(token_url, data=token_payload, timeout=10)
        if token_response.status_code != 200:
            logger.error(f"Google token exchange failed ({token_response.status_code}): {token_response.text}")
            messages.error(request, "Failed to authenticate with Google. Please check your credentials and try again.")
            return redirect('accounts:login')
        token_data = token_response.json()
        access_token = token_data.get('access_token')
    except Exception as exc:
        logger.error(f"Error during Google token request: {exc}")
        messages.error(request, "Unable to communicate with Google authentication servers. Please try again later.")
        return redirect('accounts:login')

    if not access_token:
        messages.error(request, "Did not receive access token from Google.")
        return redirect('accounts:login')

    # Fetch Google user profile
    try:
        userinfo_response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10,
        )
        if userinfo_response.status_code != 200:
            logger.error(f"Google userinfo request failed ({userinfo_response.status_code}): {userinfo_response.text}")
            messages.error(request, "Could not fetch user profile details from Google.")
            return redirect('accounts:login')
        user_info = userinfo_response.json()
    except Exception as exc:
        logger.error(f"Error requesting Google userinfo: {exc}")
        messages.error(request, "Unable to load profile data from Google.")
        return redirect('accounts:login')

    email = user_info.get('email')
    if not email:
        messages.error(request, "Your Google account did not share an email address with DevBlog.")
        return redirect('accounts:login')

    first_name = user_info.get('given_name', '').strip()
    last_name = user_info.get('family_name', '').strip()
    picture_url = user_info.get('picture', '')

    user = User.objects.filter(email__iexact=email).first()
    is_new_user = False

    if not user:
        user = User.objects.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_email_verified=True,
            is_google_user=True,
        )
        user.set_unusable_password()
        user.save()
        is_new_user = True
    else:
        update_fields = []
        if not user.is_google_user:
            user.is_google_user = True
            update_fields.append('is_google_user')
        if not user.is_email_verified:
            user.is_email_verified = True
            update_fields.append('is_email_verified')
        if not user.first_name and first_name:
            user.first_name = first_name
            update_fields.append('first_name')
        if not user.last_name and last_name:
            user.last_name = last_name
            update_fields.append('last_name')
        if update_fields:
            user.save(update_fields=update_fields)

    # If user profile has no avatar and Google provided picture, attempt to store picture URL or save
    if hasattr(user, 'profile') and not user.profile.avatar and picture_url:
        try:
            from django.core.files.base import ContentFile
            img_resp = requests.get(picture_url, timeout=5)
            if img_resp.status_code == 200:
                user.profile.avatar.save(f"google_avatar_{user.id}.jpg", ContentFile(img_resp.content), save=True)
        except Exception as e:
            logger.debug(f"Could not download Google avatar: {e}")

    # Log the user into Django session
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')

    # Resolve post-login destination
    next_url = request.session.pop('google_oauth_next', '')
    if not next_url or not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = str(reverse_lazy('dashboard:index')) if user.is_staff else str(reverse_lazy('core:home'))

    if is_new_user:
        messages.success(request, f"Welcome to DevBlog, {user.first_name or user.email}! Your account is now active.")
    else:
        messages.success(request, f"Welcome back, {user.first_name or user.email}!")

    return redirect(next_url)



