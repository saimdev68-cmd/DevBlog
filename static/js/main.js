// DevBlog Client Scripts

document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile navigation menu toggle
    const menuToggle = document.getElementById('mobileMenuToggle');
    const navMenu = document.getElementById('navMenu');

    if (menuToggle && navMenu) {
        menuToggle.addEventListener('click', () => {
            navMenu.classList.toggle('is-open');
            const isExpanded = navMenu.classList.contains('is-open');
            menuToggle.setAttribute('aria-expanded', isExpanded);
        });
    }

    // 2. Floating Toast Notification System (10s auto-dismiss, cut option, single message at a time)
    let activeToastTimer = null;

    function hideToast(toastEl) {
        if (!toastEl) return;
        toastEl.classList.remove('is-visible');
        toastEl.classList.add('is-hiding');
        setTimeout(() => {
            if (toastEl && toastEl.parentNode) {
                toastEl.remove();
            }
        }, 300);
    }

    function showToast(message, type = 'info', duration = 10000) {
        let container = document.getElementById('messagesContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'messagesContainer';
            container.className = 'messages-container';
            container.setAttribute('aria-live', 'polite');
            document.body.appendChild(container);
        }

        // Clear existing timer and remove any existing toast (ensure only ONE message shows at a time!)
        if (activeToastTimer) {
            clearTimeout(activeToastTimer);
            activeToastTimer = null;
        }
        const existingToasts = container.querySelectorAll('.toast-notification, .alert');
        existingToasts.forEach(t => t.remove());

        // Create new toast element
        const toast = document.createElement('div');
        toast.className = `toast-notification toast-${type}`;
        toast.setAttribute('role', 'alert');

        let iconSvg = '';
        if (type === 'success') {
            iconSvg = '<svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>';
        } else if (type === 'error') {
            iconSvg = '<svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>';
        } else if (type === 'warning') {
            iconSvg = '<svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>';
        } else {
            iconSvg = '<svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/></svg>';
        }

        toast.innerHTML = `
            <span class="toast-icon">${iconSvg}</span>
            <div class="toast-content">${message}</div>
            <button type="button" class="toast-close" aria-label="Dismiss notification">&times;</button>
        `;

        container.appendChild(toast);

        // Entrance animation
        requestAnimationFrame(() => {
            toast.classList.add('is-visible');
        });

        // Cut button click
        const closeBtn = toast.querySelector('.toast-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                if (activeToastTimer) {
                    clearTimeout(activeToastTimer);
                    activeToastTimer = null;
                }
                hideToast(toast);
            });
        }

        // Auto disappear after duration (default 10s)
        activeToastTimer = setTimeout(() => {
            hideToast(toast);
            activeToastTimer = null;
        }, duration);
    }

    // Expose globally
    window.showToast = showToast;

    // Initialize any server-rendered toast notifications on initial page load
    const container = document.getElementById('messagesContainer');
    if (container) {
        const initialToasts = container.querySelectorAll('.toast-notification, .alert');
        if (initialToasts.length > 0) {
            // Keep ONLY the last one if multiple were rendered
            for (let i = 0; i < initialToasts.length - 1; i++) {
                initialToasts[i].remove();
            }
            const activeToast = initialToasts[initialToasts.length - 1];

            requestAnimationFrame(() => {
                activeToast.classList.add('is-visible');
            });

            const closeBtn = activeToast.querySelector('.toast-close, .alert-close');
            if (closeBtn) {
                closeBtn.addEventListener('click', () => {
                    if (activeToastTimer) {
                        clearTimeout(activeToastTimer);
                        activeToastTimer = null;
                    }
                    hideToast(activeToast);
                });
            }

            // Auto-disappear after 10 seconds
            activeToastTimer = setTimeout(() => {
                hideToast(activeToast);
                activeToastTimer = null;
            }, 10000);
        }
    }


    // 3. Copy Link Share functionality
    const copyLinkBtn = document.getElementById('copyLinkBtn');
    if (copyLinkBtn) {
        copyLinkBtn.addEventListener('click', async () => {
            const url = window.location.href;
            try {
                if (navigator.clipboard) {
                    await navigator.clipboard.writeText(url);
                } else {
                    const temp = document.createElement('input');
                    temp.value = url;
                    document.body.appendChild(temp);
                    temp.select();
                    document.execCommand('copy');
                    document.body.removeChild(temp);
                }
                const originalText = copyLinkBtn.innerHTML;
                copyLinkBtn.innerHTML = '✓ Copied!';
                setTimeout(() => {
                    copyLinkBtn.innerHTML = originalText;
                }, 2500);
            } catch (err) {
                console.error('Failed to copy URL', err);
            }
        });
    }

    // 4. Article Like Toggle (AJAX with micro-interaction)
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const likeButtons = document.querySelectorAll('.like-btn');
    likeButtons.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const likeUrl = btn.getAttribute('data-like-url');
            if (!likeUrl) return;

            const isAuth = btn.getAttribute('data-authenticated') === 'true';
            if (!isAuth) {
                const loginUrl = btn.getAttribute('data-login-url') || '/accounts/login/';
                window.location.href = `${loginUrl}?next=${encodeURIComponent(window.location.pathname)}`;
                return;
            }

            btn.disabled = true;
            btn.classList.add('is-loading');
            const csrfToken = getCookie('csrftoken') || document.querySelector('[name=csrfmiddlewaretoken]')?.value;

            try {
                const response = await fetch(likeUrl, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest',
                        'Content-Type': 'application/json'
                    }
                });

                if (response.status === 401 || response.status === 403) {
                    window.location.href = '/accounts/login/';
                    return;
                }

                if (response.ok) {
                    const data = await response.json();
                    const countEl = btn.querySelector('.like-count');
                    const textEl = btn.querySelector('.like-text');

                    if (data.liked) {
                        btn.classList.add('liked');
                        btn.setAttribute('aria-pressed', 'true');
                        if (textEl) textEl.textContent = 'Liked';
                    } else {
                        btn.classList.remove('liked');
                        btn.setAttribute('aria-pressed', 'false');
                        if (textEl) textEl.textContent = 'Like';
                    }

                    if (countEl) {
                        countEl.textContent = data.like_count;
                        countEl.style.transform = 'scale(1.25)';
                        setTimeout(() => {
                            countEl.style.transform = 'scale(1)';
                        }, 200);
                    }
                } else {
                    showToast('Unable to update like. Please try again.', 'warning');
                }
            } catch (err) {
                console.error('Error toggling like:', err);
                showToast('Network error while updating like.', 'error');
            } finally {
                btn.disabled = false;
                btn.classList.remove('is-loading');
            }
        });
    });

    // 4b. Read Later / Bookmark Toggle Handler
    document.addEventListener('click', async (e) => {
        const btn = e.target.closest('.bookmark-btn, .card-bookmark-btn');
        if (!btn) return;
        e.preventDefault();
        e.stopPropagation();

        const bookmarkUrl = btn.getAttribute('data-bookmark-url');
        if (!bookmarkUrl) return;

        const isAuth = btn.getAttribute('data-authenticated') === 'true';
        if (!isAuth) {
            const loginUrl = btn.getAttribute('data-login-url') || '/accounts/login/';
            window.location.href = `${loginUrl}?next=${encodeURIComponent(window.location.pathname)}`;
            return;
        }

        btn.disabled = true;
        btn.classList.add('is-loading');
        const csrfToken = getCookie('csrftoken') || document.querySelector('[name=csrfmiddlewaretoken]')?.value;

        try {
            const response = await fetch(bookmarkUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json'
                }
            });

            if (response.status === 401 || response.status === 403) {
                window.location.href = '/accounts/login/';
                return;
            }

            if (response.ok) {
                const data = await response.json();

                // Update all buttons for this same article on the page
                const allMatchingBtns = document.querySelectorAll(`[data-bookmark-url="${bookmarkUrl}"]`);
                allMatchingBtns.forEach(b => {
                    const textEl = b.querySelector('.bookmark-text');
                    if (data.saved) {
                        b.classList.add('bookmarked');
                        b.setAttribute('aria-pressed', 'true');
                        if (textEl) textEl.textContent = 'Saved for Later';
                        b.setAttribute('title', 'Remove from Reading List');
                    } else {
                        b.classList.remove('bookmarked');
                        b.setAttribute('aria-pressed', 'false');
                        if (textEl) textEl.textContent = 'Read Later';
                        b.setAttribute('title', 'Save for later');
                    }
                });

                // Update navbar reading list badge if present
                const navBadge = document.getElementById('navReadingListCount');
                if (navBadge) {
                    if (data.reading_list_count > 0) {
                        navBadge.textContent = data.reading_list_count;
                        navBadge.style.display = 'inline-flex';
                    } else {
                        navBadge.style.display = 'none';
                    }
                }

                // If on reading list page and removed, gracefully fade out card
                const readingListGrid = document.getElementById('readingListGrid');
                if (readingListGrid && !data.saved) {
                    const postCard = btn.closest('.post-card');
                    if (postCard) {
                        postCard.style.transition = 'opacity 0.25s ease, transform 0.25s ease';
                        postCard.style.opacity = '0';
                        postCard.style.transform = 'scale(0.95)';
                        setTimeout(() => {
                            postCard.remove();
                            const remaining = readingListGrid.querySelectorAll('.post-card').length;
                            const totalCountEl = document.getElementById('readingListTotalCount');
                            if (totalCountEl) {
                                totalCountEl.textContent = `${remaining} article${remaining === 1 ? '' : 's'} saved`;
                            }
                            if (remaining === 0) {
                                window.location.reload();
                            }
                        }, 250);
                    }
                }

                showToast(data.message || (data.saved ? 'Saved to Reading List' : 'Removed from Reading List'), 'success');
            } else {
                showToast('Unable to update reading list. Please try again.', 'warning');
            }
        } catch (err) {
            console.error('Error toggling reading list entry:', err);
            showToast('Network error while updating reading list.', 'error');
        } finally {
            btn.disabled = false;
            btn.classList.remove('is-loading');
        }
    });

    // 5. Password Visibility Toggle (Show / Hide password)

    document.querySelectorAll('.password-toggle-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const wrapper = this.closest('.password-input-wrapper');
            if (!wrapper) return;
            const input = wrapper.querySelector('input');
            if (!input) return;

            const isPassword = input.type === 'password';
            input.type = isPassword ? 'text' : 'password';

            const eyeIcon = this.querySelector('.eye-icon');
            const eyeSlashIcon = this.querySelector('.eye-slash-icon');

            if (eyeIcon && eyeSlashIcon) {
                eyeIcon.classList.toggle('hidden', isPassword);
                eyeSlashIcon.classList.toggle('hidden', !isPassword);
            }

            this.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
        });
    });

    // 6. Asynchronous Auth Form Handler (No page reload on error)
    function setupAjaxAuthForm(formId, alertId, submitBtnId, loadingText, successText) {
        const form = document.getElementById(formId);
        if (!form) return;

        const alertBox = document.getElementById(alertId);
        const submitBtn = document.getElementById(submitBtnId);

        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            // Clear previous errors
            form.querySelectorAll('.form-error').forEach(el => el.remove());
            form.querySelectorAll('.form-input-error').forEach(el => el.classList.remove('form-input-error'));
            if (alertBox) {
                alertBox.style.display = 'none';
                alertBox.textContent = '';
            }

            // Client-side pre-validation for registration passwords match
            if (formId === 'registerForm') {
                const p1 = document.getElementById('id_password1')?.value;
                const p2 = document.getElementById('id_password2')?.value;
                if (p1 && p2 && p1 !== p2) {
                    showFieldError('id_password2', 'The two password fields didn’t match.');
                    scrollToFirstError(document.getElementById('id_password2'));
                    return;
                }
            }

            if (formId === 'passwordResetConfirmForm') {
                const p1 = document.getElementById('id_new_password1')?.value;
                const p2 = document.getElementById('id_new_password2')?.value;
                if (p1 && p2 && p1 !== p2) {
                    showFieldError('id_new_password2', 'The two password fields didn’t match.');
                    scrollToFirstError(document.getElementById('id_new_password2'));
                    return;
                }
            }


            const originalBtnText = submitBtn ? submitBtn.innerHTML : '';
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = `<span class="spinner"></span> ${loadingText}`;
            }

            try {
                const formData = new FormData(form);
                const response = await fetch(form.action || window.location.href, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    if (submitBtn) submitBtn.innerHTML = successText;
                    window.location.href = data.redirect_url || '/';
                } else {
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = originalBtnText;
                    }

                    // Handle unverified user redirect from login
                    if (data.unverified && data.redirect_url) {
                        if (alertBox) {
                            alertBox.textContent = (data.errors && data.errors.__all__) ? data.errors.__all__[0] : 'Please verify your email address. Redirecting...';
                            alertBox.style.display = 'block';
                            scrollToFirstError(alertBox);
                        }
                        setTimeout(() => {
                            window.location.href = data.redirect_url;
                        }, 1200);
                        return;
                    }

                    if (data.errors) {
                        let firstErrorTarget = null;
                        for (const [field, fieldErrors] of Object.entries(data.errors)) {
                            if (field === '__all__' || field === 'non_field_errors') {
                                if (alertBox) {
                                    alertBox.textContent = Array.isArray(fieldErrors) ? fieldErrors[0] : fieldErrors;
                                    alertBox.style.display = 'block';
                                    if (!firstErrorTarget) firstErrorTarget = alertBox;
                                }
                            } else {
                                const inputId = 'id_' + field;
                                showFieldError(inputId, Array.isArray(fieldErrors) ? fieldErrors[0] : fieldErrors);
                                const inputEl = document.getElementById(inputId);
                                if (!firstErrorTarget && inputEl) firstErrorTarget = inputEl;
                            }
                        }
                        if (firstErrorTarget) {
                            scrollToFirstError(firstErrorTarget);
                        }
                    } else if (alertBox) {
                        alertBox.textContent = data.message || 'An unexpected error occurred. Please try again.';
                        alertBox.style.display = 'block';
                        scrollToFirstError(alertBox);
                    }
                }
            } catch (err) {
                console.error('AJAX form submission error:', err);
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalBtnText;
                }
                // Fallback to standard form submission
                form.submit();
            }
        });

        function scrollToFirstError(element) {
            if (!element) return;
            const target = element.closest('.form-group') || element;
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            });

            // Focus the input if available
            if (element.tagName === 'INPUT' || element.tagName === 'SELECT' || element.tagName === 'TEXTAREA') {
                setTimeout(() => {
                    element.focus({ preventScroll: true });
                }, 250);
            }
        }

        function showFieldError(inputId, message) {
            const input = document.getElementById(inputId);
            if (!input) {
                if (alertBox) {
                    alertBox.textContent = message;
                    alertBox.style.display = 'block';
                }
                return;
            }

            input.classList.add('form-input-error');
            const errDiv = document.createElement('div');
            errDiv.className = 'form-error';
            errDiv.style.marginTop = '0.35rem';
            errDiv.textContent = message;

            const wrapper = input.closest('.password-input-wrapper') || input;
            wrapper.insertAdjacentElement('afterend', errDiv);
        }
    }

    setupAjaxAuthForm('registerForm', 'registerAlert', 'registerSubmitBtn', 'Creating Account...', 'Account Created! Redirecting...');
    setupAjaxAuthForm('loginForm', 'loginAlert', 'loginSubmitBtn', 'Signing In...', 'Signed In! Redirecting...');
    setupAjaxAuthForm('verifyOtpForm', 'verifyOtpAlert', 'verifyOtpSubmitBtn', 'Verifying Code...', 'Verified! Redirecting...');
    setupAjaxAuthForm('passwordResetForm', 'passwordResetAlert', 'passwordResetSubmitBtn', 'Sending Link...', 'Link Sent! Redirecting...');
    setupAjaxAuthForm('passwordResetConfirmForm', 'passwordResetConfirmAlert', 'passwordResetConfirmSubmitBtn', 'Updating Password...', 'Updated! Redirecting...');

    // 7. OTP Numeric Filter and Auto-advance
    const otpInput = document.getElementById('id_otp_code');
    if (otpInput) {
        otpInput.addEventListener('input', function() {
            this.value = this.value.replace(/\D/g, '').slice(0, 6);
        });
    }

    // 8. Resend OTP with Dynamic Cooldown Timer
    const resendForm = document.getElementById('resendOtpForm');
    const resendBtn = document.getElementById('resendOtpBtn');
    const resendCountdown = document.getElementById('resendCountdown');
    const countdownSeconds = document.getElementById('countdownSeconds');
    let countdownTimer = null;

    function startCooldown(seconds) {
        if (!resendBtn || !resendCountdown || !countdownSeconds) return;
        resendBtn.disabled = true;
        resendCountdown.style.display = 'block';
        let remaining = seconds;
        countdownSeconds.textContent = remaining;

        if (countdownTimer) clearInterval(countdownTimer);
        countdownTimer = setInterval(() => {
            remaining -= 1;
            countdownSeconds.textContent = remaining;
            if (remaining <= 0) {
                clearInterval(countdownTimer);
                resendBtn.disabled = false;
                resendCountdown.style.display = 'none';
            }
        }, 1000);
    }

    if (resendForm && resendBtn) {
        resendForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const alertBox = document.getElementById('verifyOtpAlert');
            const originalText = resendBtn.innerHTML;
            resendBtn.disabled = true;
            resendBtn.innerHTML = 'Sending...';

            try {
                const formData = new FormData(resendForm);
                const response = await fetch(resendForm.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                const data = await response.json();
                if (response.ok && data.success) {
                    if (alertBox) {
                        alertBox.style.display = 'none';
                        alertBox.textContent = '';
                    }
                    showToast(data.message || 'Verification code resent successfully!', 'info', 10000);
                    resendBtn.innerHTML = originalText;
                    startCooldown(data.cooldown || 60);
                } else {
                    resendBtn.innerHTML = originalText;
                    if (response.status === 429 && data.remaining_seconds) {
                        startCooldown(data.remaining_seconds);
                    } else {
                        resendBtn.disabled = false;
                    }
                    showToast(data.message || 'Failed to resend verification code.', 'warning', 10000);
                }
            } catch (err) {
                console.error('Error resending OTP:', err);
                resendBtn.disabled = false;
                resendBtn.innerHTML = originalText;
                showToast('An unexpected error occurred. Please try again.', 'error', 10000);
            }
        });
    }


    // 9. Auto-scroll to first error on initial page load if server rendered errors
    const initialServerError = document.querySelector('.form-input-error, .form-error, .alert-error');
    if (initialServerError) {
        const errorContainer = initialServerError.closest('.form-group') || initialServerError;
        errorContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    // 10. Profile Management: Tabs, Avatar Live Preview, In-Place Profile & Password Updates, OTP-Verified Email Change
    const profileTabBtns = document.querySelectorAll('.profile-tab-btn[data-profile-tab]');
    if (profileTabBtns.length > 0) {
        function activateProfileTab(tabName) {
            profileTabBtns.forEach(btn => {
                const isActive = btn.getAttribute('data-profile-tab') === tabName;
                btn.classList.toggle('is-active', isActive);
                btn.setAttribute('aria-selected', isActive);
            });
            document.querySelectorAll('.profile-pane').forEach(pane => {
                pane.classList.toggle('is-active', pane.id === `pane-${tabName}`);
            });
        }

        profileTabBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const tab = btn.getAttribute('data-profile-tab');
                activateProfileTab(tab);
                const url = new URL(window.location.href);
                url.searchParams.set('tab', tab);
                window.history.replaceState({}, '', url.toString());
            });
        });

        // Check URL parameter on load: ?tab=edit, ?tab=password, ?tab=email
        const urlParams = new URLSearchParams(window.location.search);
        const requestedTab = urlParams.get('tab');
        if (requestedTab && ['overview', 'edit', 'password', 'email'].includes(requestedTab)) {
            activateProfileTab(requestedTab);
        }
    }

    // Avatar Live Preview & Size Validation
    const avatarInput = document.getElementById('id_avatar');
    if (avatarInput) {
        avatarInput.addEventListener('change', function() {
            const file = this.files && this.files[0];
            const errorEl = document.getElementById('error_avatar');
            if (!file) return;

            // Max 3MB
            if (file.size > 3 * 1024 * 1024) {
                if (errorEl) {
                    errorEl.textContent = 'Avatar image size cannot exceed 3MB.';
                    errorEl.style.display = 'block';
                }
                showToast('Avatar image size cannot exceed 3MB.', 'error');
                this.value = '';
                return;
            }

            if (errorEl) {
                errorEl.style.display = 'none';
                errorEl.textContent = '';
            }

            if (file.type && file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(evt) {
                    const previewCircle = document.getElementById('profileAvatarPreview');
                    if (previewCircle) {
                        previewCircle.innerHTML = `<img src="${evt.target.result}" alt="Preview" id="avatarPreviewImg" style="width: 100%; height: 100%; object-fit: cover;">`;
                    }
                    showToast('Photo selected! Click "Save Profile Details" to apply.', 'info', 4000);
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // Generic helper to clear form errors
    function clearFormErrors(form) {
        if (!form) return;
        form.querySelectorAll('.form-error').forEach(el => {
            el.textContent = '';
            el.style.display = 'none';
        });
        form.querySelectorAll('.form-input-error').forEach(el => {
            el.classList.remove('form-input-error');
        });
    }

    // Helper to render form errors
    function applyFormErrors(form, errors) {
        if (!form || !errors) return;
        let firstErrorInput = null;
        for (const [field, fieldErrors] of Object.entries(errors)) {
            const errorMsg = Array.isArray(fieldErrors) ? fieldErrors[0] : fieldErrors;
            const errorEl = form.querySelector(`#error_${field}`) || form.querySelector(`.form-error[data-field="${field}"]`);
            const inputEl = form.querySelector(`[name="${field}"]`);

            if (inputEl) {
                inputEl.classList.add('form-input-error');
                if (!firstErrorInput) firstErrorInput = inputEl;
            }

            if (errorEl) {
                errorEl.textContent = errorMsg;
                errorEl.style.display = 'block';
            }
        }
        if (firstErrorInput) {
            firstErrorInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
            firstErrorInput.focus();
        }
    }

    // Edit Profile Details AJAX Submission
    const profileDetailsForm = document.getElementById('profileDetailsForm');
    const saveProfileBtn = document.getElementById('saveProfileBtn');
    if (profileDetailsForm && saveProfileBtn) {
        profileDetailsForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            clearFormErrors(profileDetailsForm);
            const originalText = saveProfileBtn.innerHTML;
            saveProfileBtn.disabled = true;
            saveProfileBtn.innerHTML = '<span class="spinner"></span> Saving...';

            try {
                const formData = new FormData(profileDetailsForm);
                const response = await fetch(profileDetailsForm.action, {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });
                const data = await response.json();

                if (response.ok && data.success) {
                    showToast(data.message || 'Profile details updated successfully.', 'success');
                    if (data.full_name) {
                        const nameEl = document.getElementById('overviewFullName');
                        if (nameEl) nameEl.textContent = data.full_name;
                    }
                    if (data.avatar_url) {
                        const overviewAvatar = document.getElementById('overviewAvatarWrapper');
                        if (overviewAvatar) {
                            overviewAvatar.innerHTML = `<img src="${data.avatar_url}" alt="${data.full_name}" class="avatar" style="width: 96px; height: 96px;">`;
                        }
                    }
                    if (data.redirect_url) {
                        setTimeout(() => {
                            window.location.href = data.redirect_url;
                        }, 800);
                    }
                } else {
                    if (data.errors && Object.keys(data.errors).length > 0) {
                        applyFormErrors(profileDetailsForm, data.errors);
                    } else if (data.message) {
                        showToast(data.message, 'error');
                    }
                }
            } catch (err) {
                console.error('Error saving profile:', err);
                showToast('An unexpected error occurred. Please try again.', 'error');
            } finally {
                saveProfileBtn.disabled = false;
                saveProfileBtn.innerHTML = originalText;
            }
        });
    }

    // Change Password AJAX Submission
    const profilePasswordForm = document.getElementById('profilePasswordForm') || document.getElementById('passwordChangeForm');
    const changePasswordBtn = document.getElementById('changePasswordBtn') || document.getElementById('submitPasswordChangeBtn');
    if (profilePasswordForm && changePasswordBtn) {
        profilePasswordForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            clearFormErrors(profilePasswordForm);
            const originalText = changePasswordBtn.innerHTML;
            changePasswordBtn.disabled = true;
            changePasswordBtn.innerHTML = '<span class="spinner"></span> Updating...';

            try {
                const formData = new FormData(profilePasswordForm);
                const response = await fetch(profilePasswordForm.action, {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });
                const data = await response.json();

                if (response.ok && data.success) {
                    showToast(data.message || 'Password changed successfully.', 'success');
                    profilePasswordForm.reset();
                    if (data.redirect_url) {
                        setTimeout(() => {
                            window.location.href = data.redirect_url;
                        }, 1200);
                    }
                } else {
                    if (data.errors && Object.keys(data.errors).length > 0) {
                        applyFormErrors(profilePasswordForm, data.errors);
                    } else if (data.message) {
                        showToast(data.message, 'error');
                    }
                }
            } catch (err) {
                console.error('Error updating password:', err);
                showToast('An unexpected error occurred. Please try again.', 'error');
            } finally {
                changePasswordBtn.disabled = false;
                changePasswordBtn.innerHTML = originalText;
            }
        });
    }

    // Email Change Step 1: Request OTP
    const emailChangeRequestForm = document.getElementById('emailChangeRequestForm');
    const requestEmailChangeBtn = document.getElementById('requestEmailChangeBtn');
    const emailChangeStep1 = document.getElementById('emailChangeStep1');
    const emailChangeStep2 = document.getElementById('emailChangeStep2');
    const step2TargetEmail = document.getElementById('step2TargetEmail');

    if (emailChangeRequestForm && requestEmailChangeBtn) {
        emailChangeRequestForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            clearFormErrors(emailChangeRequestForm);
            const originalText = requestEmailChangeBtn.innerHTML;
            requestEmailChangeBtn.disabled = true;
            requestEmailChangeBtn.innerHTML = '<span class="spinner"></span> Sending code...';

            try {
                const formData = new FormData(emailChangeRequestForm);
                const response = await fetch(emailChangeRequestForm.action, {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });
                const data = await response.json();

                if (response.ok && data.success) {
                    showToast(data.message || 'Verification code sent to your new email.', 'info', 10000);
                    if (step2TargetEmail) {
                        step2TargetEmail.textContent = data.new_email;
                    }
                    if (emailChangeStep1) emailChangeStep1.style.display = 'none';
                    if (emailChangeStep2) {
                        emailChangeStep2.style.display = 'block';
                        const otpInput = emailChangeStep2.querySelector('input[name="otp_code"]');
                        if (otpInput) {
                            otpInput.value = '';
                            otpInput.focus();
                        }
                    }
                } else {
                    if (data.errors && Object.keys(data.errors).length > 0) {
                        applyFormErrors(emailChangeRequestForm, data.errors);
                    } else if (data.message) {
                        showToast(data.message, 'error');
                    }
                }
            } catch (err) {
                console.error('Error requesting email change:', err);
                showToast('An unexpected error occurred. Please try again.', 'error');
            } finally {
                requestEmailChangeBtn.disabled = false;
                requestEmailChangeBtn.innerHTML = originalText;
            }
        });
    }

    // Email Change Step 2: Verify OTP
    const emailChangeVerifyForm = document.getElementById('emailChangeVerifyForm');
    const verifyEmailChangeBtn = document.getElementById('verifyEmailChangeBtn');
    if (emailChangeVerifyForm && verifyEmailChangeBtn) {
        emailChangeVerifyForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            clearFormErrors(emailChangeVerifyForm);
            const originalText = verifyEmailChangeBtn.innerHTML;
            verifyEmailChangeBtn.disabled = true;
            verifyEmailChangeBtn.innerHTML = '<span class="spinner"></span> Verifying...';

            try {
                const formData = new FormData(emailChangeVerifyForm);
                const response = await fetch(emailChangeVerifyForm.action, {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });
                const data = await response.json();

                if (response.ok && data.success) {
                    showToast(data.message || 'Email changed successfully!', 'success', 10000);
                    // Update active email display
                    const activeEmailEl = document.getElementById('activeEmailText');
                    if (activeEmailEl) activeEmailEl.textContent = data.new_email;
                    const profileDisplayEmail = document.getElementById('profileDisplayEmail');
                    if (profileDisplayEmail) profileDisplayEmail.value = data.new_email;

                    if (data.redirect_url) {
                        setTimeout(() => {
                            window.location.href = data.redirect_url;
                        }, 800);
                    } else {
                        // Reset form and revert to Step 1
                        emailChangeVerifyForm.reset();
                        if (emailChangeRequestForm) emailChangeRequestForm.reset();
                        if (emailChangeStep2) emailChangeStep2.style.display = 'none';
                        if (emailChangeStep1) emailChangeStep1.style.display = 'block';
                    }
                } else {
                    if (data.errors && Object.keys(data.errors).length > 0) {
                        applyFormErrors(emailChangeVerifyForm, data.errors);
                    } else if (data.message) {
                        showToast(data.message, 'error');
                    }
                }
            } catch (err) {
                console.error('Error verifying email change:', err);
                showToast('An unexpected error occurred. Please try again.', 'error');
            } finally {
                verifyEmailChangeBtn.disabled = false;
                verifyEmailChangeBtn.innerHTML = originalText;
            }
        });
    }

    // Back to Step 1 Button
    const backToStep1Btn = document.getElementById('backToStep1Btn');
    if (backToStep1Btn) {
        backToStep1Btn.addEventListener('click', () => {
            if (emailChangeStep2) emailChangeStep2.style.display = 'none';
            if (emailChangeStep1) emailChangeStep1.style.display = 'block';
        });
    }

    // Resend Email Change OTP Button
    const resendEmailChangeOtpBtn = document.getElementById('resendEmailChangeOtpBtn');
    const emailOtpCooldown = document.getElementById('emailOtpCooldown');
    let emailCooldownTimer = null;

    function startEmailCooldown(seconds = 60) {
        if (!resendEmailChangeOtpBtn || !emailOtpCooldown) return;
        resendEmailChangeOtpBtn.disabled = true;
        let remaining = seconds;
        emailOtpCooldown.style.display = 'inline';
        emailOtpCooldown.textContent = `(${remaining}s)`;

        if (emailCooldownTimer) clearInterval(emailCooldownTimer);
        emailCooldownTimer = setInterval(() => {
            remaining -= 1;
            emailOtpCooldown.textContent = `(${remaining}s)`;
            if (remaining <= 0) {
                clearInterval(emailCooldownTimer);
                resendEmailChangeOtpBtn.disabled = false;
                emailOtpCooldown.style.display = 'none';
            }
        }, 1000);
    }

    if (resendEmailChangeOtpBtn) {
        resendEmailChangeOtpBtn.addEventListener('click', async () => {
            const originalText = resendEmailChangeOtpBtn.innerHTML;
            resendEmailChangeOtpBtn.disabled = true;
            resendEmailChangeOtpBtn.innerHTML = 'Sending...';

            try {
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
                const targetEmail = step2TargetEmail ? step2TargetEmail.textContent.trim() : '';

                const formData = new FormData();
                if (csrfToken) formData.append('csrfmiddlewaretoken', csrfToken);
                if (targetEmail) formData.append('new_email', targetEmail);

                const response = await fetch('/accounts/email-change/resend/', {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });
                const data = await response.json();

                if (response.ok && data.success) {
                    showToast(data.message || 'Verification code resent successfully.', 'info', 10000);
                    resendEmailChangeOtpBtn.innerHTML = originalText;
                    startEmailCooldown(data.cooldown || 60);
                } else {
                    resendEmailChangeOtpBtn.innerHTML = originalText;
                    if (response.status === 429 && data.cooldown) {
                        startEmailCooldown(data.cooldown);
                    } else {
                        resendEmailChangeOtpBtn.disabled = false;
                    }
                    showToast(data.message || 'Failed to resend code.', 'warning');
                }
            } catch (err) {
                console.error('Error resending email change OTP:', err);
                resendEmailChangeOtpBtn.disabled = false;
                resendEmailChangeOtpBtn.innerHTML = originalText;
                showToast('An unexpected error occurred. Please try again.', 'error');
            }
        });
    }
});

