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
    Serializer for System Check entries.
    Includes explicit names for System and Status for better readability.
    """
    # Read-Only Fields (Sirf dekhne ke liye, data save karte waqt ignore honge)
    system_name = serializers.CharField(source='system.name', read_only=True)
    status_name = serializers.CharField(source='status.name', read_only=True)

    class Meta:
        model = SystemCheck
        # Ab hum ID aur Name dono bhej rahe hain
        fields = [
            'id', 
            'vehicle', 
            'system',       # ID (e.g., 1)
            'system_name',  # Name (e.g., "Engine")
            'status',       # ID (e.g., 2)
            'status_name',  # Name (e.g., "Leaking")
            'number_of_issues'
        ]



class NetworkSystemSerializer(serializers.ModelSerializer):
    """
    Serializer for Network System entries.
    Shows Area Name and Status Name explicitly for better Frontend understanding.
    """
    # Read-Only Fields (Display ke liye)
    area_name = serializers.CharField(source='area.name', read_only=True)
    status_name = serializers.CharField(source='status.name', read_only=True)

    class Meta:
        model = NetworkSystem
        fields = [
            'id', 
            'vehicle', 
            'area',        # ID (e.g., 1)
            'area_name',   # Name (e.g., "CAN High")
            'status',      # ID (e.g., 2)
            'status_name', # Name (e.g., "OK")
            'remark'       # Text remark
        ]


class LiveParameterSerializer(serializers.ModelSerializer):
    """
    Serializer for Live Parameters.
    Fetches names for 'System' (Parameter) and 'Inference' (Voltage/Result)
    to show clear details in the API response.
    """
    # Read-Only fields for Display (UX)
    # Note: 'system' linked to Parameters model
    system_name = serializers.CharField(source='system.name', read_only=True)
    
    # Note: 'interence' linked to VoltageInference model (based on your model field name)
    inference_value = serializers.CharField(source='interence.voltage', read_only=True)
    inference_id = serializers.PrimaryKeyRelatedField(source='interence', read_only=True)

    class Meta:
        model = LiveParameters
        fields = [
            'id', 
            'vehicle', 
            'system',       # ID sent by frontend
            'system_name',  # Name returned by backend
            'inference_id',    # ID sent by frontend (Field name matches your model)
            'inference_value' # Value returned by backend
        ]
        

class PerformanceCheckSerializer(serializers.ModelSerializer):
    """
    Serializer for Performance Checks.
    Includes explicit names for System and Status for better UI display.
    """
    # Read-Only Fields (Bas dekhne ke liye)
    system_name = serializers.CharField(source='system.name', read_only=True)
    status_name = serializers.CharField(source='status.name', read_only=True)

    class Meta:
        model = PerformanceCheck
        fields = [
            'id', 
            'vehicle', 
            'system',       # ID (Input)
            'system_name',  # Name (Output)
            'status',       # ID (Input)
            'status_name',  # Name (Output)
            'recommendation' # Text
        ]


class FluidLevelSerializer(serializers.ModelSerializer):
    """
    Serializer for Fluid Level Checks.
    Includes Area, Range, and Contamination names for readable GET responses.
    """
    area_name = serializers.CharField(source='area.name', read_only=True)
    range_name = serializers.CharField(source='in_range.name', read_only=True)
    contamination_name = serializers.CharField(source='contamination.name', read_only=True)

    class Meta:
        model = FluidLevel
        fields = [
            'id', 'vehicle', 'area', 'area_name', 
            'in_range', 'range_name', 'contamination', 
            'contamination_name', 'recommendation'
        ]

class TyreConditionSerializer(serializers.ModelSerializer):
    """
    Serializer for Tyre Condition Checks.
    Exposes Position and Condition names for better API consumption.
    """
    position_name = serializers.CharField(source='position.name', read_only=True)
    condition_name = serializers.CharField(source='condition.name', read_only=True)

    class Meta:
        model = TyreCondition
        fields = [
            'id', 'vehicle', 'position', 'position_name', 
            'brand', 'condition', 'condition_name', 
            'remaining_life_percent'
        ]


class PaintFinishSerializer(serializers.ModelSerializer):
    """
    Serializer for Paint and Finish Quality.
    Shows Area name and Condition status for a clear inspection report.
    """
    area_name = serializers.CharField(source='area.name', read_only=True)
    condition_name = serializers.CharField(source='condition.name', read_only=True)

    class Meta:
        model = PaintFinish
        fields = [
            'id', 'vehicle', 'area', 'area_name', 
            'repainted', 'condition', 'condition_name', 'action'
        ]


class FlushGapSerializer(serializers.ModelSerializer):
    """
    Serializer for Flush and Gap Inspection.
    Returns names for Area and Operation for a readable inspection report.
    """
    area_name = serializers.CharField(source='area.name', read_only=True)
    operation_name = serializers.CharField(source='operation.name', read_only=True)

    class Meta:
        model = FlushGap
        fields = [
            'id', 'vehicle', 'area', 'area_name', 
            'operation', 'operation_name', 'observation_gap', 'action'
        ]



class RubberComponentSerializer(serializers.ModelSerializer):
    """
    Serializer for Rubber Components Inspection.
    Returns names for Area and Condition for a clear report.
    """
    area_name = serializers.CharField(source='area.name', read_only=True)
    condition_name = serializers.CharField(source='condition.name', read_only=True)

    class Meta:
        model = RubberComponent
        fields = [
            'id', 'vehicle', 'area', 'area_name', 
            'condition', 'condition_name', 'recommendation'
        ]

class GlassComponentSerializer(serializers.ModelSerializer):
    """
    Serializer for Glass Components (Windshield, Mirrors, Windows).
    Returns names for Area and Condition for a clear inspection report.
    """
    area_name = serializers.CharField(source='area.name', read_only=True)
    condition_name = serializers.CharField(source='condition.name', read_only=True)

    class Meta:
        model = GlassComponent
        fields = [
            'id', 'vehicle', 'area', 'area_name', 
            'brand', 'condition', 'condition_name', 'recommendation'
        ]


class InteriorComponentSerializer(serializers.ModelSerializer):
    """
    Serializer for Interior Components Inspection.
    Returns names for Category, Area, and Condition for a detailed interior report.
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    area_name = serializers.CharField(source='area.name', read_only=True)
    condition_name = serializers.CharField(source='condition.name', read_only=True)

    class Meta:
        model = InteriorComponent
        fields = [
            'id', 'vehicle', 'category', 'category_name', 
            'area', 'area_name', 'condition', 'condition_name', 
            'recommendation'
        ]


class DocumentationSerializer(serializers.ModelSerializer):
    """
    Serializer for Vehicle Documentation (RC, Insurance, Manuals).
    Returns names for Document Type and Status for the final PDI report.
    """
    document_name = serializers.CharField(source='document.name', read_only=True)
    status_name = serializers.CharField(source='status.name', read_only=True)

    class Meta:
        model = Documentation
        fields = [
            'id', 'vehicle', 'document', 'document_name', 
            'status', 'status_name', 'remark'
        ]