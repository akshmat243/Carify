from rest_framework import serializers
from .models import *

# --- Master Data Serializers (Dropdowns ke liye) ---
class FuelTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleFuelType
        fields = ['id', 'name']

class TransmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleTransmission
        fields = ['id', 'name']

class EngineTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleEngineType
        fields = ['id', 'name']

# --- Customer Serializer ---
class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

# --- Vehicle Serializer ---
class VehicleSerializer(serializers.ModelSerializer):
    # Nested Serializers (Taaki dashboard par ID ki jagah Naam dikhe - Petrol, Manual etc.)
    fuel_type_details = FuelTypeSerializer(source='fuel_type', read_only=True)
    transmission_details = TransmissionSerializer(source='transmission', read_only=True)
    engine_type_details = EngineTypeSerializer(source='engine_type', read_only=True)
    
    # Customer ki details bhi dikhane ke liye
    customer_details = CustomerSerializer(source='customer', read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            'id', 'model', 'vin', 
            'fuel_type', 'fuel_type_details', 
            'transmission', 'transmission_details',
            'engine_type', 'engine_type_details',
            'customer', 'customer_details',
            'inspection_date', 'health_score', 'is_completed',
            'image'
        ]


class PaymentOrderSerializer(serializers.ModelSerializer):
    # Yeh fields frontend ko chahiye hongi payment kholne ke liye
    order_id = serializers.CharField(source='transaction_id')
    amount_paise = serializers.SerializerMethodField()
    key_id = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = ['id', 'model', 'payment_amount', 'amount_paise', 'order_id', 'payment_status', 'key_id']

    def get_amount_paise(self, obj):
        # Razorpay paise mein deal karta hai (100 Rs = 10000 Paise)
        return int(obj.payment_amount * 100)

    def get_key_id(self, obj):
        from django.conf import settings
        return settings.RAZORPAY_KEY_ID
    

class PaymentVerifySerializer(serializers.Serializer):
    vehicle_id = serializers.IntegerField()
    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()


class PaymentStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['id', 'model', 'payment_status', 'transaction_id', 'payment_amount']


class PaymentLinkResponseSerializer(serializers.ModelSerializer):
    """
    Serializer to format the response after generating a payment link.
    """
    payment_link_url = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = ['id', 'model', 'payment_status', 'payment_link_id', 'payment_link_url']

    def get_payment_link_url(self, obj):
        # We will pass the generated URL through the serializer context
        return self.context.get('short_url', '')
    
from .models import Customer # Import your Customer model

class CustomerSerializer(serializers.ModelSerializer):
    """
    Serializer for Customer data. 
    Validates name, phone, and email before saving.
    """
    class Meta:
        model = Customer
        fields = ['id', 'name', 'phone', 'email']


class VehicleSerializer(serializers.ModelSerializer):
    """
    Serializer for Vehicle Data.
    Handles validation for vehicle details and image uploads.
    """
    class Meta:
        model = Vehicle
        fields = '__all__'
        read_only_fields = ['customer', 'inspected_by', 'inspection_date']

class OBDReadingSerializer(serializers.ModelSerializer):
    """
    Serializer for OBD (On-Board Diagnostics) Readings.
    """
    class Meta:
        model = OBDReading
        fields = '__all__'
        read_only_fields = ['vehicle']


class SystemCheckSerializer(serializers.ModelSerializer):
    """
    Serializer to handle individual System Check entries.
    """
    class Meta:
        model = SystemCheck
        fields = ['id', 'vehicle', 'system', 'status', 'number_of_issues']


        








