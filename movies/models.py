from django.db import models


class SynoSession(models.Model):
    account = models.CharField(max_length=50, primary_key=True)
    sid = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now=True)


class LibrarySection(models.Model):
    uuid = models.CharField(max_length=32, primary_key=True)
    title = models.CharField(max_length=50)
    changed_at = models.IntegerField()


class Movie(models.Model):
    guid = models.CharField(max_length=255, primary_key=True)
    title = models.CharField(max_length=255)
    year = models.IntegerField()
    thumb = models.CharField(max_length=255)
    added_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    section = models.ForeignKey(LibrarySection, on_delete=models.CASCADE)


class Media(models.Model):
    id = models.IntegerField(primary_key=True)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)


class MediaPart(models.Model):
    id = models.IntegerField(primary_key=True)
    path = models.CharField(max_length=255)
    best_path = models.CharField(max_length=255)
    media = models.ForeignKey(Media, on_delete=models.CASCADE)
