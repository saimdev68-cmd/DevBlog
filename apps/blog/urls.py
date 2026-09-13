from django.urls import path
from . import views
from .feeds import LatestPostsFeed

app_name = 'blog'

urlpatterns = [
    path('', views.PostListView.as_view(), name='post_list'),
    path('search/', views.PostSearchView.as_view(), name='search'),
    path('feed/', LatestPostsFeed(), name='feed'),
    path('category/<slug:slug>/', views.CategoryPostListView.as_view(), name='category'),
    path('tag/<slug:slug>/', views.TagPostListView.as_view(), name='tag'),
    path('reading-list/', views.ReadLaterListView.as_view(), name='reading_list'),
    path('<slug:slug>/like/', views.toggle_like, name='toggle_like'),
    path('<slug:slug>/toggle-read-later/', views.toggle_read_later, name='toggle_read_later'),
    path('<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),


]
