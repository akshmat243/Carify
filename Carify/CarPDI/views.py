# views/customer_view.py
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from .forms import *
from .models import *
from django.utils import timezone
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.html import escapejs
import json
import razorpay
from django.conf import settings

@csrf_exempt
def create_payment(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    if vehicle.payment_status == 'success':
        return redirect('payment_success', vehicle_id=vehicle.id)

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    amount_paise = int(vehicle.payment_amount * 100)
    payment = client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "payment_capture": '1'
    })

    vehicle.transaction_id = payment['id']
    vehicle.payment_status = 'pending'
    vehicle.save()

    return render(request, "payment/payment.html", {
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "order_id": payment['id'],
        "amount": amount_paise,
        "vehicle": vehicle
    })

@csrf_exempt
def payment_verify(request):
    if request.method == "POST":
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        try:
            order_id = request.POST.get('razorpay_order_id')
            payment_id = request.POST.get('razorpay_payment_id')
            signature = request.POST.get('razorpay_signature')
            vehicle_id = request.POST.get("vehicle_id")

            vehicle = get_object_or_404(Vehicle, id=vehicle_id)

            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }

            client.utility.verify_payment_signature(params_dict)

            vehicle.payment_status = 'success'
            vehicle.transaction_id = payment_id
            vehicle.save()

            return redirect('payment_success', vehicle_id=vehicle.id)

        except razorpay.errors.SignatureVerificationError:
            vehicle = get_object_or_404(Vehicle, id=request.POST.get("vehicle_id"))
            vehicle.payment_status = 'failed'
            vehicle.save()
            return redirect('payment_failed', vehicle_id=vehicle.id)

def payment_success(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    return render(request, 'payment/success.html', {'vehicle': vehicle})

def payment_failed(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    return render(request, 'payment/failed.html', {'vehicle': vehicle})

def send_payment_link(request, vehicle_id):
    vehicle = Vehicle.objects.get(id=vehicle_id)
    
    client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))

    amount_rupees = 500  # Replace with dynamic logic or field (₹500)
    amount_paise = amount_rupees * 100  # Razorpay uses paise

    payment_data = {
        "amount": amount_paise,
        "currency": "INR",
        "accept_partial": False,
        "description": f"Payment for Vehicle #{vehicle.id}",
        "customer": {
            "name": vehicle.customer.name,
            "contact": vehicle.customer.phone,
            "email": vehicle.customer.email
        },
        "notify": {
            "sms": True,
            "email": True
        },
        "reminder_enable": True,
        "callback_url": "http://localhost:8000/carify/payment/callback/",
        "callback_method": "get"
    }

    response = client.payment_link.create(payment_data)

    # Optional: Save the link ID and status to your model
    vehicle.payment_link_id = response['id']
    vehicle.payment_status = response['status']
    vehicle.save()

    return JsonResponse({
        "success": True,
        "payment_link": response['short_url'],
        "status": response['status'],
        "id": response['id']
    })

@csrf_exempt
def razorpay_callback(request):
    if request.method == "GET":
        payment_id = request.GET.get('razorpay_payment_id')
        link_id = request.GET.get('razorpay_payment_link_id')
        status = request.GET.get('razorpay_payment_link_status')

        if status == "paid":
            vehicle = Vehicle.objects.filter(razorpay_link_id=link_id).first()
            if vehicle:
                vehicle.payment_status = "paid"
                vehicle.razorpay_payment_id = payment_id
                vehicle.save()
                return render(request, "car/payment_success.html", {
                    "payment_id": payment_id,
                    "vehicle": vehicle
                })
            else:
                return HttpResponseBadRequest("Vehicle not found.")
        else:
            return render(request, "car/payment_failed.html")
    return HttpResponseBadRequest("Invalid request method.")

#--------------Form-------------
@csrf_exempt
def customer_view(request):
    
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()  
            request.session['customer_id'] = customer.id  
            return redirect('form_vehicle')  
    else:
        form = CustomerForm()

    # 🟡 Always return a response, even after POST fails
    return render(request, 'car/form.html', {
        'form': form,
        'current_form': 'customer'
    })


