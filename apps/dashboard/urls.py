from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardIndexView.as_view(), name='index'),
    path('overview/', views.DashboardIndexView.as_view(), name='overview'),
    path('posts/', views.PostManageListView.as_view(), name='post_list'),
    path('posts/create/', views.PostCreateView.as_view(), name='post_create'),
    path('posts/<int:pk>/edit/', views.PostEditView.as_view(), name='post_edit'),
    path('posts/<int:pk>/delete/', views.PostDeleteView.as_view(), name='post_delete'),
    path('posts/<int:pk>/toggle-publish/', views.toggle_post_status, name='post_toggle_publish'),
    path('comments/', views.CommentManageListView.as_view(), name='comment_list'),
    path('comments/<int:pk>/approve/', views.approve_comment, name='comment_approve'),
    path('comments/<int:pk>/delete/', views.delete_comment, name='comment_delete'),
    path('categories/', views.CategoryManageListView.as_view(), name='category_list'),
    path('tags/', views.TagManageListView.as_view(), name='tag_list'),
]
