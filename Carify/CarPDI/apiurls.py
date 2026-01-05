from django.urls import path
from .apiviews import *

urlpatterns = [
    
    path('payment/create/<int:vehicle_id>/', CreatePaymentAPI.as_view(), name='api-create-payment'),

    path('payment/verify/', VerifyPaymentAPI.as_view(), name='api-payment-verify'),

    path('payment/status/<int:vehicle_id>/', GetPaymentStatusAPI.as_view(), name='api-payment-status'),

    path('payment/send-link/<int:vehicle_id>/', SendPaymentLinkAPI.as_view(), name='api-send-payment-link'),

    path('payment/callback/', RazorpayCallbackAPI.as_view(), name='api-razorpay-callback'),
    path('customer/create/', CreateCustomerAPI.as_view(), name='api-create-customer'),
    path('vehicle/create/', CreateVehicleAPI.as_view(), name='api-create-vehicle'),
    path('obd/create/', CreateOBDReadingAPI.as_view(), name='api-create-obd'),
    path('system-check/create/', CreateSystemCheckAPI.as_view(), name='api-create-system-check'),
    path('network-system/create/', CreateNetworkSystemAPI.as_view(), name='api-create-network-system'),
    path('live-parameters/create/', LiveParametersAPI.as_view(), name='api-create-live-parameters'),
    path('performance-check/', PerformanceCheckAPI.as_view(), name='api-performance-check'),
    path('fluid-level/', FluidLevelAPI.as_view(), name='api-fluid-level'),
    path('tyre-condition/', TyreConditionAPI.as_view(), name='api-tyre-condition'),
    path('paint-finish/', PaintFinishAPI.as_view(), name='api-paint-finish'),
    path('flush-gap/', FlushGapAPI.as_view(), name='api-flush-gap'),
    path('rubber-component/', RubberComponentAPI.as_view(), name='api-rubber-component'),
    path('glass-component/', GlassComponentAPI.as_view(), name='api-glass-component'),
    path('interior-component/', InteriorComponentAPI.as_view(), name='api-interior-component'),
    path('documentation/', DocumentationAPI.as_view(), name='api-documentation'),


]