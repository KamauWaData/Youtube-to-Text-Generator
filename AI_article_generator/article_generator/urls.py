from django.urls import path
from .import views

urlpatterns = [
    path('',views.index, name='index'),
    path('signin',views.user_signin, name='signin'),
    path('signup', views.user_signup, name='signup'),
    path('logout', views.user_logout, name='logout'),
    path('generate_blog', views.generateBlog, name='generateBlog'),
    path('articles', views.blog_list, name='blog_list'),
    path('article-details', views.blog_details, name='blog-details'),
]