from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q, QuerySet, Value, F
from django.db.models.functions import JSONObject, Coalesce
from django_filters import rest_framework as filters
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import OrderingFilter

from movies.api.v1.filters import FilmWorkFilter, PersonFilter, GenreFilter
from movies.api.v1.serializers import (
    FilmworkSerializer, PersonSerializer, GenreSerializer
)
from movies.models import Filmwork, PersonFilmwork, Person, Genre


class MoviesApiMixin:
    def get_queryset(self) -> QuerySet:
        base_queryset = Filmwork.objects.all()
        genres_annotation = ArrayAgg(
            'genres__name',
            filter=Q(genres__isnull=False),
            distinct=True,
            default=Value([]),
        )
        actors_annotation = Coalesce(
            ArrayAgg(
                JSONObject(
                    id=F('persons__id'),
                    full_name=F('persons__full_name'),
                ),
                filter=Q(personfilmwork__role=PersonFilmwork.RoleChoices.ACTOR),
                distinct=True
            ),
            Value([]),
        )
        directors_annotation = Coalesce(
            ArrayAgg(
                JSONObject(
                    id=F('persons__id'),
                    full_name=F('persons__full_name'),
                ),
                filter=Q(personfilmwork__role=PersonFilmwork.RoleChoices.DIRECTOR),
                distinct=True
            ),
            Value([]),
        )
        writers_annotation = Coalesce(
            ArrayAgg(
                JSONObject(
                    id=F('persons__id'),
                    full_name=F('persons__full_name'),
                ),
                filter=Q(personfilmwork__role=PersonFilmwork.RoleChoices.WRITER),
                distinct=True
            ),
            Value([]),
        )
        queryset = base_queryset.annotate(
            genres_list=genres_annotation,
            actors=actors_annotation,
            directors=directors_annotation,
            writers=writers_annotation,
        )
        return queryset


class MoviesListApi(MoviesApiMixin, ListAPIView):
    pagination_class = PageNumberPagination
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    filterset_class = FilmWorkFilter
    serializer_class = FilmworkSerializer
    ordering_fields = ['title', 'creation_date', 'rating', 'created', 'modified']
    ordering = ['creation_date']


class MoviesDetailApi(MoviesApiMixin, RetrieveAPIView):
    serializer_class = FilmworkSerializer


class PersonsListApi(ListAPIView):
    queryset = Person.objects.all()
    pagination_class = PageNumberPagination
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    filterset_class = PersonFilter
    serializer_class = PersonSerializer
    ordering_fields = ['full_name', 'created', 'modified']
    ordering = ['created']


class PersonsDetailApi(RetrieveAPIView):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer


class GenresListApi(ListAPIView):
    queryset = Genre.objects.all()
    pagination_class = PageNumberPagination
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    filterset_class = GenreFilter
    serializer_class = GenreSerializer
    ordering_fields = ['name', 'created', 'modified']
    ordering = ['created']


class GenresDetailApi(RetrieveAPIView):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
