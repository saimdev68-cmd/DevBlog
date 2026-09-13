"""
URL configuration for DevBlog project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from apps.blog.feeds import LatestPostsFeed
from apps.blog.sitemaps import CategorySitemap, PostSitemap, StaticViewSitemap

sitemaps = {
    'posts': PostSitemap,
    'categories': CategorySitemap,
    'static': StaticViewSitemap,
}

from apps.accounts import views as account_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('blog/', include('apps.blog.urls')),
    path('comments/', include('apps.comments.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    path('feed/', LatestPostsFeed(), name='feed'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    # Direct convenience routes
    path('login/', account_views.LoginView.as_view(), name='login'),
    path('logout/', account_views.logout_view, name='logout'),
    path('register/', account_views.RegisterView.as_view(), name='register'),
    path('verify-otp/', account_views.verify_otp_view, name='verify_otp'),
    path('resend-otp/', account_views.resend_otp_view, name='resend_otp'),
    path('profile/', account_views.current_profile_view, name='profile'),
]


if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])