@csrf_exempt
def vehicle_view(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return JsonResponse({
            'success': False,
            'message': 'Customer ID not found in session.',
            'redirect': '/carify/form/customer/'
        }, status=400)

    customer = get_object_or_404(Customer, id=customer_id)
    instance = Vehicle.objects.filter(customer_id=customer_id).first()
    vehicle = None
    print("Vehicle:", vehicle)
    print("Instance:", instance)

    
    if request.method == 'POST':
        request.POST = request.POST.copy()  

        # TRANSMISSION
        custom_transmission = request.POST.get('custom_transmission')
        selected_transmission = request.POST.get('transmission')
        if custom_transmission and selected_transmission == '__custom__':
            trans_type, _ = VehicleTransmission.objects.get_or_create(
                name__iexact=custom_transmission,
                defaults={'name': custom_transmission}
            )
            request.POST['transmission'] = trans_type.id

        # ENGINE
        custom_engine = request.POST.get('custom_engine')
        selected_engine = request.POST.get('engine_type')
        if custom_engine and selected_engine == '__custom__':
            eng_type, _ = VehicleEngineType.objects.get_or_create(
                name__iexact=custom_engine,
                defaults={'name': custom_engine}
            )
            request.POST['engine_type'] = eng_type.id

        # FUEL
        custom_fuel = request.POST.get('custom_fuel')
        selected_fuel_id = request.POST.get('fuel_type')
        if custom_fuel and selected_fuel_id == '__custom__':
            fuel_type, _ = VehicleFuelType.objects.get_or_create(
                name__iexact=custom_fuel,
                defaults={'name': custom_fuel}
            )
            request.POST['fuel_type'] = fuel_type.id

        form = VehicleForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.customer = customer
            if not vehicle.inspection_date:
                vehicle.inspection_date = timezone.now().date()
            if not vehicle.inspected_by_id:
                vehicle.inspected_by = request.user
            vehicle.save()
            request.session['vehicle_id'] = vehicle.id
            return redirect ('form_obdreading')

    else:
        initial_date = instance.inspection_date if instance and instance.inspection_date else timezone.now().date()
        initial_data = {
            'customer': customer_id,
            'inspection_date': initial_date,
            'inspected_by': request.user.id,
        }
        form = VehicleForm(instance=instance, initial=initial_data)
        return render(request, 'car/form.html', {
            'form': form,
            'current_form': 'vehicle',
            'fuel_types': VehicleFuelType.objects.all(),
            'transmission_types': VehicleTransmission.objects.all(),
            'engine_types': VehicleEngineType.objects.all(),
            'customer': customer,
            'vehcile':vehicle,
        })



@csrf_exempt
def obdreading_view(request):
    vehicle_id = request.session.get('vehicle_id')
    if not vehicle_id:
        return JsonResponse({
            'success': False,
            'message': 'Vehicle ID not found in session.',
            'redirect': '/carify/form/vehicle/'
        }, status=400)

    instance = OBDReading.objects.filter(vehicle_id=vehicle_id).first()
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    if request.method == 'POST':
        form = OBDReadingForm(request.POST, instance=instance)
        if form.is_valid():
            obd = form.save(commit=False)
            obd.vehicle = vehicle
            obd.save()
            return redirect('form_systemcheck')  
        else:
            return JsonResponse({
                'success': False,
                'message': 'Validation failed.',
                'errors': form.errors
            }, status=400)
    
    form = OBDReadingForm(instance=instance)
    return render(request, 'car/form.html', {
        'form': form,
        'current_form': 'obdreading',
        'vehicle': vehicle
    })



@csrf_exempt
def systemcheck_view(request):
    vehicle_id = request.session.get('vehicle_id')
    if not vehicle_id:
        return JsonResponse({
            'success': False,
            'message': 'Vehicle ID not found in session.',
            'redirect': '/carify/form/vehicle/'
        }, status=400)

    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    if request.method == 'POST':
        systems_qs = System.objects.all()
        for system in systems_qs:
            status_key = f'status_{system.id}'
            custom_status_key = f'custom_status_{system.id}'
            issue_key = f'number_of_issues_{system.id}'

            status_id = request.POST.get(status_key)
            custom_status = request.POST.get(custom_status_key)
            number_of_issues = request.POST.get(issue_key)

            if not status_id and not custom_status:
                continue  # skip if no data

            # Handle custom status
            if status_id == '__custom__' and custom_status.strip():
                status_obj, _ = Status.objects.get_or_create(
                    name__iexact=custom_status.strip(),
                    defaults={'name': custom_status.strip()}
                )
            else:
                try:
                    status_obj = Status.objects.get(id=int(status_id))
                except (ValueError, Status.DoesNotExist):
                    continue  # skip invalid status

            SystemCheck.objects.create(
                vehicle=vehicle,
                system=system,
                status=status_obj,
                number_of_issues=int(number_of_issues or 0)
            )

        return redirect('form_networksystem')


    # Querysets for dropdowns (HTML usage)
    systems_qs = System.objects.all()
    statuses_qs = Status.objects.all()

    # JSON-safe data for JavaScript usage
    systems = list(System.objects.values('id', 'name'))
    statuses = list(Status.objects.values('id', 'name'))
    return render(request, 'car/form.html', {
    'current_form': 'systemcheck',
    'vehicle': vehicle,
    'systems': systems_qs,       
    'statuses': statuses_qs,
    'systems_json': json.dumps(systems),
    'statuses_json':json.dumps(statuses),
    })


@csrf_exempt
def networksystem_view(request):
    vehicle_id = request.session.get("vehicle_id")
    if not vehicle_id:
        return JsonResponse({'success': False, 'message': 'Vehicle ID not found in session'}, status=400)

    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    if request.method == "POST":
        statuses = request.POST.getlist('status')
        custom_statuses = request.POST.getlist('custom_status')
        remarks = request.POST.getlist('remark')

        areas_qs = list(NetworkArea.objects.all())  # Assumed order preserved

        if not (len(areas_qs) == len(statuses) == len(custom_statuses) == len(remarks)):
            return JsonResponse({'success': False, 'message': 'Mismatched row count'}, status=400)

        for i, area in enumerate(areas_qs):
            # Status
            status_id = statuses[i]
            if status_id == "__custom__" and custom_statuses[i].strip():
                status, _ = Status.objects.get_or_create(name=custom_statuses[i].strip())
            else:
                status = get_object_or_404(Status, id=status_id)

            remark = remarks[i]

            NetworkSystem.objects.create(
                vehicle=vehicle,
                area=area,
                status=status,
                remark=remark
            )

        return redirect('form_liveparameters')

    # GET request
    areas_qs = NetworkArea.objects.all()
    statuses_qs = Status.objects.all()
    return render(request, 'car/form.html', {
            'current_form': 'networksystem',
            'vehicle': vehicle,
            'areas': areas_qs,
            'statuses': Status.objects.all(),
            'areas_json': json.dumps(list(areas_qs.values('id', 'name'))),
            'statuses_json': json.dumps(list(Status.objects.values('id', 'name'))),
            'error': 'Something went wrong. Please ensure all fields are filled correctly.'
        })

@csrf_exempt
def liveparameters_view(request):
    vehicle_id = request.session.get("vehicle_id")
    if not vehicle_id:
        return JsonResponse({
            'success': False,
            'message': 'Vehicle ID not found in session.'
        }, status=400)

    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    if request.method == "POST":
        systems = request.POST.getlist('system')
        custom_systems = request.POST.getlist('custom_system')
        inferences = request.POST.getlist('inference')
        custom_inferences = request.POST.getlist('custom_inference')

        # Check for row length consistency
        if not (len(systems) == len(custom_systems) == len(inferences) == len(custom_inferences)):
            return render(request, 'car/form.html', {
                'current_form': 'liveparameters',
                'vehicle': vehicle,
                'parameters': Parameters.objects.all(),
                'inferences': VoltageInference.objects.all(),
                'parameters_json': json.dumps(list(Parameters.objects.values('id', 'name'))),
                'inferences_json': json.dumps(list(VoltageInference.objects.values('id', 'voltage'))),
                'error': 'Mismatched data rows. Please check and try again.'
            })

        for i in range(len(systems)):
            try:
                # SYSTEM
                if systems[i] == "__custom__" and custom_systems[i].strip():
                    system, _ = Parameters.objects.get_or_create(name=custom_systems[i].strip())
                else:
                    system = get_object_or_404(Parameters, id=systems[i])

                # INFERENCE
                if inferences[i] == "__custom__" and custom_inferences[i].strip():
                    inference, _ = VoltageInference.objects.get_or_create(
                        voltage=custom_inferences[i].strip(),  # Assuming `voltage` is used as name
                        defaults={'engine_state': '', 'interence': '', 'recommendation': ''}
                    )
                else:
                    inference = get_object_or_404(VoltageInference, id=inferences[i])

                LiveParameters.objects.create(
                    vehicle=vehicle,
                    system=system,
                    interence=inference
                )
            except Exception as e:
                return render(request, 'car/form.html', {
                    'current_form': 'liveparameters',
                    'vehicle': vehicle,
                    'parameters': Parameters.objects.all(),
                    'inferences': VoltageInference.objects.all(),
                    'parameters_json': json.dumps(list(Parameters.objects.values('id', 'name'))),
                    'inferences_json': json.dumps(list(VoltageInference.objects.values('id', 'voltage'))),
                    'error': f"Error in row {i+1}: {str(e)}"
                })

        return redirect('form_performancecheck')

    # GET: return form
    param_qs = list(Parameters.objects.values('id', 'name'))
    inf_qs = list(VoltageInference.objects.values('id', 'voltage'))

    return render(request, 'car/form.html', {
        'current_form': 'liveparameters',
        'vehicle': vehicle,
        'parameters': Parameters.objects.all(),
        'inferences': VoltageInference.objects.all(),
        'parameters_json': json.dumps(param_qs),
        'inferences_json': json.dumps(inf_qs),
    })

@csrf_exempt
def performancecheck_view(request):
    vehicle_id = request.session.get("vehicle_id")
    if not vehicle_id:
        return JsonResponse({'success': False, 'message': 'Vehicle ID not in session'}, status=400)

    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    performance_systems = list(Performance.objects.all())
    statuses = list(Status.objects.all())

    if request.method == "POST":
        status_list = request.POST.getlist("status")
        custom_status_list = request.POST.getlist("custom_status")
        recommendation_list = request.POST.getlist("recommendation")
        system_list = request.POST.getlist("system")  # From JS-added rows
        custom_system_list = request.POST.getlist("custom_system")

        # Merge static systems (from DB) + dynamic systems (from JS)
        all_systems = performance_systems + [None] * (len(system_list) - len(performance_systems))

        if not (len(status_list) == len(custom_status_list) == len(recommendation_list)):
            return render(request, "car/form.html", {
                'current_form': 'performancecheck',
                'vehicle': vehicle,
                'performance_systems': performance_systems,
                'statuses': statuses,
                'performance_json': json.dumps([{'id': s.id, 'name': s.name} for s in performance_systems]),
                'statuses_json': json.dumps([{'id': s.id, 'name': s.name} for s in statuses]),
                'error': "Mismatch in row data. Ensure all inputs are filled correctly."
            })

        for i in range(len(status_list)):
            try:
                # Handle system (static or dynamic)
                if i < len(performance_systems):
                    system = performance_systems[i]
                else:
                    sys_id = system_list[i - len(performance_systems)]
                    custom_name = custom_system_list[i - len(performance_systems)].strip()
                    if sys_id == "__custom__" and custom_name:
                        system, _ = Performance.objects.get_or_create(name=custom_name)
                    else:
                        system = get_object_or_404(Performance, id=sys_id)

                # Handle status
                status_id = status_list[i]
                if status_id == "__custom__" and custom_status_list[i].strip():
                    status, _ = Status.objects.get_or_create(name=custom_status_list[i].strip())
                else:
                    status = get_object_or_404(Status, id=status_id)

                # Save
                PerformanceCheck.objects.create(
                    vehicle=vehicle,
                    system=system,
                    status=status,
                    recommendation=recommendation_list[i].strip()
                )

            except Exception as e:
                return render(request, "car/form.html", {
                    'current_form': 'performancecheck',
                    'vehicle': vehicle,
                    'performance_systems': performance_systems,
                    'statuses': statuses,
                    'performance_json': json.dumps([{'id': s.id, 'name': s.name} for s in performance_systems]),
                    'statuses_json': json.dumps([{'id': s.id, 'name': s.name} for s in statuses]),
                    'error': f"Error at row {i+1}: {str(e)}"
                })

        return redirect('form_fluidlevel')

    # GET
    return render(request, "car/form.html", {
        'current_form': 'performancecheck',
        'vehicle': vehicle,
        'performance_systems': performance_systems,
        'statuses': statuses,
        'performance_json': json.dumps([{'id': s.id, 'name': s.name} for s in performance_systems]),
        'statuses_json': json.dumps([{'id': s.id, 'name': s.name} for s in statuses]),
    })

@csrf_exempt
def fluidlevel_view(request):
    vehicle_id = request.session.get('vehicle_id')
    if not vehicle_id:
        return JsonResponse({'success': False, 'message': 'Vehicle ID not found'}, status=400)

    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    fluid_areas = list(FluidArea.objects.all())
    fluid_ranges = list(FluidRange.objects.all())
    statuses = list(Status.objects.all())

    if request.method == 'POST':
        try:
            # POST data
            range_ids = request.POST.getlist('in_range')
            custom_ranges = request.POST.getlist('custom_range')
            contamination_ids = request.POST.getlist('contamination')
            custom_statuses = request.POST.getlist('custom_status')
            recommendations = request.POST.getlist('recommendation')
            area_ids = request.POST.getlist('area')  # From dynamic rows
            custom_areas = request.POST.getlist('custom_area')

            total_rows = len(recommendations)

            if not (len(range_ids) == len(custom_ranges) == len(contamination_ids) == len(custom_statuses) == total_rows):
                raise ValueError("Input row lengths mismatch.")

            for i in range(total_rows):
                # Area: from static loop or dynamic row
                if i < len(fluid_areas):
                    area = fluid_areas[i]
                else:
                    area_id = area_ids[i - len(fluid_areas)]
                    custom_area = custom_areas[i - len(fluid_areas)].strip()
                    if area_id == '__custom__' and custom_area:
                        area, _ = FluidArea.objects.get_or_create(name=custom_area)
                    else:
                        area = get_object_or_404(FluidArea, id=area_id)

                # Range
                range_id = range_ids[i]
                if range_id == '__custom__' and custom_ranges[i].strip():
                    in_range, _ = FluidRange.objects.get_or_create(name=custom_ranges[i].strip())
                else:
                    in_range = get_object_or_404(FluidRange, id=range_id)

                # Contamination
                status_id = contamination_ids[i]
                if status_id == '__custom__' and custom_statuses[i].strip():
                    contamination, _ = Status.objects.get_or_create(name=custom_statuses[i].strip())
                else:
                    contamination = get_object_or_404(Status, id=status_id)

                # Save
                FluidLevel.objects.create(
                    vehicle=vehicle,
                    area=area,
                    in_range=in_range,
                    contamination=contamination,
                    recommendation=recommendations[i].strip()
                )

            return redirect('form_tyrecondition')

        except Exception as e:
            return render(request, 'car/form.html', {
                'current_form': 'fluidlevel',
                'vehicle': vehicle,
                'fluid_areas': fluid_areas,
                'fluid_ranges': fluid_ranges,
                'statuses': statuses,
                'fluid_areas_json': json.dumps([{'id': a.id, 'name': a.name} for a in fluid_areas]),
                'fluid_ranges_json': json.dumps([{'id': r.id, 'name': r.name} for r in fluid_ranges]),
                'statuses_json': json.dumps([{'id': s.id, 'name': s.name} for s in statuses]),
                'error': f"⚠️ Error processing row {i + 1}: {str(e)}"
            })

    # GET request
    return render(request, 'car/form.html', {
        'current_form': 'fluidlevel',
        'vehicle': vehicle,
        'fluid_areas': fluid_areas,
        'fluid_ranges': fluid_ranges,
        'statuses': statuses,
        'fluid_areas_json': json.dumps([{'id': a.id, 'name': a.name} for a in fluid_areas]),
        'fluid_ranges_json': json.dumps([{'id': r.id, 'name': r.name} for r in fluid_ranges]),
        'statuses_json': json.dumps([{'id': s.id, 'name': s.name} for s in statuses]),
    })



@csrf_exempt
def tyrecondition_view(request):
    vehicle_id = request.session.get('vehicle_id')
    if not vehicle_id:
        return redirect('form_vehicle')

    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    if request.method == 'POST':
        positions = ['Front Left', 'Front Right', 'Rear Left', 'Rear Right', 'Spare']
        brands = request.POST.getlist('brand')
        conditions = request.POST.getlist('condition')
        dates = request.POST.getlist('manufacturing_date')
        lives = request.POST.getlist('remaining_life_percent')
        custom_conditions = request.POST.getlist('custom_condition')

        for i in range(len(positions)):
            # Get or create the TyrePosition (predefined)
            pos_obj, _ = TyrePosition.objects.get_or_create(name=positions[i])

            # Handle condition (may include custom)
            if conditions[i] == '__custom__' and custom_conditions[i].strip():
                cond_obj, _ = Status.objects.get_or_create(
                    name__iexact=custom_conditions[i].strip(),
                    defaults={'name': custom_conditions[i].strip()}
                )
            else:
                cond_obj = get_object_or_404(Status, id=int(conditions[i]))

            TyreCondition.objects.create(
                vehicle=vehicle,
                position=pos_obj,
                brand=brands[i],
                condition=cond_obj,
                remaining_life_percent=lives[i]
            )

        return redirect('form_paintfinish')

    statuses_qs = list(Status.objects.values('id', 'name'))
    return render(request, 'car/form.html', {
        'current_form': 'tyrecondition',
        'vehicle': vehicle,
        'statuses': Status.objects.all(),
        'statuses_json': escapejs(json.dumps(statuses_qs)),
    })
@csrf_exempt
def paintfinish_view(request):
    vehicle_id = request.session.get('vehicle_id')
    if not vehicle_id:
        return JsonResponse({
            'success': False,
            'message': 'Vehicle ID not found in session.',
            'redirect': '/carify/form/vehicle/'
        }, status=400)

    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    paint_areas_qs = PaintArea.objects.all()
    status_qs = Status.objects.all()

    if request.method == 'POST':
        try:
            areas = request.POST.getlist('area')
            custom_areas = request.POST.getlist('custom_area')
            conditions = request.POST.getlist('condition')
            custom_conditions = request.POST.getlist('custom_condition')
            actions = request.POST.getlist('action')
            repainted_flags = request.POST.getlist('repainted')  # hidden field to keep count

            total_rows = len(conditions)
            if not (len(conditions) == len(actions)):
                raise ValueError("Mismatch in form row lengths.")

            for i in range(total_rows):
                # Area Handling (for static rows, we take from DB order; for dynamic, from POST)
                if i < len(paint_areas_qs):
                    area_obj = paint_areas_qs[i]
                else:
                    area_id = areas[i - len(paint_areas_qs)]
                    custom_area = custom_areas[i - len(paint_areas_qs)].strip()
                    if area_id == '__custom__' and custom_area:
                        area_obj, _ = PaintArea.objects.get_or_create(name=custom_area)
                    else:
                        area_obj = get_object_or_404(PaintArea, id=area_id)

                # Condition Handling
                cond_id = conditions[i]
                custom_condition = custom_conditions[i].strip()
                if cond_id == '__custom__' and custom_condition:
                    condition_obj, _ = Status.objects.get_or_create(name=custom_condition)
                else:
                    condition_obj = get_object_or_404(Status, id=cond_id)

                # Repainted Checkbox
                repainted = request.POST.get(f'repainted_{i}', 'off') == 'on'

                # Action
                action = actions[i].strip() if i < len(actions) else 'NIL'

                # Save
                PaintFinish.objects.create(
                    vehicle=vehicle,
                    area=area_obj,
                    repainted=repainted,
                    condition=condition_obj,
                    action=action if action else 'NIL'
                )

            return redirect('form_flushgap')

        except Exception as e:
            return render(request, 'car/form.html', {
                'current_form': 'paintfinish',
                'vehicle': vehicle,
                'paint_areas': paint_areas_qs,
                'statuses': status_qs,
                'paint_areas_json': json.dumps(list(paint_areas_qs.values('id', 'name'))),
                'statuses_json': json.dumps(list(status_qs.values('id', 'name'))),
                'error': f"⚠️ Error: {str(e)}"
            })

    # GET
    return render(request, 'car/form.html', {
        'current_form': 'paintfinish',
        'vehicle': vehicle,
        'paint_areas': paint_areas_qs,
        'statuses': status_qs,
        'paint_areas_json': json.dumps(list(paint_areas_qs.values('id', 'name'))),
        'statuses_json': json.dumps(list(status_qs.values('id', 'name')))
    })

@csrf_exempt
def flushgap_view(request):
    vehicle_id = request.session.get('vehicle_id')
    if not vehicle_id:
        return redirect('form_vehicle')

    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    flush_areas_qs = FlushArea.objects.all()
    operations_qs = Operations.objects.all()

    if request.method == 'POST':
        try:
            areas = request.POST.getlist('area')
            custom_areas = request.POST.getlist('custom_area')
            operations = request.POST.getlist('operation')
            custom_ops = request.POST.getlist('custom_operation')
            observations = request.POST.getlist('observation')
            actions = request.POST.getlist('action')

            total = len(observations)
            if not (len(operations) == len(actions) == total):
                raise ValueError("Mismatch in form data rows.")

            for i in range(total):
                # Area - match static rows by index, dynamic by area input
                if i < len(flush_areas_qs):
                    area_obj = flush_areas_qs[i]
                else:
                    area_id = areas[i - len(flush_areas_qs)]
                    custom_area = custom_areas[i - len(flush_areas_qs)].strip()
                    if area_id == '__custom__' and custom_area:
                        area_obj, _ = FlushArea.objects.get_or_create(name=custom_area)
                    else:
                        area_obj = get_object_or_404(FlushArea, id=area_id)

                # Operation
                op_id = operations[i]
                custom_op = custom_ops[i].strip()
                if op_id == '__custom__' and custom_op:
                    op_obj, _ = Operations.objects.get_or_create(name=custom_op)
                else:
                    op_obj = get_object_or_404(Operations, id=op_id)

                # Observation (Yes/No)
                observation = observations[i] if i < len(observations) else 'No'

                # Action
                action = actions[i].strip() if i < len(actions) else 'NIL'

                # Save
                FlushGap.objects.create(
                    vehicle=vehicle,
                    area=area_obj,
                    operation=op_obj,
                    observation_gap=observation,
                    action=action if action else 'NIL'
                )

            return redirect('form_rubbercomponent')

        except Exception as e:
            return render(request, 'car/form.html', {
                'current_form': 'flushgap',
                'vehicle': vehicle,
                'flush_areas': flush_areas_qs,
                'operations': operations_qs,
                'flush_areas_json': json.dumps(list(flush_areas_qs.values('id', 'name'))),
                'operations_json': json.dumps(list(operations_qs.values('id', 'name'))),
                'error': f"⚠️ Error: {str(e)}"
            })

    # GET request
    return render(request, 'car/form.html', {
        'current_form': 'flushgap',
        'vehicle': vehicle,
        'flush_areas': flush_areas_qs,
        'operations': operations_qs,
        'flush_areas_json': json.dumps(list(flush_areas_qs.values('id', 'name'))),
        'operations_json': json.dumps(list(operations_qs.values('id', 'name')))
    })

# views.py
@csrf_exempt
def rubbercomponent_view(request):
    vehicle_id = request.session.get('vehicle_id')
    if not vehicle_id:
        return JsonResponse({
            'success': False,
            'message': 'Vehicle ID not found in session.',
            'redirect': '/carify/form/vehicle/'
        }, status=400)

    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    rubber_areas_qs = RubberArea.objects.all()
    statuses_qs = Status.objects.all()

    if request.method == 'POST':
        try:
            # From dynamically created rows (if any)
            areas = request.POST.getlist('area')
            custom_areas = request.POST.getlist('custom_area')
            
            # From form template
            conditions = request.POST.getlist('condition')
            custom_conditions = request.POST.getlist('custom_condition')
            recommendations = request.POST.getlist('action')  # matches input name in template

            total = len(conditions)
            if not (len(conditions) == len(recommendations)):
                raise ValueError("Mismatch in form input rows")

            for i in range(total):
                # Handle area (static or dynamic)
                if i < len(rubber_areas_qs):
                    area_obj = rubber_areas_qs[i]
                else:
                    area_id = areas[i - len(rubber_areas_qs)]
                    custom_area = custom_areas[i - len(rubber_areas_qs)].strip()
                    if area_id == '__custom__' and custom_area:
                        area_obj, _ = RubberArea.objects.get_or_create(name=custom_area)
                    else:
                        area_obj = get_object_or_404(RubberArea, id=area_id)

                # Handle condition (standard or custom)
                condition_id = conditions[i]
                custom_cond = custom_conditions[i].strip() if i < len(custom_conditions) else ''
                if condition_id == '__custom__' and custom_cond:
                    condition_obj, _ = Status.objects.get_or_create(name=custom_cond)
                else:
                    condition_obj = get_object_or_404(Status, id=condition_id)

                # Recommendation
                rec = recommendations[i].strip() if i < len(recommendations) else 'NIL'

                # Save
                RubberComponent.objects.create(
                    vehicle=vehicle,
                    area=area_obj,
                    condition=condition_obj,
                    recommendation=rec
                )

            return redirect('form_glasscomponent')

        except Exception as e:
            return render(request, 'car/form.html', {
                'current_form': 'rubbercomponent',
                'vehicle': vehicle,
                'rubber_areas': rubber_areas_qs,
                'statuses': statuses_qs,
                'rubber_areas_json': json.dumps(list(rubber_areas_qs.values('id', 'name'))),
                'statuses_json': json.dumps(list(statuses_qs.values('id', 'name'))),
                'error': f"⚠️ Error: {str(e)}"
            })

    # GET request
    return render(request, 'car/form.html', {
        'current_form': 'rubbercomponent',
        'vehicle': vehicle,
        'rubber_areas': rubber_areas_qs,
        'statuses': statuses_qs,
        'rubber_areas_json': json.dumps(list(rubber_areas_qs.values('id', 'name'))),
        'statuses_json': json.dumps(list(statuses_qs.values('id', 'name')))
    })

@csrf_exempt
def glasscomponent_view(request):
    vehicle_id = request.session.get('vehicle_id')
    if not vehicle_id:
        return JsonResponse({
            'success': False,
            'message': 'Vehicle ID not found in session.',
            'redirect': '/carify/form/vehicle/'
        }, status=400)

    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    glass_areas_qs = GlassArea.objects.all()
    statuses_qs = Status.objects.all()

    if request.method == 'POST':
        try:
            areas = request.POST.getlist('area')
            custom_areas = request.POST.getlist('custom_area')
            brands = request.POST.getlist('brand')
            conditions = request.POST.getlist('condition')
            custom_conditions = request.POST.getlist('custom_condition')
            recommendations = request.POST.getlist('action')  # 'action' used as name in input

            total = len(brands)

            if not (len(brands) == len(conditions) == len(recommendations)):
                raise ValueError("Mismatch in number of rows submitted")

            for i in range(total):
                # Handle Area (static or dynamic)
                if i < len(glass_areas_qs):
                    area_obj = glass_areas_qs[i]
                else:
                    area_id = areas[i - len(glass_areas_qs)]
                    custom_area = custom_areas[i - len(glass_areas_qs)].strip()
                    if area_id == '__custom__' and custom_area:
                        area_obj, _ = GlassArea.objects.get_or_create(name=custom_area)
                    else:
                        area_obj = get_object_or_404(GlassArea, id=area_id)

                # Handle Condition
                condition_id = conditions[i]
                custom_cond = custom_conditions[i].strip()
                if condition_id == '__custom__' and custom_cond:
                    condition_obj, _ = Status.objects.get_or_create(name=custom_cond)
                else:
                    condition_obj = get_object_or_404(Status, id=condition_id)

                # Create GlassComponent record
                GlassComponent.objects.create(
                    vehicle=vehicle,
                    area=area_obj,
                    brand=brands[i].strip(),
                    condition=condition_obj,
                    recommendation=recommendations[i].strip()
                )

            return redirect('form_interiorcomponent')

        except Exception as e:
            return render(request, 'car/form.html', {
                'current_form': 'glasscomponent',
                'vehicle': vehicle,
                'glass_areas': glass_areas_qs,
                'statuses': statuses_qs,
                'glass_areas_json': json.dumps(list(glass_areas_qs.values('id', 'name'))),
                'statuses_json': json.dumps(list(statuses_qs.values('id', 'name'))),
                'error': f"⚠️ Error: {str(e)}"
            })

    # GET Request
    return render(request, 'car/form.html', {
        'current_form': 'glasscomponent',
        'vehicle': vehicle,
        'glass_areas': glass_areas_qs,
        'statuses': statuses_qs,
        'glass_areas_json': json.dumps(list(glass_areas_qs.values('id', 'name'))),
        'statuses_json': json.dumps(list(statuses_qs.values('id', 'name')))
    })

@csrf_exempt
def interiorcomponent_view(request):
    vehicle_id = request.session.get('vehicle_id')
    if not vehicle_id:
        return redirect('form_vehicle')

    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    if request.method == 'POST':
        categories = request.POST.getlist('category')
        custom_categories = request.POST.getlist('custom_category')
        areas = request.POST.getlist('area')
        custom_areas = request.POST.getlist('custom_area')
        conditions = request.POST.getlist('condition')
        custom_conditions = request.POST.getlist('custom_condition')
        recommendations = request.POST.getlist('recommendation')

        for i in range(len(categories)):
            # Category
            if categories[i] == '__custom__' and custom_categories[i].strip():
                category_obj, _ = InteriorCategory.objects.get_or_create(
                    name__iexact=custom_categories[i].strip(),
                    defaults={'name': custom_categories[i].strip()}
                )
            else:
                category_obj = get_object_or_404(InteriorCategory, id=int(categories[i]))

            # Area
            if areas[i] == '__custom__' and custom_areas[i].strip():
                area_obj, _ = InteriorArea.objects.get_or_create(
                    name__iexact=custom_areas[i].strip(),
                    defaults={'name': custom_areas[i].strip()}
                )
            else:
                area_obj = get_object_or_404(InteriorArea, id=int(areas[i]))

            # Condition
            if conditions[i] == '__custom__' and custom_conditions[i].strip():
                condition_obj, _ = Status.objects.get_or_create(
                    name__iexact=custom_conditions[i].strip(),
                    defaults={'name': custom_conditions[i].strip()}
                )
            else:
                condition_obj = get_object_or_404(Status, id=int(conditions[i]))

            # Recommendation
            recommendation = recommendations[i].strip() if i < len(recommendations) else 'NIL'

            # Save
            InteriorComponent.objects.create(
                vehicle=vehicle,
                category=category_obj,
                area=area_obj,
                condition=condition_obj,
                recommendation=recommendation
            )

        return redirect('form_documentation') 
    categories = InteriorCategory.objects.all()
    areas = InteriorArea.objects.all()
    statuses = Status.objects.all()

    return render(request, 'car/form.html', {
        'current_form': 'interiorcomponent',
        'vehicle': vehicle,
        'categories': categories,
        'areas': areas,
        'statuses': statuses,
        'categories_json': json.dumps(list(categories.values('id', 'name'))),
        'areas_json': json.dumps(list(areas.values('id', 'name'))),
        'statuses_json': json.dumps(list(statuses.values('id', 'name')))
    })

@csrf_exempt
def documentation_view(request):
    vehicle_id = request.session.get('vehicle_id')
    if not vehicle_id:
        return redirect('form_vehicle')

    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    document_types = list(DocumentType.objects.all())
    statuses = list(Status.objects.all())

    if request.method == 'POST':
        for i, doc in enumerate(document_types):
            doc_id = request.POST.get(f'document_{i}')
            status_val = request.POST.get(f'status_{i}')
            custom_status_val = request.POST.get(f'custom_status_{i}', '').strip()
            remark = request.POST.get(f'remark_{i}', '')

            # Determine status object
            if status_val == '__custom__' and custom_status_val:
                status_obj, _ = Status.objects.get_or_create(
                    name__iexact=custom_status_val,
                    defaults={'name': custom_status_val}
                )
            else:
                status_obj = get_object_or_404(Status, id=int(status_val))

            Documentation.objects.create(
                vehicle=vehicle,
                document=doc,
                status=status_obj,
                remark=remark
            )

        # ✅ Redirect after successful POST
        return redirect('admin_dashboard')  # or 'admin_dashboard' if you want to go back

    return render(request, 'car/form.html', {
        'current_form': 'documentation',
        'vehicle': vehicle,
        'document_types': document_types,
        'statuses': statuses,
        'document_types_json': json.dumps(list(DocumentType.objects.values('id', 'name'))),
        'statuses_json': json.dumps(list(Status.objects.values('id', 'name')))
    })
