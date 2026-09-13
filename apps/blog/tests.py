from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .models import Category, Post, Tag

User = get_user_model()


class BlogModelAndViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='author@example.com', password='Password123!', first_name='Alex')
        self.category = Category.objects.create(name='Django', description='Django web framework')
        self.tag = Tag.objects.create(name='Python')
        self.post = Post.objects.create(
            title='Understanding Django Models in Depth',
            author=self.user,
            category=self.category,
            content='Django models provide an abstraction over database tables. ' * 50,
            status='PUBLISHED',
            published_at=timezone.now(),
        )
        self.post.tags.add(self.tag)

    def test_category_and_tag_slug_generation(self):
        self.assertEqual(self.category.slug, 'django')
        self.assertEqual(self.tag.slug, 'python')
        self.assertEqual(self.category.get_absolute_url(), '/blog/category/django/')
        self.assertEqual(self.tag.get_absolute_url(), '/blog/tag/python/')

    def test_post_slug_and_reading_time(self):
        self.assertEqual(self.post.slug, 'understanding-django-models-in-depth')
        self.assertGreaterEqual(self.post.reading_time, 1)
        self.assertTrue(bool(self.post.excerpt))

    def test_unique_slug_generation_for_duplicate_title(self):
        second_post = Post.objects.create(
            title='Understanding Django Models in Depth',
            author=self.user,
            category=self.category,
            content='Second post content',
            status='DRAFT',
        )
        self.assertEqual(second_post.slug, 'understanding-django-models-in-depth-1')

    def test_blog_list_view(self):
        response = self.client.get(reverse('blog:post_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post.title)

    def test_blog_detail_view_and_view_count(self):
        initial_views = self.post.views
        response = self.client.get(reverse('blog:post_detail', kwargs={'slug': self.post.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post.title)
        
        self.post.refresh_from_db()
        self.assertEqual(self.post.views, initial_views + 1)

        # Refresh within same session should not increment views again
        self.client.get(reverse('blog:post_detail', kwargs={'slug': self.post.slug}))
        self.post.refresh_from_db()
        self.assertEqual(self.post.views, initial_views + 1)

    def test_category_and_tag_views(self):
        cat_resp = self.client.get(reverse('blog:category', kwargs={'slug': self.category.slug}))
        self.assertEqual(cat_resp.status_code, 200)
        self.assertContains(cat_resp, self.post.title)

        tag_resp = self.client.get(reverse('blog:tag', kwargs={'slug': self.tag.slug}))
        self.assertEqual(tag_resp.status_code, 200)
        self.assertContains(tag_resp, self.post.title)

    def test_search_view(self):
        search_resp = self.client.get(reverse('blog:search') + '?q=Django')
        self.assertEqual(search_resp.status_code, 200)
        self.assertContains(search_resp, self.post.title)

    def test_feed_view(self):
        feed_resp = self.client.get(reverse('blog:feed'))
        self.assertEqual(feed_resp.status_code, 200)
        self.assertEqual(feed_resp['Content-Type'], 'application/rss+xml; charset=utf-8')

    def test_sitemap_view(self):
        sitemap_resp = self.client.get('/sitemap.xml')
        self.assertEqual(sitemap_resp.status_code, 200)
        self.assertEqual(sitemap_resp['Content-Type'], 'application/xml')

    def test_article_like_toggle_and_uniqueness(self):
        # Anonymous like redirects to login
        anon_resp = self.client.post(reverse('blog:toggle_like', kwargs={'slug': self.post.slug}))
        self.assertEqual(anon_resp.status_code, 302)
        self.assertIn('/accounts/login/', anon_resp.url)

        # Authenticated user likes article
        reader = User.objects.create_user(email='reader@example.com', password='Password123!')
        self.client.login(email='reader@example.com', password='Password123!')

        resp = self.client.post(reverse('blog:toggle_like', kwargs={'slug': self.post.slug}))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['liked'])
        self.assertEqual(data['like_count'], 1)
        self.assertEqual(self.post.likes_count, 1)

        # Detail view includes user_has_liked = True
        detail_resp = self.client.get(reverse('blog:post_detail', kwargs={'slug': self.post.slug}))
        self.assertEqual(detail_resp.status_code, 200)
        self.assertTrue(detail_resp.context['user_has_liked'])

        # Liking again unlikes (toggles)
        resp2 = self.client.post(reverse('blog:toggle_like', kwargs={'slug': self.post.slug}))
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.json()
        self.assertFalse(data2['liked'])
        self.assertEqual(data2['like_count'], 0)
        self.assertEqual(self.post.likes_count, 0)

    def test_duplicate_like_db_constraint(self):
        from django.db import IntegrityError
        from .models import ArticleLike
        reader = User.objects.create_user(email='reader2@example.com', password='Password123!')
        ArticleLike.objects.create(user=reader, post=self.post)
        with self.assertRaises(IntegrityError):
            ArticleLike.objects.create(user=reader, post=self.post)

    def test_draft_post_access_permissions(self):
        draft_post = Post.objects.create(
            title='Secret Draft Article',
            author=self.user,
            category=self.category,
            content='Draft content only admins can see',
            status='DRAFT',
        )

        # Anonymous cannot view draft (404)
        anon_resp = self.client.get(reverse('blog:post_detail', kwargs={'slug': draft_post.slug}))
        self.assertEqual(anon_resp.status_code, 404)

        # Normal logged-in reader cannot view draft (404)
        reader = User.objects.create_user(email='reader3@example.com', password='Password123!', is_staff=False)
        self.client.login(email='reader3@example.com', password='Password123!')
        reader_resp = self.client.get(reverse('blog:post_detail', kwargs={'slug': draft_post.slug}))
        self.assertEqual(reader_resp.status_code, 404)

        # Staff admin can view draft (200)
        admin = User.objects.create_user(email='admin_staff@example.com', password='Password123!', is_staff=True)
        self.client.login(email='admin_staff@example.com', password='Password123!')
        admin_resp = self.client.get(reverse('blog:post_detail', kwargs={'slug': draft_post.slug}))
        self.assertEqual(admin_resp.status_code, 200)
        self.assertContains(admin_resp, 'Secret Draft Article')

