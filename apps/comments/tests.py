from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from apps.blog.models import Category, Post
from .models import Comment

User = get_user_model()


class CommentTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(email='author@example.com', password='Password123!', first_name='Author')
        self.reader = User.objects.create_user(email='reader@example.com', password='Password123!', first_name='Reader')
        self.category = Category.objects.create(name='Architecture')
        self.post = Post.objects.create(
            title='Building High Scalability Backends',
            author=self.author,
            category=self.category,
            content='Content for scalability article',
            status='PUBLISHED',
        )

    def test_anonymous_user_cannot_comment(self):
        response = self.client.post(reverse('comments:add_comment', kwargs={'post_slug': self.post.slug}), {
            'content': 'Great post!',
        })
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_authenticated_user_comment_requires_moderation(self):
        self.client.login(email='reader@example.com', password='Password123!')
        response = self.client.post(reverse('comments:add_comment', kwargs={'post_slug': self.post.slug}), {
            'content': 'This was a very insightful writeup.',
        })
        self.assertEqual(response.status_code, 302)

        comment = Comment.objects.get(post=self.post, user=self.reader)
        self.assertFalse(comment.is_approved)

    def test_author_comment_is_auto_approved(self):
        self.client.login(email='author@example.com', password='Password123!')
        response = self.client.post(reverse('comments:add_comment', kwargs={'post_slug': self.post.slug}), {
            'content': 'Thanks for reading everyone!',
        })
        self.assertEqual(response.status_code, 302)

        comment = Comment.objects.get(post=self.post, user=self.author)
        self.assertTrue(comment.is_approved)
