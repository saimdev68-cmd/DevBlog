/**
 * DevBlog - Modern Skeleton Loading & Image Progression System
 * Premium Editorial UX for Slow Connections, Image Decodes, and Async Actions
 */

(function() {
    'use strict';

    const DevBlogSkeleton = {
        /**
         * Initialize progressive image loading across all image skeleton containers
         */
        initImages: function(root = document) {
            const containers = root.querySelectorAll('.image-skeleton-container');

            containers.forEach(container => {
                const img = container.querySelector('img.progressive-img');
                if (!img) return;

                const markLoaded = () => {
                    img.classList.add('is-loaded');
                    container.classList.add('image-loaded');
                };

                const markFailed = () => {
                    container.classList.add('image-loaded');
                    img.style.display = 'none';

                    // Insert elegant fallback icon if not already present
                    if (!container.querySelector('.image-fallback-placeholder')) {
                        const fallback = document.createElement('div');
                        fallback.className = 'image-fallback-placeholder';
                        fallback.innerHTML = `
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                                <circle cx="8.5" cy="8.5" r="1.5"></circle>
                                <polyline points="21 15 16 10 5 21"></polyline>
                            </svg>
                            <span>DevBlog Image</span>
                        `;
                        container.appendChild(fallback);
                    }
                };

                // Check if image is already cached / decoded by the browser
                if (img.complete && img.naturalWidth !== 0) {
                    markLoaded();
                } else if (img.complete && img.naturalWidth === 0) {
                    markFailed();
                } else {
                    img.addEventListener('load', markLoaded, { once: true });
                    img.addEventListener('error', markFailed, { once: true });
                }
            });
        },

        /**
         * Apply button loading micro-state
         */
        setButtonLoading: function(btn, loadingText = '') {
            if (!btn || btn.classList.contains('is-loading')) return;
            btn.dataset.originalHtml = btn.innerHTML;
            btn.classList.add('is-loading');
            btn.disabled = true;

            if (loadingText) {
                // If button contains standard text, wrap or update
                btn.innerHTML = `<span class="spinner" style="width: 14px; height: 14px; display: inline-block; vertical-align: middle; margin-right: 0.4rem; border: 2px solid rgba(255,255,255,0.3); border-top-color: currentColor; border-radius: 50%; animation: spin 0.6s linear infinite;"></span> ${loadingText}`;
            }
        },

        /**
         * Reset button from loading micro-state
         */
        resetButton: function(btn) {
            if (!btn) return;
            btn.classList.remove('is-loading');
            btn.disabled = false;
            if (btn.dataset.originalHtml) {
                btn.innerHTML = btn.dataset.originalHtml;
                delete btn.dataset.originalHtml;
            }
        },

        /**
         * Display a structured skeleton within a container
         */
        showSkeleton: function(container, skeletonHtml) {
            if (!container) return;
            container.setAttribute('aria-busy', 'true');
            if (typeof skeletonHtml === 'string') {
                container.innerHTML = skeletonHtml;
            } else if (skeletonHtml instanceof Node) {
                container.innerHTML = '';
                container.appendChild(skeletonHtml);
            }
        },

        /**
         * Replace skeleton with real content
         */
        hideSkeleton: function(container, realContentHtml) {
            if (!container) return;
            container.setAttribute('aria-busy', 'false');
            if (realContentHtml) {
                container.style.opacity = '0';
                container.innerHTML = realContentHtml;
                // Fade in new content smoothly
                requestAnimationFrame(() => {
                    container.style.transition = 'opacity 0.25s ease-in-out';
                    container.style.opacity = '1';
                });
            }
            this.initImages(container);
        },

        /**
         * Render an editorial error state with a retry button
         */
        showError: function(container, message = 'Unable to load content at this moment.', retryCallback = null) {
            if (!container) return;
            container.setAttribute('aria-busy', 'false');

            const errorBox = document.createElement('div');
            errorBox.className = 'skeleton-error-state';
            errorBox.innerHTML = `
                <div style="font-size: 2rem; margin-bottom: 0.75rem;">⚡</div>
                <h3 style="font-size: 1.2rem; margin-bottom: 0.5rem; color: var(--color-text);">Content Unavailable</h3>
                <p>${message}</p>
            `;

            if (typeof retryCallback === 'function') {
                const retryBtn = document.createElement('button');
                retryBtn.type = 'button';
                retryBtn.className = 'btn btn-primary btn-sm';
                retryBtn.style.marginTop = '0.5rem';
                retryBtn.innerHTML = '↻ Try Again';
                retryBtn.addEventListener('click', () => {
                    retryCallback();
                });
                errorBox.appendChild(retryBtn);
            }

            container.innerHTML = '';
            container.appendChild(errorBox);
        },
        /**
         * Return HTML string for a grid of article card skeletons
         */
        getCardsSkeletonHtml: function(count = 6) {
            const cardHtml = `
                <article class="skeleton-card" aria-hidden="true">
                    <div class="skeleton skeleton-card-thumb"></div>
                    <div class="skeleton-card-body">
                        <div class="skeleton skeleton-badge skeleton-w-25" style="margin-bottom: 0.75rem; height: 1rem; width: 75px;"></div>
                        <div class="skeleton skeleton-title skeleton-w-90"></div>
                        <div class="skeleton skeleton-title skeleton-w-65" style="height: 1.2rem; margin-bottom: 1rem;"></div>
                        <div class="skeleton-paragraph" style="margin-bottom: 1.25rem;">
                            <div class="skeleton skeleton-text skeleton-w-100"></div>
                            <div class="skeleton skeleton-text skeleton-w-95"></div>
                            <div class="skeleton skeleton-text skeleton-w-60"></div>
                        </div>
                        <div class="skeleton-card-meta">
                            <div class="flex items-center gap-2">
                                <div class="skeleton skeleton-avatar skeleton-avatar-sm"></div>
                                <div class="skeleton skeleton-text" style="width: 85px; height: 0.8rem; margin-bottom: 0;"></div>
                            </div>
                            <div class="flex items-center gap-3">
                                <div class="skeleton skeleton-meta" style="width: 38px;"></div>
                                <div class="skeleton skeleton-meta" style="width: 58px;"></div>
                            </div>
                        </div>
                    </div>
                </article>
            `;
            let gridHtml = `<div class="grid grid-cols-3 gap-6" style="margin-bottom: 3.5rem;">`;
            for (let i = 0; i < count; i++) {
                gridHtml += cardHtml;
            }
            gridHtml += `</div>`;
            return gridHtml;
        },

        /**
         * Intercept category tabs and pagination for zero-jump skeleton transitions
         */
        initAjaxNavigation: function() {
            const container = document.getElementById('postsGridContainer');
            if (!container) return;

            const loadPage = async (url, push = true) => {
                DevBlogSkeleton.showSkeleton(container, DevBlogSkeleton.getCardsSkeletonHtml(6));
                try {
                    const response = await fetch(url, {
                        headers: { 'X-Requested-With': 'XMLHttpRequest' }
                    });
                    if (!response.ok) throw new Error('HTTP error ' + response.status);
                    const htmlText = await response.text();
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(htmlText, 'text/html');
                    const newContainer = doc.getElementById('postsGridContainer');

                    if (newContainer) {
                        DevBlogSkeleton.hideSkeleton(container, newContainer.innerHTML);
                        if (push) {
                            window.history.pushState({ url: url }, '', url);
                        }
                    } else {
                        window.location.href = url;
                    }
                } catch (err) {
                    console.error('AJAX navigation error:', err);
                    DevBlogSkeleton.showError(container, 'Unable to load publications. Please check your network connection.', () => {
                        loadPage(url, false);
                    });
                }
            };

            // Category tabs within filter card
            document.querySelectorAll('a[href*="/blog/category/"], a[href$="/blog/"]').forEach(link => {
                if (link.closest('.card')) {
                    link.addEventListener('click', function(e) {
                        e.preventDefault();
                        const targetUrl = this.getAttribute('href');
                        if (!targetUrl) return;

                        link.closest('.flex').querySelectorAll('.badge').forEach(b => {
                            b.classList.remove('badge-primary');
                            b.classList.add('badge-secondary');
                        });
                        this.classList.remove('badge-secondary');
                        this.classList.add('badge-primary');

                        loadPage(targetUrl, true);
                    });
                }
            });

            // Pagination clicks
            container.addEventListener('click', function(e) {
                const paginationLink = e.target.closest('.pagination a');
                if (paginationLink) {
                    e.preventDefault();
                    const targetUrl = paginationLink.getAttribute('href');
                    if (targetUrl) {
                        loadPage(targetUrl, true);
                        container.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                }
            });

            // Browser back/forward navigation
            window.addEventListener('popstate', function(e) {
                if (e.state && e.state.url) {
                    loadPage(e.state.url, false);
                }
            });
        }
    };

    // Expose globally
    window.DevBlogSkeleton = DevBlogSkeleton;

    // Auto-initialize on DOM ready
    document.addEventListener('DOMContentLoaded', () => {
        DevBlogSkeleton.initImages();
        DevBlogSkeleton.initAjaxNavigation();

        // Form submission loading protection (prevents double submits, adds accessible micro-state)
        const trackedForms = document.querySelectorAll(
            '#profileDetailsForm, #profilePasswordForm, #passwordChangeForm, #emailChangeRequestForm, #emailChangeVerifyForm, #commentForm, #postForm, #contactForm, form[action*="add_comment"], form[action*="contact"]'
        );

        trackedForms.forEach(form => {
            form.addEventListener('submit', function(e) {
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn && !submitBtn.disabled && !form.dataset.submitting) {
                    form.dataset.submitting = 'true';
                    submitBtn.classList.add('is-loading');
                }
            });
        });
    });
})();
