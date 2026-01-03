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


]