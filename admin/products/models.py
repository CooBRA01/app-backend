from django.db import models

class Product(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='products/')
    likes = models.PositiveIntegerField(default=0)

class User(models.Model):
    pass