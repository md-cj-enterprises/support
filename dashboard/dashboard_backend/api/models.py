from django.db import models

class TradingScript(models.Model):
    name = models.CharField(max_length=100, default="")
    ltp = models.IntegerField(default=0)
    position = models.IntegerField(default=0)
    net_quantity = models.IntegerField(default=0)
    entry_rate = models.IntegerField(default=0)
    m2m = models.IntegerField(default=0)

 
    def __str__(self):
        return self.name