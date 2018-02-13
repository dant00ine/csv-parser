from django.db import models

class Batch(models.Model):
    name = models.CharField(max_length=255)
    created_date = models.DateTimeField()

class File(models.Model):
    file_type = models.CharField(max_length=255)
    filepath = models.CharField(max_length=255)
    group = models.ForeignKey(Batch, on_delete=models.CASCADE)
    created_date = models.DateTimeField()


