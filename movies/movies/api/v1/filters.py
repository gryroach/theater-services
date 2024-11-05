from django_filters import rest_framework as filters

from movies.models import Filmwork, Person, Genre


class _UUIDInFilter(filters.BaseInFilter, filters.UUIDFilter):
    pass


class BaseFilter(filters.FilterSet):
    ids = _UUIDInFilter(field_name='id', lookup_expr='in')
    modified = filters.IsoDateTimeFilter(
        field_name='modified', lookup_expr='gt'
    )


class FilmWorkFilter(BaseFilter):
    person = _UUIDInFilter(field_name='persons', lookup_expr='in')
    genre = _UUIDInFilter(field_name='genres', lookup_expr='in')

    class Meta:
        model = Filmwork
        fields = ['ids', 'modified', 'person', 'genre']


class PersonFilter(BaseFilter):
    class Meta:
        model = Person
        fields = ['ids', 'modified']


class GenreFilter(BaseFilter):
    class Meta:
        model = Genre
        fields = ['ids', 'modified']
