from django.contrib import admin
from .models import *

# --- Inline Models ---
class OBDReadingInline(admin.StackedInline):
    model = OBDReading
    extra = 0

class SystemCheckInline(admin.TabularInline):
    model = SystemCheck
    extra = 0

class NetworkSystemInline(admin.TabularInline):
    model = NetworkSystem
    extra = 0

class FluidLevelInline(admin.TabularInline):
    model = FluidLevel
    extra = 0

class LiveParametersInline(admin.TabularInline):
    model = LiveParameters
    extra = 0

class PerformanceCheckInline(admin.TabularInline):
    model = PerformanceCheck
    extra = 0

class PaintFinishInline(admin.TabularInline):
    model = PaintFinish
    extra = 0

class TyreConditionInline(admin.TabularInline):
    model = TyreCondition
    extra = 0

class FlushGapInline(admin.TabularInline):
    model = FlushGap
    extra = 0

class RubberComponentInline(admin.TabularInline):
    model = RubberComponent
    extra = 0

class GlassComponentInline(admin.TabularInline):
    model = GlassComponent
    extra = 0

class InteriorComponentInline(admin.TabularInline):
    model = InteriorComponent
    extra = 0

class DocumentationInline(admin.TabularInline):
    model = Documentation
    extra = 0

# --- Main ModelAdmins ---
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone']
    search_fields = ['name', 'email', 'phone']

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = [ 'model',  'vin', 'fuel_type', 'transmission', 'health_score']
    search_fields = ['vin', 'model', 'variant']
    list_filter = ['fuel_type', 'transmission', 'inspection_date']
    inlines = [
        OBDReadingInline,
        SystemCheckInline,
        NetworkSystemInline,
        FluidLevelInline,
        LiveParametersInline,
        PerformanceCheckInline,
        PaintFinishInline,
        TyreConditionInline,
        FlushGapInline,
        RubberComponentInline,
        GlassComponentInline,
        InteriorComponentInline,
        DocumentationInline,
    ]

@admin.register(VoltageInference)
class VoltageInferenceAdmin(admin.ModelAdmin):
    list_display = ['voltage', 'engine_state', 'interence', 'recommendation']
    search_fields = ['voltage', 'engine_state', 'interence']

# --- Simple Register Models ---
simple_models = [
    Status, VehicleFuelType, VehicleTransmission, VehicleEngineType,
    System, NetworkArea, FluidArea, FluidRange, Parameters, Performance,
    PaintArea, TyrePosition, FlushArea, Operations, RubberArea, GlassArea,
    InteriorArea, InteriorCategory, DocumentType
]

for model in simple_models:
    admin.site.register(model)


