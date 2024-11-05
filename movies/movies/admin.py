from django.contrib import admin

from movies.models import Filmwork, Genre, GenreFilmwork, Person, PersonFilmwork


class GenreFilmworkInline(admin.TabularInline):
    model = GenreFilmwork
    extra = 1
    raw_id_fields = ('genre',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('genre', 'film_work')


class PersonFilmworkInline(admin.TabularInline):
    model = PersonFilmwork
    extra = 1
    raw_id_fields = ('person',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('person', 'film_work')


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    search_fields = ('full_name',)


@admin.register(Filmwork)
class FilmworkAdmin(admin.ModelAdmin):
    inlines = (GenreFilmworkInline, PersonFilmworkInline)
    list_display = ('title', 'creation_date', 'rating', 'type')
    list_filter = ('type', 'creation_date')
    search_fields = ('title', 'id')
