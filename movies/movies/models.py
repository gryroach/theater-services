import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class UUIDMixin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimeStampedMixin(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Genre(UUIDMixin, TimeStampedMixin):
    name = models.CharField(_('name'), max_length=255, unique=True)
    description = models.TextField(_('description'), blank=True, null=True)

    class Meta:
        db_table = "content\".\"genre"
        verbose_name = _('Genre')
        verbose_name_plural = _('Genres')

    def __str__(self):
        return self.name


class Person(UUIDMixin, TimeStampedMixin):
    class Gender(models.TextChoices):
        MALE = 'male', _('male')
        FEMALE = 'female', _('female')

    full_name = models.CharField(_('full name'), max_length=255)
    gender = models.TextField(_('gender'), choices=Gender.choices, blank=True, null=True)

    class Meta:
        db_table = "content\".\"person"
        verbose_name = _('Person')
        verbose_name_plural = _('Persons')
        indexes = [
            models.Index(fields=['full_name'], name='person_full_name_idx'),
        ]

    def __str__(self):
        return self.full_name


class Filmwork(UUIDMixin, TimeStampedMixin):
    class TypeChoices(models.TextChoices):
        MOVIE = 'movie', _('movie')
        TV_SHOW = 'tv_show', _('tv_show')

    title = models.TextField(_('title'))
    description = models.TextField(_('description'), blank=True, null=True)
    creation_date = models.DateField(_('creation date'), blank=True, null=True)
    rating = models.FloatField(
        _('rating'),
        blank=True,
        null=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
    )
    type = models.CharField(_('type'), max_length=32, choices=TypeChoices, default=TypeChoices.MOVIE.value)
    certificate = models.CharField(_('certificate'), max_length=512, blank=True, null=True)
    file_path = models.FileField(_('file'), blank=True, null=True, upload_to='filmworks/')
    genres = models.ManyToManyField(Genre, through='GenreFilmwork', related_name='genre_filmworks')
    persons = models.ManyToManyField(Person, through='PersonFilmwork', related_name='person_filmworks')

    class Meta:
        db_table = "content\".\"film_work"
        verbose_name = _('Filmwork')
        verbose_name_plural = _('Filmworks')
        ordering = ('-creation_date',)
        indexes = [
            models.Index(fields=['creation_date', 'rating'], name='film_work_creation_date_idx'),
            models.Index(fields=['title'], name='film_work_title_idx'),
            models.Index(fields=['rating'], name='film_work_rating_idx'),
        ]

    def __str__(self):
        return self.title


class GenreFilmwork(UUIDMixin):
    film_work = models.ForeignKey('Filmwork', on_delete=models.CASCADE)
    genre = models.ForeignKey('Genre', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "content\".\"genre_film_work"
        constraints = [
            models.UniqueConstraint('genre', 'film_work', name='film_work_genre_idx')
        ]

    def __str__(self):
        return f'{self.genre} - {self.film_work}'


class PersonFilmwork(UUIDMixin):
    class RoleChoices(models.TextChoices):
        ACTOR = 'actor', _('actor')
        DIRECTOR = 'director', _('director')
        WRITER = 'writer', _('writer')
        PRODUCER = 'producer', _('producer')
        FILM_CREW = 'film crew', _('film crew')

    person = models.ForeignKey('Person', on_delete=models.CASCADE)
    film_work = models.ForeignKey('Filmwork', on_delete=models.CASCADE)
    role = models.CharField(_('role'), max_length=255, choices=RoleChoices, default=RoleChoices.ACTOR.value)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "content\".\"person_film_work"
        constraints = [
            models.UniqueConstraint('film_work', 'person', 'role', name='film_work_person_role_idx')
        ]
        indexes = [
            models.Index(fields=['person', 'film_work'], name='person_film_work_idx'),
        ]

    def __str__(self):
        return f'{self.person} - {self.film_work}'
