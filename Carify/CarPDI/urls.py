from django.urls import path
from . import views

urlpatterns = [
    path('payment/<int:vehicle_id>/', views.create_payment, name='create_payment'),
    path('payment/verify/', views.payment_verify, name='payment_verify'),
    path('payment/success/<int:vehicle_id>/', views.payment_success, name='payment_success'),
    path('payment/failed/<int:vehicle_id>/', views.payment_failed, name='payment_failed'),
    path('send-payment/<int:vehicle_id>/', views.send_payment_link, name='send_payment_link'),
    path('payment/callback/', views.razorpay_callback, name='razorpay_callback'),


    path('customer/', views.customer_view, name='form_customer'),
    path('vehicle/', views.vehicle_view, name='form_vehicle'),
    path('obdreading/', views.obdreading_view, name='form_obdreading'),
    path('systemcheck/', views.systemcheck_view, name='form_systemcheck'),
    path('networksystem/', views.networksystem_view, name='form_networksystem'),
    path('liveparameters/', views.liveparameters_view, name='form_liveparameters'),
    path('performancecheck/', views.performancecheck_view, name='form_performancecheck'),
    path('fluidlevel/', views.fluidlevel_view, name='form_fluidlevel'),
    path('tyrecondition/', views.tyrecondition_view, name='form_tyrecondition'),
    path('paintfinish/', views.paintfinish_view, name='form_paintfinish'),
    path('flushgap/', views.flushgap_view, name='form_flushgap'),
    path('rubbercomponent/', views.rubbercomponent_view, name='form_rubbercomponent'),
    path('glasscomponent/', views.glasscomponent_view, name='form_glasscomponent'),
    path('interiorcomponent/', views.interiorcomponent_view, name='form_interiorcomponent'),
    path('form/documentation/', views.documentation_view, name='form_documentation'),

]
   