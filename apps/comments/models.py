from django.conf import settings
from django.db import models


class Comment(models.Model):
    post = models.ForeignKey(
        'blog.Post',
        on_delete=models.CASCADE,
        related_name='comments',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    content = models.TextField(help_text="Comment text.")
    is_approved = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Designates whether this comment has been approved for publication.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "comment"
        verbose_name_plural = "comments"
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.user.email} on {self.post.title}"
