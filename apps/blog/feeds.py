from django.contrib.syndication.views import Feed
from django.urls import reverse_lazy
from .models import Post


class LatestPostsFeed(Feed):
    title = "DevBlog - Latest Developer Articles"
    link = reverse_lazy('core:home')
    description = "Updates, tutorials, and engineering articles from DevBlog."

    def items(self):
        return Post.objects.published()[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.excerpt or item.content[:200]

    def item_pubdate(self, item):
        return item.published_at or item.created_at
