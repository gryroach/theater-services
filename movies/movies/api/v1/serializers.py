from rest_framework import serializers

from movies.models import Filmwork, Person, Genre


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = (
            'id',
            'full_name',
            'gender',
            'modified',
        )


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = (
            'id',
            'name',
            'description',
            'modified',
        )


class FilmworkSerializer(serializers.ModelSerializer):
    genres_list = serializers.ListSerializer(child=serializers.CharField())
    directors = serializers.ListSerializer(child=serializers.JSONField())
    actors = serializers.ListSerializer(child=serializers.JSONField())
    writers = serializers.ListSerializer(child=serializers.JSONField())

    class Meta:
        model = Filmwork
        fields = (
            'id',
            'rating',
            'genres_list',
            'title',
            'description',
            'directors',
            'actors',
            'writers',
            'modified',
        )
