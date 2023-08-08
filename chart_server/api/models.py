from django.db import models
from django_unixdatetimefield import UnixDateTimeField

class Candle(models.Model):
  date = models.FloatField()
  open = models.FloatField()
  high = models.FloatField()
  low = models.FloatField()
  close = models.FloatField()
  signal = models.IntegerField()
  mark_index = models.TextField(null=True)
  volume = models.FloatField()
  
  entry_point = models.FloatField()
  exit_point = models.FloatField()
  entry_position = models.FloatField()
  stop_loss = models.FloatField()
  profit = models.FloatField()
  turn_to0 = models.IntegerField()
                 
  objects = models.Manager()
