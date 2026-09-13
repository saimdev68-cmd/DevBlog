from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from apps.blog.models import Post
from .forms import CommentForm
from .models import Comment


@login_required
@require_POST
def add_comment(request, post_slug):
    post = get_object_or_404(Post, slug=post_slug)

    # Only allow comments on published posts unless author or staff
    if post.status != 'PUBLISHED' and not (request.user.is_staff or post.author == request.user):
        raise Http404("Post not found.")

    # Flood protection: prevent spamming comments within 5 seconds
    last_comment = Comment.objects.filter(user=request.user).order_by('-created_at').first()
    if last_comment and (timezone.now() - last_comment.created_at).total_seconds() < 5:
        messages.warning(request, "Please wait a few seconds before posting another comment.")
        return redirect(post.get_absolute_url() + '#comments')

    form = CommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.user = request.user
        # Moderation requirement: author comments can be auto-approved, others require approval
        if post.author == request.user or request.user.is_staff:
            comment.is_approved = True
            messages.success(request, "Your comment has been posted.")
        else:
            comment.is_approved = False
            messages.success(request, "Thank you! Your comment has been submitted and is pending author moderation.")
        comment.save()
    else:
        messages.error(request, "Unable to post comment. Please provide valid text.")

    return redirect(post.get_absolute_url() + '#comments')
