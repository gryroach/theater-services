from django.urls import path

from movies.api.v1 import views

urlpatterns = [
    path('movies/', views.MoviesListApi.as_view()),
    path('movies/<uuid:pk>/', views.MoviesDetailApi.as_view()),
    path('persons/', views.PersonsListApi.as_view()),
    path('persons/<uuid:pk>/', views.PersonsDetailApi.as_view()),
    path('genres/', views.GenresListApi.as_view()),
    path('genres/<uuid:pk>/', views.GenresDetailApi.as_view()),
]
