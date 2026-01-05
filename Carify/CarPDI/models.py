from django.db import models
from User.models import CustomUser

class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone=models.CharField(max_length=10)
    email=models.EmailField(max_length=254)

    def __str__(self):
        return f"{self.name} - {self.email} - {self.phone}"
    
class Status(models.Model):
    name = models.CharField(max_length=50)
    def __str__(self):
        return self.name
    

class VehicleFuelType(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name
    
class VehicleTransmission(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name
    
class VehicleEngineType(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class Vehicle(models.Model):

    payment_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ], default='pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_amount = models.FloatField(default=500.0) 
    payment_link_id = models.CharField(max_length=100, blank=True, null=True)

    image = models.ImageField(upload_to='cars')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    model = models.CharField(max_length=100)
    vin = models.CharField(max_length=50, unique=True)
    fuel_type = models.ForeignKey(VehicleFuelType, on_delete=models.CASCADE)
    transmission = models.ForeignKey(VehicleTransmission, on_delete=models.CASCADE)
    engine_cc = models.IntegerField(null=True, blank=True)
    engine_type = models.ForeignKey(VehicleEngineType, on_delete=models.CASCADE)
    bhp = models.CharField(max_length=20)
    airbags = models.CharField(max_length=1)
    mileage_kmpl = models.FloatField(null=True, blank=True)
    ncap_rating = models.CharField(max_length=20, null=True, blank=True)
    num_keys = models.IntegerField(null=True, blank=True)
    inspection_date = models.DateField(auto_now_add=True)
    inspected_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='inspected_vehicles')
    health_score = models.FloatField()
    is_completed = models.BooleanField(default=False) 


    def __str__(self):
        return f"{self.model} - {self.model} - {self.vin}"
    
class OBDReading(models.Model):
    vehicle = models.OneToOneField(Vehicle, on_delete=models.CASCADE)
    avg_city_running_kms = models.IntegerField()
    pre_delivery_odo_kms = models.IntegerField()
    current_odo_kms = models.IntegerField()
    obd_running_kms = models.IntegerField()
    obd_tampering = models.BooleanField()

class System(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class SystemCheck(models.Model):

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    status = models.ForeignKey(Status, on_delete=models.CASCADE)
    number_of_issues = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.system}: {self.status} ({self.number_of_issues})"
    
class NetworkArea(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name
    
class NetworkSystem(models.Model):

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    area = models.ForeignKey(NetworkArea, on_delete=models.CASCADE)
    status = models.ForeignKey(Status, on_delete=models.CASCADE)
    remark = models.CharField(max_length=200 )

class FluidArea(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name
    
class FluidRange(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class FluidLevel(models.Model):

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    area = models.ForeignKey(FluidArea, on_delete=models.CASCADE)
    in_range = models.ForeignKey(FluidRange, on_delete=models.CASCADE)
    contamination = models.ForeignKey(Status, on_delete=models.CASCADE)
    recommendation = models.CharField(max_length=100)

class VoltageInference(models.Model):

    voltage = models.CharField(max_length=20)
    engine_state = models.CharField(max_length=20)
    interence = models.CharField(max_length=70)
    recommendation = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.voltage}, {self.engine_state}, {self.interence}, {self.recommendation}"

class Parameters(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class LiveParameters(models.Model):

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    system = models.ForeignKey(Parameters, on_delete=models.CASCADE)
    interence = models.ForeignKey(VoltageInference, on_delete=models.CASCADE)

class Performance(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name    

class PerformanceCheck(models.Model):

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    system = models.ForeignKey(Performance, on_delete=models.CASCADE)
    status = models.ForeignKey(Status, on_delete=models.CASCADE)
    recommendation = models.CharField(max_length=100)

class PaintArea(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name
    

class PaintFinish(models.Model):

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    area = models.ForeignKey(PaintArea, on_delete=models.CASCADE)
    repainted = models.BooleanField(default=False)

    condition = models.ForeignKey(Status, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)

class TyrePosition(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class TyreCondition(models.Model):
    
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    position = models.ForeignKey(TyrePosition, on_delete=models.CASCADE)
    brand = models.CharField(max_length=50)
    condition = models.ForeignKey(Status, on_delete=models.CASCADE)
    remaining_life_percent = models.FloatField()

class FlushArea(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class Operations(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name   

class FlushGap(models.Model):

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    area = models.ForeignKey(FlushArea, on_delete=models.CASCADE)
    operation = models.ForeignKey(Operations, on_delete=models.CASCADE)
    observation_gap = models.CharField(max_length=20)
    action = models.CharField(max_length=100)

class RubberArea(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class RubberComponent(models.Model):

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    area = models.ForeignKey(RubberArea, on_delete=models.CASCADE)
    condition = models.ForeignKey(Status, on_delete=models.CASCADE)
    recommendation = models.CharField(max_length=100)

class GlassArea(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class GlassComponent(models.Model):

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    area = models.ForeignKey(GlassArea, on_delete=models.CASCADE)
    brand = models.CharField(max_length=50)
    condition = models.ForeignKey(Status, on_delete=models.CASCADE)
    recommendation = models.CharField(max_length=100)

class InteriorArea(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class InteriorCategory(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class InteriorComponent(models.Model):

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    category = models.ForeignKey(InteriorCategory, on_delete=models.CASCADE)
    area = models.ForeignKey(InteriorArea, on_delete=models.CASCADE)
    condition = models.ForeignKey(Status, on_delete=models.CASCADE)
    recommendation = models.CharField(max_length=100)

class DocumentType(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class Documentation(models.Model):
   
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    document = models.ForeignKey(DocumentType, on_delete=models.CASCADE)
    status = models.ForeignKey(Status, on_delete=models.CASCADE)
    remark = models.CharField(max_length=200)
