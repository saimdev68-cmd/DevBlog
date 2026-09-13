from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from apps.blog.models import Category, Post
from apps.comments.models import Comment

User = get_user_model()


class DashboardTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            email='admin@example.com', password='Password123!', first_name='Admin', is_staff=True
        )
        self.reader_user = User.objects.create_user(
            email='reader@example.com', password='Password123!', first_name='Reader', is_staff=False
        )
        self.category = Category.objects.create(name='Python')
        self.post = Post.objects.create(
            title='My Dashboard Post',
            author=self.admin_user,
            category=self.category,
            content='Article content for testing',
            status='DRAFT',
        )

    def test_anonymous_access_redirects_to_login(self):
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_non_staff_user_forbidden_from_dashboard(self):
        self.client.login(email='reader@example.com', password='Password123!')
        
        # All dashboard views should return 403 Forbidden for regular readers
        index_resp = self.client.get(reverse('dashboard:index'))
        self.assertEqual(index_resp.status_code, 403)

        list_resp = self.client.get(reverse('dashboard:post_list'))
        self.assertEqual(list_resp.status_code, 403)

        create_resp = self.client.get(reverse('dashboard:post_create'))
        self.assertEqual(create_resp.status_code, 403)

        edit_resp = self.client.get(reverse('dashboard:post_edit', kwargs={'pk': self.post.pk}))
        self.assertEqual(edit_resp.status_code, 403)

        delete_resp = self.client.post(reverse('dashboard:post_delete', kwargs={'pk': self.post.pk}))
        self.assertEqual(delete_resp.status_code, 403)

        toggle_resp = self.client.post(reverse('dashboard:post_toggle_publish', kwargs={'pk': self.post.pk}))
        self.assertEqual(toggle_resp.status_code, 403)

    def test_staff_admin_can_access_dashboard(self):
        self.client.login(email='admin@example.com', password='Password123!')
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Editorial Overview')
        self.assertContains(response, 'My Dashboard Post')

    def test_staff_post_create_view(self):
        self.client.login(email='admin@example.com', password='Password123!')
        response = self.client.post(reverse('dashboard:post_create'), {
            'title': 'New Created Article',
            'category': self.category.pk,
            'content': 'Comprehensive guide content here.',
            'status': 'PUBLISHED',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Post.objects.filter(title='New Created Article').exists())

    def test_staff_post_edit(self):
        self.client.login(email='admin@example.com', password='Password123!')
        response = self.client.post(reverse('dashboard:post_edit', kwargs={'pk': self.post.pk}), {
            'title': 'Updated Article Title',
            'category': self.category.pk,
            'content': 'Updated content.',
            'status': 'PUBLISHED',
        })
        self.assertEqual(response.status_code, 302)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Updated Article Title')

    def test_staff_toggle_publish_status(self):
        self.client.login(email='admin@example.com', password='Password123!')
        self.assertEqual(self.post.status, 'DRAFT')
        response = self.client.post(reverse('dashboard:post_toggle_publish', kwargs={'pk': self.post.pk}))
        self.assertEqual(response.status_code, 302)
        self.post.refresh_from_db()
        self.assertEqual(self.post.status, 'PUBLISHED')

    def test_staff_post_delete(self):
        self.client.login(email='admin@example.com', password='Password123!')
        response = self.client.post(reverse('dashboard:post_delete', kwargs={'pk': self.post.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())
