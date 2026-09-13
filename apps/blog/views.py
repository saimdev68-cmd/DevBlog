from django.contrib.auth.decorators import login_required
from django.db.models import Q, F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView
from .models import ArticleLike, Category, Post, Tag
from apps.comments.forms import CommentForm


class PostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        qs = (
            Post.objects.published()
            .select_related('category', 'author', 'author__profile')
            .prefetch_related('tags')
            .with_counts()
        )
        category_slug = self.request.GET.get('category')
        tag_slug = self.request.GET.get('tag')

        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        if tag_slug:
            qs = qs.filter(tags__slug=tag_slug)

        return qs.order_by('-published_at', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['tags'] = Tag.objects.all()
        context['selected_category'] = self.request.GET.get('category')
        context['selected_tag'] = self.request.GET.get('tag')
        return context


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'

    def get_queryset(self):
        # Allow staff to preview drafts, but normal users can only view published articles
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return Post.objects.all().select_related('category', 'author', 'author__profile').prefetch_related('tags').with_counts()
        return Post.objects.published().select_related('category', 'author', 'author__profile').prefetch_related('tags').with_counts()

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        
        # Session-based view counting to prevent refresh abuse
        session_key = 'viewed_posts'
        viewed_posts = self.request.session.get(session_key, [])
        if obj.pk not in viewed_posts:
            # Atomically increment views in database and memory without extra round-trip
            Post.objects.filter(pk=obj.pk).update(views=F('views') + 1)
            obj.views += 1
            viewed_posts.append(obj.pk)
            self.request.session[session_key] = viewed_posts
        
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object

        # Related posts: same category or tags, excluding current post
        related_posts = list(
            Post.objects.published()
            .filter(Q(category=post.category) | Q(tags__in=post.tags.all()))
            .exclude(pk=post.pk)
            .distinct()
            .select_related('category', 'author', 'author__profile')
            .prefetch_related('tags')
            .with_counts()[:3]
        )
        if len(related_posts) < 3:
            needed = 3 - len(related_posts)
            exclude_pks = [post.pk] + [p.pk for p in related_posts]
            fallback = list(
                Post.objects.published()
                .exclude(pk__in=exclude_pks)
                .select_related('category', 'author', 'author__profile')
                .prefetch_related('tags')
                .with_counts()[:needed]
            )
            related_posts.extend(fallback)

        context['related_posts'] = related_posts

        # Approved comments (evaluated as list to prevent duplicate COUNT queries)
        comments = list(post.comments.filter(is_approved=True).select_related('user', 'user__profile'))
        context['comments'] = comments
        context['comment_form'] = CommentForm()


        # Previous and Next articles
        context['previous_post'] = (
            Post.objects.published()
            .filter(published_at__lt=post.published_at or post.created_at)
            .order_by('-published_at', '-created_at')
            .first()
        )
        context['next_post'] = (
            Post.objects.published()
            .filter(published_at__gt=post.published_at or post.created_at)
            .order_by('published_at', 'created_at')
            .first()
        )

        # User like status
        user_has_liked = False
        if self.request.user.is_authenticated:
            user_has_liked = post.likes.filter(user=self.request.user).exists()
        context['user_has_liked'] = user_has_liked

        return context


@login_required
@require_POST
def toggle_like(request, slug):
    post = get_object_or_404(Post, slug=slug, status='PUBLISHED')
    like, created = ArticleLike.objects.get_or_create(user=request.user, post=post)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True

    return JsonResponse({
        'liked': liked,
        'like_count': post.likes.count(),
    })


class CategoryPostListView(ListView):
    model = Post
    template_name = 'blog/category.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        return (
            Post.objects.published()
            .filter(category=self.category)
            .select_related('category', 'author', 'author__profile')
            .prefetch_related('tags')
            .with_counts()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['total_articles'] = self.category.posts.filter(status='PUBLISHED').count()
        return context


class TagPostListView(ListView):
    model = Post
    template_name = 'blog/tag.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        self.tag = get_object_or_404(Tag, slug=self.kwargs['slug'])
        return (
            Post.objects.published()
            .filter(tags=self.tag)
            .select_related('category', 'author', 'author__profile')
            .prefetch_related('tags')
            .with_counts()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = self.tag
        context['total_articles'] = self.tag.posts.filter(status='PUBLISHED').count()
        return context


class PostSearchView(ListView):
    model = Post
    template_name = 'blog/search.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        if not query:
            return Post.objects.none()

        return (
            Post.objects.published()
            .filter(
                Q(title__icontains=query) |
                Q(excerpt__icontains=query) |
                Q(content__icontains=query) |
                Q(category__name__icontains=query) |
                Q(tags__name__icontains=query)
            )
            .distinct()
            .select_related('category', 'author', 'author__profile')
            .prefetch_related('tags')
            .with_counts()
        )


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '').strip()
        context['total_results'] = self.get_queryset().count()
        return context
