from django.db import models


class Job(models.Model):
    date = models.DateField()
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    url = models.URLField()
    english = models.CharField(max_length=255)
    experience = models.IntegerField()
    technologies = models.ManyToManyField('Technology', related_name='jobs')


class Technology(models.Model):
    name = models.CharField(max_length=100, unique=True)
