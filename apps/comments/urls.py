from django.urls import path
from . import views

app_name = 'comments'

urlpatterns = [
    path('add/<slug:post_slug>/', views.add_comment, name='add_comment'),
]
