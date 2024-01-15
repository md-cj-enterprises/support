from django.db import models

class Script(models.Model):
    name = models.CharField(max_length=100)
    ltp = models.IntegerField()
 
    def __str__(self):
        return self.name
