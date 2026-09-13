from django.contrib import admin
from .models import Category, Tag, Post, ArticleLike


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at', 'updated_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'status', 'is_featured', 'views', 'published_at', 'created_at']
    list_filter = ['status', 'is_featured', 'category', 'created_at', 'published_at']
    search_fields = ['title', 'excerpt', 'content', 'author__email', 'author__first_name', 'author__last_name']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('tags',)
    readonly_fields = ['views', 'created_at', 'updated_at']
    date_hierarchy = 'published_at'
    ordering = ['-published_at', '-created_at']
    actions = ['make_published', 'make_draft', 'make_featured', 'remove_featured']

    @admin.action(description='Mark selected posts as Published')
    def make_published(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='PUBLISHED', published_at=timezone.now())

    @admin.action(description='Mark selected posts as Draft')
    def make_draft(self, request, queryset):
        queryset.update(status='DRAFT')

    @admin.action(description='Mark selected posts as Featured')
    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)

    @admin.action(description='Remove Featured flag from selected posts')
    def remove_featured(self, request, queryset):
        queryset.update(is_featured=False)


@admin.register(ArticleLike)
class ArticleLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']
    search_fields = ['user__email', 'post__title']
    list_filter = ['created_at']
    ordering = ['-created_at']
