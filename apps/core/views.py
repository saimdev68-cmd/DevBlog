from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from apps.blog.models import Category, Post


class HomeView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch both featured and latest posts in a single query with with_counts()
        posts = list(
            Post.objects.published()
            .select_related('category', 'author', 'author__profile')
            .prefetch_related('tags')
            .with_counts()
            .order_by('-is_featured', '-published_at', '-created_at')[:7]
        )

        featured_post = posts[0] if posts else None
        latest_posts = posts[1:] if len(posts) > 1 else []

        context['featured_post'] = featured_post
        context['latest_posts'] = latest_posts


        # Popular categories with post count
        context['popular_categories'] = (
            Category.objects.annotate(num_posts=Count('posts'))
            .filter(num_posts__gt=0)
            .order_by('-num_posts')[:6]
        )
        return context


class AboutView(TemplateView):
    template_name = 'core/about.html'


class ContactView(TemplateView):
    template_name = 'core/contact.html'

    def post(self, request, *args, **kwargs):
        name = (request.POST.get('name') or '').strip()
        email = (request.POST.get('email') or '').strip()
        subject = (request.POST.get('subject') or '').strip()
        message = (request.POST.get('message') or '').strip()

        if not (name and email and message):
            messages.error(request, "Please fill in all required fields.")
            return render(request, self.template_name, {'name': name, 'email': email, 'subject': subject, 'message': message})

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please provide a valid email address.")
            return render(request, self.template_name, {'name': name, 'email': email, 'subject': subject, 'message': message})

        if len(name) > 100 or len(subject) > 200 or len(message) > 5000:
            messages.error(request, "One or more fields exceed maximum allowed length.")
            return render(request, self.template_name, {'name': name, 'email': email, 'subject': subject, 'message': message})

        messages.success(request, "Thank you for reaching out! Your message has been received.")
        return redirect('core:contact')


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /dashboard/",
        "Disallow: /accounts/",
        "Sitemap: " + request.build_absolute_uri('/sitemap.xml'),
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
