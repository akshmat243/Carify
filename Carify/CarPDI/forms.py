from django import forms
from .models import (
    Customer, Vehicle, OBDReading, SystemCheck, NetworkSystem, FluidLevel,
    PerformanceCheck, PaintFinish, TyreCondition, FlushGap, RubberComponent,
    GlassComponent, InteriorComponent, Documentation, LiveParameters
)

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone']



class VehicleForm(forms.ModelForm):


    class Meta:
        model = Vehicle
        fields = [ 'image', 'model',  'vin', 'fuel_type',
            'transmission', 'engine_cc', 'engine_type', 'bhp', 'airbags',
            'mileage_kmpl', 'ncap_rating', 'num_keys', 
            'inspected_by', 'health_score']

class OBDReadingForm(forms.ModelForm):
    class Meta:
        model = OBDReading
        fields = [
             'avg_city_running_kms', 'pre_delivery_odo_kms',
            'current_odo_kms', 'obd_running_kms', 'obd_tampering'
        ]

class SystemCheckForm(forms.ModelForm):
    class Meta:
        model = SystemCheck
        fields = [ 'system', 'status', 'number_of_issues']

class LiveParameterForm(forms.ModelForm):
    class Meta:
        model = LiveParameters
        fields = ['system', 'interence']

class NetworkSystemForm(forms.ModelForm):
    class Meta:
        model = NetworkSystem
        fields = [ 'area','status', 'remark']

class FluidLevelForm(forms.ModelForm):
    class Meta:
        model = FluidLevel
        fields = [ 'area', 'in_range', 'contamination', 'recommendation']

class PerformanceCheckForm(forms.ModelForm):
    class Meta:
        model = PerformanceCheck
        fields = [ 'system', 'status', 'recommendation']

class PaintFinishForm(forms.ModelForm):
    class Meta:
        model = PaintFinish
        fields = [ 'area', 'repainted', 'condition', 'action']
        repainted = forms.BooleanField(required=False)


class TyreConditionForm(forms.ModelForm):
    class Meta:
        model = TyreCondition
        fields = [ 'position', 'brand', 'condition', 'remaining_life_percent']

class FlushGapForm(forms.ModelForm):
    class Meta:
        model = FlushGap
        fields = [ 'area', 'operation', 'observation_gap', 'action']

class RubberComponentForm(forms.ModelForm):
    class Meta:
        model = RubberComponent
        fields = [ 'area', 'condition', 'recommendation']

class GlassComponentForm(forms.ModelForm):
    class Meta:
        model = GlassComponent
        fields = [ 'area', 'brand', 'condition', 'recommendation']

class InteriorComponentForm(forms.ModelForm):
    class Meta:
        model = InteriorComponent
        fields = [ 'category', 'area', 'condition', 'recommendation']

class DocumentationForm(forms.ModelForm):
    class Meta:
        model = Documentation
        fields = [ 'document', 'status', 'remark']