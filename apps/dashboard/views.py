from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView
from apps.blog.forms import CategoryForm, PostForm, TagForm
from apps.blog.models import Category, Post, Tag
from apps.comments.models import Comment


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restricts access exclusively to active staff / admin users."""

    def test_func(self):
        return bool(self.request.user.is_authenticated and self.request.user.is_active and self.request.user.is_staff)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        raise PermissionDenied("Only administrators can access the editorial dashboard.")


class DashboardIndexView(StaffRequiredMixin, TemplateView):
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        all_posts = Post.objects.all()
        total_posts = all_posts.count()
        published_posts = all_posts.filter(status='PUBLISHED').count()
        draft_posts = all_posts.filter(status='DRAFT').count()
        total_views = all_posts.aggregate(total=Sum('views'))['total'] or 0

        all_comments = Comment.objects.all()
        total_comments = all_comments.count()
        pending_comments = all_comments.filter(is_approved=False).count()

        context['stats'] = {
            'total_posts': total_posts,
            'published_posts': published_posts,
            'draft_posts': draft_posts,
            'total_views': total_views,
            'total_comments': total_comments,
            'pending_comments': pending_comments,
        }

        context['recent_posts'] = all_posts.select_related('category', 'author')[:5]
        context['recent_comments'] = all_comments.select_related('user', 'post')[:5]

        return context


class PostManageListView(StaffRequiredMixin, ListView):
    model = Post
    template_name = 'dashboard/posts/list.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        qs = Post.objects.all().select_related('category', 'author').prefetch_related('tags')

        status_filter = self.request.GET.get('status')
        if status_filter in ('DRAFT', 'PUBLISHED', 'SCHEDULED'):
            qs = qs.filter(status=status_filter)

        search_query = self.request.GET.get('q')
        if search_query:
            qs = qs.filter(title__icontains=search_query)

        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_status'] = self.request.GET.get('status', 'ALL')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class PostCreateView(StaffRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'dashboard/posts/create.html'
    success_url = reverse_lazy('dashboard:post_list')

    def form_valid(self, form):
        form.instance.author = self.request.user
        if form.instance.status == 'PUBLISHED' and not form.instance.published_at:
            form.instance.published_at = timezone.now()
        messages.success(self.request, "Article created successfully!")
        return super().form_valid(form)


class PostEditView(StaffRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'dashboard/posts/edit.html'
    success_url = reverse_lazy('dashboard:post_list')

    def form_valid(self, form):
        if form.instance.status == 'PUBLISHED' and not form.instance.published_at:
            form.instance.published_at = timezone.now()
        messages.success(self.request, "Article updated successfully!")
        return super().form_valid(form)


class PostDeleteView(StaffRequiredMixin, DeleteView):
    model = Post
    template_name = 'dashboard/posts/delete.html'
    success_url = reverse_lazy('dashboard:post_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Article has been deleted.")
        return super().delete(request, *args, **kwargs)


@login_required
@require_POST
def toggle_post_status(request, pk):
    if not (request.user.is_active and request.user.is_staff):
        raise PermissionDenied("Only administrators can modify article status.")

    post = get_object_or_404(Post, pk=pk)
    if post.status == 'PUBLISHED':
        post.status = 'DRAFT'
        messages.info(request, f"'{post.title}' unpublished and moved to draft.")
    else:
        post.status = 'PUBLISHED'
        if not post.published_at:
            post.published_at = timezone.now()
        messages.success(request, f"'{post.title}' is now published.")
    post.save()
    return redirect('dashboard:post_list')


class CommentManageListView(StaffRequiredMixin, ListView):
    model = Comment
    template_name = 'dashboard/comments/list.html'
    context_object_name = 'comments'
    paginate_by = 15

    def get_queryset(self):
        return Comment.objects.all().select_related('post', 'user', 'user__profile').order_by('-created_at')


@login_required
@require_POST
def approve_comment(request, pk):
    if not (request.user.is_active and request.user.is_staff):
        raise PermissionDenied("Only administrators can moderate comments.")

    comment = get_object_or_404(Comment, pk=pk)
    comment.is_approved = True
    comment.save()
    messages.success(request, "Comment approved.")
    return redirect('dashboard:comment_list')


@login_required
@require_POST
def delete_comment(request, pk):
    if not (request.user.is_active and request.user.is_staff):
        raise PermissionDenied("Only administrators can delete comments.")

    comment = get_object_or_404(Comment, pk=pk)
    comment.delete()
    messages.success(request, "Comment removed.")
    return redirect('dashboard:comment_list')


class CategoryManageListView(StaffRequiredMixin, ListView):
    model = Category
    template_name = 'dashboard/categories/list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.annotate(total_posts=Count('posts')).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CategoryForm()
        return context

    def post(self, request, *args, **kwargs):
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category created successfully.")
            return redirect('dashboard:category_list')
        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)


class TagManageListView(StaffRequiredMixin, ListView):
    model = Tag
    template_name = 'dashboard/tags/list.html'
    context_object_name = 'tags'

    def get_queryset(self):
        return Tag.objects.annotate(total_posts=Count('posts')).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = TagForm()
        return context

    def post(self, request, *args, **kwargs):
        form = TagForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Tag created successfully.")
            return redirect('dashboard:tag_list')
        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)
