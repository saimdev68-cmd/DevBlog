import math
import re
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, db_index=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "category"
        verbose_name_plural = "categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:category', kwargs={'slug': self.slug})

    @property
    def published_posts_count(self):
        return self.posts.filter(status='PUBLISHED').count()


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "tag"
        verbose_name_plural = "tags"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:tag', kwargs={'slug': self.slug})


class PostQuerySet(models.QuerySet):
    def published(self):
        return self.filter(
            status='PUBLISHED',
            published_at__lte=timezone.now()
        )

    def featured(self):
        return self.published().filter(is_featured=True)

    def with_counts(self):
        from django.db.models import Count
        return self.annotate(
            likes_count=Count('likes', distinct=True)
        )


class PostManager(models.Manager):
    def get_queryset(self):
        return PostQuerySet(self.model, using=self._db)

    def published(self):
        return self.get_queryset().published()

    def featured(self):
        return self.get_queryset().featured()

    def with_counts(self):
        return self.get_queryset().with_counts()



class Post(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
        ('SCHEDULED', 'Scheduled'),
    )

    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=280, unique=True, db_index=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts',
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')
    excerpt = models.TextField(
        blank=True,
        help_text="Short summary of the article. If left blank, one will be generated from content.",
    )
    content = models.TextField(help_text="Article body content.")
    featured_image = models.ImageField(upload_to='posts/%Y/%m/', blank=True, null=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='DRAFT', db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = PostManager()

    class Meta:
        verbose_name = "post"
        verbose_name_plural = "posts"
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Generate unique slug only if it does not already exist
        if not self.slug:
            base_slug = slugify(self.title) or "post"
            slug = base_slug
            counter = 1
            while Post.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        # Fallback excerpt generation
        if not self.excerpt and self.content:
            plain_text = strip_tags(self.content).strip()
            self.excerpt = plain_text[:180] + ("..." if len(plain_text) > 180 else "")

        # Set published_at if moving to PUBLISHED status
        if self.status == 'PUBLISHED' and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.slug})

    @property
    def reading_time(self):
        """Calculates estimated reading time in minutes assuming 200 wpm."""
        text = strip_tags(self.content)
        words = len(re.findall(r'\w+', text))
        minutes = math.ceil(words / 200)
        return max(1, minutes)

    @property
    def approved_comments_count(self):
        if hasattr(self, '_approved_comments_count'):
            return self._approved_comments_count
        return self.comments.filter(is_approved=True).count()

    @approved_comments_count.setter
    def approved_comments_count(self, value):
        self._approved_comments_count = value

    @property
    def likes_count(self):
        if hasattr(self, '_likes_count'):
            return self._likes_count
        return self.likes.count()

    @likes_count.setter
    def likes_count(self, value):
        self._likes_count = value




class ArticleLike(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='likes',
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='likes',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "article like"
        verbose_name_plural = "article likes"
        constraints = [
            models.UniqueConstraint(fields=['user', 'post'], name='unique_user_post_like')
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} likes {self.post.title}"


class ReadLater(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='read_later_entries',
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='read_later_entries',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "read later entry"
        verbose_name_plural = "read later entries"
        constraints = [
            models.UniqueConstraint(fields=['user', 'post'], name='unique_user_post_read_later')
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} saved {self.post.title} for later"

