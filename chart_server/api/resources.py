from import_export import resources
from .models import Candle
 
class EmployeeResource(resources.ModelResource):
    class Meta:
        model = Candle
