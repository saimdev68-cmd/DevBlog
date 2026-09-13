from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from .models import Profile

User = get_user_model()


class UserModelAndProfileTests(TestCase):
    def test_create_user_with_email(self):
        user = User.objects.create_user(email='author@example.com', password='secretpassword123', first_name='John', last_name='Doe')
        self.assertEqual(user.email, 'author@example.com')
        self.assertEqual(user.full_name, 'John Doe')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        # Verify post_save profile creation signal
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsInstance(user.profile, Profile)

    def test_create_superuser(self):
        admin = User.objects.create_superuser(email='admin@example.com', password='adminpassword123')
        self.assertEqual(admin.email, 'admin@example.com')
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_registration_view(self):
        from django.core import mail
        mail.outbox = []

        response = self.client.post(reverse('accounts:register'), {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane@example.com',
            'password1': 'StrongPass123!@#',
            'password2': 'StrongPass123!@#',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:verify_otp'))

        # User is created but NOT verified
        user = User.objects.get(email='jane@example.com')
        self.assertFalse(user.is_email_verified)

        # User is NOT logged in automatically
        self.assertNotIn('_auth_user_id', self.client.session)

        # OTP is generated and email sent
        self.assertTrue(user.email_otps.filter(is_used=False).exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Your Verification Code', mail.outbox[0].subject)

    def test_registration_ajax_validation_error_and_success(self):
        # Mismatched passwords via AJAX -> 400 Bad Request with JSON errors (no page reload)
        ajax_err_resp = self.client.post(
            reverse('accounts:register'),
            {
                'first_name': 'Jane',
                'last_name': 'Smith',
                'email': 'jane2@example.com',
                'password1': 'StrongPass123!@#',
                'password2': 'DifferentPass999!@#',
            },
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertEqual(ajax_err_resp.status_code, 400)
        data = ajax_err_resp.json()
        self.assertFalse(data['success'])
        self.assertIn('password2', data['errors'])

        # Valid submission via AJAX -> 200 OK with redirect_url to verify_otp
        ajax_ok_resp = self.client.post(
            reverse('accounts:register'),
            {
                'first_name': 'Jane',
                'last_name': 'Smith',
                'email': 'jane2@example.com',
                'password1': 'StrongPass123!@#',
                'password2': 'StrongPass123!@#',
            },
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertEqual(ajax_ok_resp.status_code, 200)
        ok_data = ajax_ok_resp.json()
        self.assertTrue(ok_data['success'])
        self.assertIn(str(reverse('accounts:verify_otp')), ok_data['redirect_url'])
        self.assertTrue(User.objects.filter(email='jane2@example.com').exists())

    def test_login_and_logout_view(self):
        # Create verified user
        user = User.objects.create_user(email='test@example.com', password='ValidPass123!', is_email_verified=True)
        login_response = self.client.post(reverse('accounts:login'), {
            'username': 'test@example.com',
            'password': 'ValidPass123!',
        })
        self.assertEqual(login_response.status_code, 302)
        self.client.logout()

        # AJAX login error (wrong password) -> 400 Bad Request with JSON errors
        ajax_login_fail = self.client.post(
            reverse('accounts:login'),
            {'username': 'test@example.com', 'password': 'WrongPassword!'},
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertEqual(ajax_login_fail.status_code, 400)
        fail_data = ajax_login_fail.json()
        self.assertFalse(fail_data['success'])

        # AJAX login success -> 200 OK with redirect_url
        ajax_login_ok = self.client.post(
            reverse('accounts:login'),
            {'username': 'test@example.com', 'password': 'ValidPass123!'},
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertEqual(ajax_login_ok.status_code, 200)
        self.assertTrue(ajax_login_ok.json()['success'])

        logout_response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(logout_response.status_code, 302)

    def test_unverified_user_cannot_login(self):
        # User not verified
        user = User.objects.create_user(email='unverified@example.com', password='ValidPass123!', is_email_verified=False)

        # Attempt standard POST login
        resp = self.client.post(reverse('accounts:login'), {
            'username': 'unverified@example.com',
            'password': 'ValidPass123!',
        })
        # Should redirect to OTP verification, not authenticate
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse('accounts:verify_otp'))
        self.assertNotIn('_auth_user_id', self.client.session)

        # Attempt AJAX login
        ajax_resp = self.client.post(
            reverse('accounts:login'),
            {'username': 'unverified@example.com', 'password': 'ValidPass123!'},
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertEqual(ajax_resp.status_code, 400)
        data = ajax_resp.json()
        self.assertTrue(data['unverified'])
        self.assertIn(str(reverse('accounts:verify_otp')), data['redirect_url'])

    def test_otp_verification_success_and_login(self):
        from .models import EmailVerificationOTP
        user = User.objects.create_user(email='verify_me@example.com', password='ValidPass123!', is_email_verified=False)
        otp = EmailVerificationOTP.generate_otp_for_user(user, send_email=False)

        # Set session verify_email
        session = self.client.session
        session['verify_email'] = user.email
        session.save()

        # Submit correct OTP
        resp = self.client.post(reverse('accounts:verify_otp'), {
            'email': user.email,
            'otp_code': otp.otp_code,
        })
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse('core:home'))

        # Check user is now verified and logged in
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_otp_verification_invalid_and_expired(self):
        from datetime import timedelta
        from django.utils import timezone
        from .models import EmailVerificationOTP

        user = User.objects.create_user(email='fail_otp@example.com', password='ValidPass123!', is_email_verified=False)
        otp = EmailVerificationOTP.generate_otp_for_user(user, send_email=False)

        # Wrong OTP
        resp = self.client.post(reverse('accounts:verify_otp'), {
            'email': user.email,
            'otp_code': '000000',
        }, headers={'x-requested-with': 'XMLHttpRequest'})
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.json()['success'])
        user.refresh_from_db()
        self.assertFalse(user.is_email_verified)

        # Expired OTP
        otp.expires_at = timezone.now() - timedelta(minutes=1)
        otp.save()
        resp_exp = self.client.post(reverse('accounts:verify_otp'), {
            'email': user.email,
            'otp_code': otp.otp_code,
        }, headers={'x-requested-with': 'XMLHttpRequest'})
        self.assertEqual(resp_exp.status_code, 400)
        self.assertIn('expired', resp_exp.json()['errors']['otp_code'][0])

    def test_resend_otp_and_cooldown(self):
        from django.core import mail
        from .models import EmailVerificationOTP

        user = User.objects.create_user(email='resend@example.com', password='ValidPass123!', is_email_verified=False)
        EmailVerificationOTP.generate_otp_for_user(user, send_email=False)

        # First resend immediately -> Cooldown triggered (429 Too Many Requests)
        resp1 = self.client.post(reverse('accounts:resend_otp'), {
            'email': user.email,
        }, headers={'x-requested-with': 'XMLHttpRequest'})
        self.assertEqual(resp1.status_code, 429)

        # Fast-forward time
        from datetime import timedelta
        from django.utils import timezone
        latest_otp = EmailVerificationOTP.objects.filter(user=user).first()
        latest_otp.created_at = timezone.now() - timedelta(seconds=65)
        latest_otp.save()

        # Resend after cooldown -> 200 OK and email sent
        mail.outbox = []
        resp2 = self.client.post(reverse('accounts:resend_otp'), {
            'email': user.email,
        }, headers={'x-requested-with': 'XMLHttpRequest'})
        self.assertEqual(resp2.status_code, 200)
        self.assertTrue(resp2.json()['success'])
        self.assertEqual(len(mail.outbox), 1)

    def test_author_profile_public_view(self):

        author = User.objects.create_user(email='writer@example.com', password='Pass123!', first_name='Writer')
        response = self.client.get(reverse('accounts:author_profile', kwargs={'pk': author.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Writer')

    def test_create_admin_command_missing_env(self):
        from io import StringIO
        from django.core.management import call_command
        import os

        # Ensure env vars are not set
        old_email = os.environ.pop('DJANGO_SUPERUSER_EMAIL', None)
        old_pass = os.environ.pop('DJANGO_SUPERUSER_PASSWORD', None)

        try:
            err = StringIO()
            call_command('create_admin', stderr=err)
            self.assertIn('DJANGO_SUPERUSER_EMAIL and DJANGO_SUPERUSER_PASSWORD environment variables are required', err.getvalue())
        finally:
            if old_email: os.environ['DJANGO_SUPERUSER_EMAIL'] = old_email
            if old_pass: os.environ['DJANGO_SUPERUSER_PASSWORD'] = old_pass

    def test_create_admin_command_success_and_idempotent(self):
        from io import StringIO
        from django.core.management import call_command
        import os

        test_email = 'renderadmin@example.com'
        test_pass = 'SuperSecurePass2026!'

        os.environ['DJANGO_SUPERUSER_EMAIL'] = test_email
        os.environ['DJANGO_SUPERUSER_PASSWORD'] = test_pass
        os.environ['DJANGO_SUPERUSER_FIRST_NAME'] = 'Platform'
        os.environ['DJANGO_SUPERUSER_LAST_NAME'] = 'Admin'

        try:
            out1 = StringIO()
            call_command('create_admin', stdout=out1)
            self.assertIn(f'Superuser created successfully: {test_email}', out1.getvalue())

            # Verify user properties
            admin_user = User.objects.get(email=test_email)
            self.assertTrue(admin_user.is_staff)
            self.assertTrue(admin_user.is_superuser)
            self.assertTrue(admin_user.is_active)
            self.assertEqual(admin_user.first_name, 'Platform')
            self.assertTrue(admin_user.check_password(test_pass))

            # Run again (Idempotency test)
            out2 = StringIO()
            call_command('create_admin', stdout=out2)
            self.assertIn(f'Admin user already exists: {test_email}', out2.getvalue())

            # Verify no duplicates
            self.assertEqual(User.objects.filter(email=test_email).count(), 1)
        finally:
            os.environ.pop('DJANGO_SUPERUSER_EMAIL', None)
            os.environ.pop('DJANGO_SUPERUSER_PASSWORD', None)
            os.environ.pop('DJANGO_SUPERUSER_FIRST_NAME', None)
            os.environ.pop('DJANGO_SUPERUSER_LAST_NAME', None)

    def test_current_profile_redirect(self):
        # Anonymous redirects to login
        anon_resp = self.client.get(reverse('accounts:current_profile'))
        self.assertEqual(anon_resp.status_code, 302)
        self.assertIn('/accounts/login/', anon_resp.url)

        # Authenticated redirects to author_profile
        user = User.objects.create_user(email='reader_prof@example.com', password='ValidPass123!')
        self.client.login(email='reader_prof@example.com', password='ValidPass123!')
        resp = self.client.get(reverse('accounts:current_profile'))
        self.assertRedirects(resp, reverse('accounts:author_profile', kwargs={'pk': user.pk}))

    def test_password_change_view(self):
        user = User.objects.create_user(email='pwduser@example.com', password='OldPassword123!')
        self.client.login(email='pwduser@example.com', password='OldPassword123!')

        get_resp = self.client.get(reverse('accounts:password_change'))
        self.assertEqual(get_resp.status_code, 200)
        self.assertContains(get_resp, 'Change Password')

        post_resp = self.client.post(reverse('accounts:password_change'), {
            'old_password': 'OldPassword123!',
            'new_password1': 'BrandNewPassword456!@#',
            'new_password2': 'BrandNewPassword456!@#',
        })
        self.assertEqual(post_resp.status_code, 302)
        user.refresh_from_db()
        self.assertTrue(user.check_password('BrandNewPassword456!@#'))

    def test_avatar_size_limit_validation(self):
        from io import BytesIO
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        from .forms import ProfileUpdateForm

        # Generate valid JPEG image
        img = Image.new('RGB', (50, 50), color='blue')
        buf = BytesIO()
        img.save(buf, format='JPEG')
        valid_jpeg_bytes = buf.getvalue()

        # Simulate 4MB file exceeding 3MB limit
        oversized = SimpleUploadedFile("big_avatar.jpg", valid_jpeg_bytes, content_type="image/jpeg")
        oversized.size = 4 * 1024 * 1024

        form = ProfileUpdateForm(data={}, files={'avatar': oversized})
        self.assertFalse(form.is_valid())
        self.assertIn('avatar', form.errors)
        self.assertIn('cannot exceed 3MB', str(form.errors['avatar']))

    def test_password_reset_view_ajax(self):
        from django.core import mail
        mail.outbox = []

        # GET password reset page
        get_resp = self.client.get(reverse('accounts:password_reset'))
        self.assertEqual(get_resp.status_code, 200)
        self.assertContains(get_resp, 'Reset Password')
        self.assertContains(get_resp, 'DevBlog Logo')

        # AJAX invalid form submission (empty email) -> 400 Bad Request
        fail_resp = self.client.post(
            reverse('accounts:password_reset'),
            {'email': ''},
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertEqual(fail_resp.status_code, 400)
        self.assertFalse(fail_resp.json()['success'])
        self.assertIn('email', fail_resp.json()['errors'])

        # AJAX valid form submission -> 200 OK with redirect_url
        user = User.objects.create_user(email='reset_target@example.com', password='Password123!', is_email_verified=True)
        ok_resp = self.client.post(
            reverse('accounts:password_reset'),
            {'email': user.email},
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertEqual(ok_resp.status_code, 200)
        self.assertTrue(ok_resp.json()['success'])
        self.assertIn(str(reverse('accounts:password_reset_done')), ok_resp.json()['redirect_url'])
        self.assertEqual(len(mail.outbox), 1)

    def test_owner_profile_view_and_public_visitor(self):
        owner = User.objects.create_user(email='author1@example.com', password='Password123!', first_name='Alice', last_name='Wonder')
        other = User.objects.create_user(email='visitor@example.com', password='Password123!', first_name='Bob', last_name='Builder')

        # Visitor viewing Alice's profile -> no owner action links
        self.client.login(email='visitor@example.com', password='Password123!')
        resp = self.client.get(reverse('accounts:author_profile', kwargs={'pk': owner.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context['is_owner'])
        self.assertNotContains(resp, 'Edit Profile Details')

        # Alice viewing her own profile -> owner action links present
        self.client.login(email='author1@example.com', password='Password123!')
        resp = self.client.get(reverse('accounts:author_profile', kwargs={'pk': owner.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context['is_owner'])
        self.assertContains(resp, 'Edit Profile Details')
        self.assertContains(resp, 'Change Password')
        self.assertContains(resp, 'Change Email')

    def test_dedicated_edit_profile_page(self):
        user = User.objects.create_user(email='editor@example.com', password='Password123!', first_name='OldFirst', last_name='OldLast')
        self.client.login(email='editor@example.com', password='Password123!')

        # GET dedicated edit page
        get_resp = self.client.get(reverse('accounts:edit_profile'))
        self.assertEqual(get_resp.status_code, 200)
        self.assertContains(get_resp, 'Edit Profile Details')
        self.assertContains(get_resp, 'Verified &bull; Read Only')
        self.assertContains(get_resp, 'Change Email via OTP')

        # POST profile update including attempted email tampering
        resp = self.client.post(
            reverse('accounts:edit_profile'),
            {
                'first_name': 'NewFirst',
                'last_name': 'NewLast',
                'bio': 'Updated biography.',
                'website': 'https://example.com',
                'email': 'hacked@example.com',  # Attempt to change email directly
            },
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertIn('redirect_url', data)
        self.assertIn(str(reverse('accounts:author_profile', kwargs={'pk': user.pk})), data['redirect_url'])

        user.refresh_from_db()
        self.assertEqual(user.first_name, 'NewFirst')
        self.assertEqual(user.last_name, 'NewLast')
        self.assertEqual(user.profile.bio, 'Updated biography.')
        # Email MUST remain untouched
        self.assertEqual(user.email, 'editor@example.com')

    def test_dedicated_email_change_page(self):
        user = User.objects.create_user(email='emailtarget@example.com', password='Password123!')
        self.client.login(email='emailtarget@example.com', password='Password123!')

        # GET dedicated email change page
        get_resp = self.client.get(reverse('accounts:email_change'))
        self.assertEqual(get_resp.status_code, 200)
        self.assertContains(get_resp, 'Change Email Address')
        self.assertContains(get_resp, 'Step 1: Request Email Update')
        self.assertContains(get_resp, 'Step 2: Enter Verification Code')
        self.assertContains(get_resp, 'emailtarget@example.com')

    def test_change_password_ajax_view(self):
        user = User.objects.create_user(email='pwtest@example.com', password='OldPassword123!')
        self.client.login(email='pwtest@example.com', password='OldPassword123!')

        # Incorrect old password
        bad_resp = self.client.post(
            reverse('accounts:change_password_ajax'),
            {
                'old_password': 'WrongPassword123!',
                'new_password1': 'NewValidPassword123!',
                'new_password2': 'NewValidPassword123!',
            },
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertEqual(bad_resp.status_code, 400)
        self.assertFalse(bad_resp.json()['success'])

        # Valid password change
        good_resp = self.client.post(
            reverse('accounts:change_password_ajax'),
            {
                'old_password': 'OldPassword123!',
                'new_password1': 'NewValidPassword123!',
                'new_password2': 'NewValidPassword123!',
            },
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertEqual(good_resp.status_code, 200)
        self.assertTrue(good_resp.json()['success'])

        user.refresh_from_db()
        self.assertTrue(user.check_password('NewValidPassword123!'))

    def test_email_change_full_otp_workflow(self):
        from django.core import mail
        from .models import EmailVerificationOTP
        mail.outbox = []

        user = User.objects.create_user(email='current@example.com', password='SecretPassword123!', is_email_verified=True)
        existing_other = User.objects.create_user(email='taken@example.com', password='SecretPassword123!')

        self.client.login(email='current@example.com', password='SecretPassword123!')

        # 1. Request with wrong password -> fails
        req_fail_pwd = self.client.post(
            reverse('accounts:request_email_change'),
            {'current_password': 'WrongPassword!', 'new_email': 'brandnew@example.com'},
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertEqual(req_fail_pwd.status_code, 400)
        self.assertIn('current_password', req_fail_pwd.json()['errors'])

        # 2. Request with existing taken email -> fails
        req_fail_taken = self.client.post(
            reverse('accounts:request_email_change'),
            {'current_password': 'SecretPassword123!', 'new_email': 'taken@example.com'},
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertEqual(req_fail_taken.status_code, 400)
        self.assertIn('new_email', req_fail_taken.json()['errors'])

        # 3. Request with valid new email -> succeeds & sends OTP
        req_ok = self.client.post(
            reverse('accounts:request_email_change'),
            {'current_password': 'SecretPassword123!', 'new_email': 'brandnew@example.com'},
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertEqual(req_ok.status_code, 200)
        self.assertTrue(req_ok.json()['success'])
        self.assertEqual(req_ok.json()['new_email'], 'brandnew@example.com')

        # Verify OTP was created in DB for brandnew@example.com
        otp_record = EmailVerificationOTP.objects.filter(user=user, is_used=False).first()
        self.assertIsNotNone(otp_record)
        self.assertEqual(otp_record.new_email, 'brandnew@example.com')
        otp_code = otp_record.otp_code

        # Verify email was sent to brandnew@example.com
        self.assertTrue(len(mail.outbox) > 0)
        self.assertIn('brandnew@example.com', mail.outbox[-1].to)
        self.assertIn(otp_code, mail.outbox[-1].body)

        # 4. Verify with wrong code -> fails
        verify_fail = self.client.post(
            reverse('accounts:verify_email_change'),
            {'otp_code': '999999'},
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertEqual(verify_fail.status_code, 400)
        user.refresh_from_db()
        self.assertEqual(user.email, 'current@example.com')  # Still not changed!

        # 5. Verify with correct OTP code -> email is successfully changed!
        verify_ok = self.client.post(
            reverse('accounts:verify_email_change'),
            {'otp_code': otp_code},
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertEqual(verify_ok.status_code, 200)
        self.assertTrue(verify_ok.json()['success'])

        user.refresh_from_db()
        self.assertEqual(user.email, 'brandnew@example.com')
        self.assertTrue(user.is_email_verified)

        otp_record.refresh_from_db()
        self.assertTrue(otp_record.is_used)





