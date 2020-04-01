from django.urls import path
from . import views

urlpatterns = [
    path('', views.movies, name='movies'),
    path('sync', views.sync, name='sync'),
    path('rename', views.rename_all, name='rename_all'),
    path('<int:id>/rename/', views.rename, name='rename'),
]
