import razorpay
import uuid
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import *
from .serializers import *
from .permissions import IsStaffOrManager
from User.models import UserRole
from django.db import transaction
from django.utils import timezone


# CREATE PAYMENT API 
class CreatePaymentAPI(APIView):
    """
    Initiates a payment order for a specific vehicle.
    Security: Staff can pay for anyone. Customers can ONLY pay for their own vehicle.
    Generates a valid Razorpay Order ID (Live Mode) or a simulated Order ID (Mock Mode).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, vehicle_id):
        
        vehicle = get_object_or_404(Vehicle, id=vehicle_id)

        # SECURITY CHECK: Ownership & Role Validation
        # 1. Check if user is Staff, Superuser, or has specific Admin roles
        is_staff_or_admin = (
            request.user.is_staff or 
            request.user.is_superuser or 
            UserRole.objects.filter(user=request.user, role__name__in=['Admin', 'Manager', 'Staff']).exists()
        )

        # 2. Check if the logged-in user is the owner of the vehicle
        # Assuming 'customer' field in Vehicle model links to the User
        is_owner = (vehicle.customer == request.user)

        # 3. If user is NEITHER Staff NOR Owner -> Block Access
        if not is_staff_or_admin and not is_owner:
             return Response({
                "status": "error",
                "message": "Permission Denied: You can only make payments for your own vehicle."
            }, status=status.HTTP_403_FORBIDDEN)
        # ---------------------------------------------------------------

        if vehicle.payment_status == 'success':
            return Response({
                "status": "info",
                "message": "Payment already completed for this vehicle.",
                "data": PaymentOrderSerializer(vehicle).data
            }, status=status.HTTP_200_OK)

        amount_paise = int(vehicle.payment_amount * 100) # Dynamic Amount

        # --- MODE 1: DUMMY / MOCK MODE ---
        if not getattr(settings, 'IS_RAZORPAY_LIVE', False):
            # Generate Fake Order ID
            fake_order_id = f"order_mock_{uuid.uuid4().hex[:10]}"
            
            # Update DB 
            vehicle.transaction_id = fake_order_id
            vehicle.payment_status = 'pending' 
            vehicle.save()

            return Response({
                "status": "success",
                "message": "Order Created (MOCK MODE)",
                "data": PaymentOrderSerializer(vehicle).data
            }, status=status.HTTP_201_CREATED)

        # --- MODE 2: LIVE MODE ---
        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            
            payment_data = {
                "amount": amount_paise,
                "currency": "INR",
                "payment_capture": '1' # Auto capture
            }
            
            # Real Razorpay Call
            order = client.order.create(data=payment_data)

            # DB Update
            vehicle.transaction_id = order['id']
            vehicle.payment_status = 'pending'
            vehicle.save()

            return Response({
                "status": "success",
                "message": "Razorpay Order Created Successfully",
                "data": PaymentOrderSerializer(vehicle).data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "status": "error",
                "message": "Razorpay Gateway Error",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VerifyPaymentAPI(APIView):
    """
    Verifies the payment signature returned by the payment gateway.
    Security: Only Staff or the Vehicle Owner (matched via Email) can verify.
    Validates transaction integrity and updates status.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PaymentVerifySerializer(data=request.data)
        
        if serializer.is_valid():
            vehicle_id = serializer.validated_data['vehicle_id']
            order_id = serializer.validated_data['razorpay_order_id']
            payment_id = serializer.validated_data['razorpay_payment_id']
            signature = serializer.validated_data['razorpay_signature']

            vehicle = get_object_or_404(Vehicle, id=vehicle_id)

            # SECURITY CHECK: Ownership (Email Matching) & Role Validation
            
            # 1. Check if the user is Staff or Superuser
            is_staff_or_admin = (
                request.user.is_staff or 
                request.user.is_superuser or 
                # Check UserRole model if it exists (remove this line if UserRole is not imported)
                UserRole.objects.filter(user=request.user, role__name__in=['Admin', 'Manager', 'Staff']).exists()
            )

            # 2. Check if the logged-in User's email matches the Vehicle Customer's email
            try:
                # We access the 'email' field inside the linked 'customer' object
                customer_email = vehicle.customer.email 
                user_email = request.user.email
                
                # Check if emails match (and ensure they are not empty)
                is_owner = (customer_email == user_email) and (user_email is not None)
            except AttributeError:
                # If vehicle.customer is None or doesn't have an email field
                is_owner = False

            # 3. Final Decision
            if not is_staff_or_admin and not is_owner:
                 return Response({
                    "status": "error",
                    "message": "Permission Denied: Your login email does not match the vehicle owner's email."
                }, status=status.HTTP_403_FORBIDDEN)

            # Security Check: Ensure Order ID matches what we saved earlier
            if vehicle.transaction_id != order_id:
                return Response({
                    "status": "error",
                    "message": "Order ID mismatch! Possible fraud attempt."
                }, status=status.HTTP_400_BAD_REQUEST)

            # --- MODE 1: MOCK / DUMMY MODE ---
            if not getattr(settings, 'IS_RAZORPAY_LIVE', False):
                
                # Force Fail Logic for Testing
                if payment_id == "PAYMENT_FAILED":
                    vehicle.payment_status = 'failed'
                    vehicle.save()
                    return Response({
                        "status": "failed",
                        "message": "Payment Verification Failed (Simulated).",
                        "data": {"vehicle_id": vehicle.id, "new_status": "failed"}
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Default Success Logic
                vehicle.payment_status = 'success'
                vehicle.transaction_id = payment_id 
                vehicle.save()

                return Response({
                    "status": "success",
                    "message": "Payment Verified Successfully (MOCK MODE)",
                    "data": {
                        "vehicle_id": vehicle.id,
                        "new_status": vehicle.payment_status
                    }
                }, status=status.HTTP_200_OK)

            # --- MODE 2: LIVE MODE (Real Razorpay Check) ---
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            
            try:
                # Razorpay Verification
                params_dict = {
                    'razorpay_order_id': order_id,
                    'razorpay_payment_id': payment_id,
                    'razorpay_signature': signature
                }
                
                client.utility.verify_payment_signature(params_dict)

                # If successful
                vehicle.payment_status = 'success'
                vehicle.transaction_id = payment_id 
                vehicle.save()

                return Response({
                    "status": "success",
                    "message": "Payment Verified Successfully",
                }, status=status.HTTP_200_OK)

            except razorpay.errors.SignatureVerificationError:
                # If signature invalid
                vehicle.payment_status = 'failed'
                vehicle.save()
                
                return Response({
                    "status": "failed",
                    "message": "Payment Verification Failed. Invalid Signature."
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class GetPaymentStatusAPI(APIView):
    """
    Retrieves the real-time payment status of a vehicle.
    Security: Customers can only see THEIR OWN vehicle (matched via Email). Staff can see ALL.
    Used by the frontend client to determine whether to display the 
    'Payment Success' or 'Payment Failed' screen.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, vehicle_id):
        # 1. Vehicle dhoondo
        vehicle = get_object_or_404(Vehicle, id=vehicle_id)

        # SECURITY CHECK: Ownership (Email Matching) & Role Validation
        
        # 1. Check if user is Staff, Superuser, or Admin/Manager
        is_staff_or_admin = (
            request.user.is_staff or 
            request.user.is_superuser or 
            # Remove the line below if UserRole is not imported or needed
            UserRole.objects.filter(user=request.user, role__name__in=['Admin', 'Manager', 'Staff']).exists()
        )

        # 2. Check if the logged-in User's email matches the Vehicle Customer's email
        try:
            customer_email = vehicle.customer.email
            user_email = request.user.email
            
            # Match emails (Make sure both are not None/Empty)
            is_owner = (customer_email == user_email) and (user_email is not None)
        except AttributeError:
            # Agar customer set nahi hai ya email missing hai
            is_owner = False

        # 3. Final Decision: Agar na Staff hai na Owner -> BLOCK KARO
        if not is_staff_or_admin and not is_owner:
            return Response({
                "status": "error",
                "message": "Permission Denied: You are not authorized to view this vehicle's status."
            }, status=status.HTTP_403_FORBIDDEN)
        
        # 2. Serializer se data convert karo
        serializer = PaymentStatusSerializer(vehicle)

        # 3. Response Return karo
        response_data = {
            "status": "success", 
            "payment_current_status": vehicle.payment_status, # Frontend ispar depend karega (success/failed)
            "data": serializer.data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)

class SendPaymentLinkAPI(APIView):
    """
    Generates a Razorpay Payment Link and sends it to the customer via SMS/Email.
    Supports Mock Mode for testing without real transaction costs.
    """
    permission_classes = [IsAuthenticated , IsStaffOrManager]

    def post(self, request, vehicle_id):
        # 1. Fetch Vehicle
        vehicle = get_object_or_404(Vehicle, id=vehicle_id)

        # 2. Validation: Check if customer details exist (Required for Payment Links)
        # Assuming 'customer' is a ForeignKey on the Vehicle model
        if not getattr(vehicle, 'customer', None):
            return Response({
                "status": "error",
                "message": "Customer details are missing for this vehicle. Cannot send link."
            }, status=status.HTTP_400_BAD_REQUEST)

        customer = vehicle.customer
        amount_paise = int(vehicle.payment_amount * 100) # Dynamic Amount

        
        # MODE 1: MOCK / DEVELOPMENT MODE
        if not getattr(settings, 'IS_RAZORPAY_LIVE', False):
            # Generate fake details
            fake_link_id = f"plink_mock_{uuid.uuid4().hex[:10]}"
            fake_short_url = f"https://mock-payment.com/{fake_link_id}"

            # Update DB
            vehicle.payment_link_id = fake_link_id
            vehicle.payment_status = 'created' # Razorpay status for created links
            vehicle.save()

            return Response({
                "status": "success",
                "message": "Payment Link Generated (MOCK MODE)",
                "data": PaymentLinkResponseSerializer(vehicle, context={'short_url': fake_short_url}).data
            }, status=status.HTTP_201_CREATED)

        # MODE 2: LIVE / PRODUCTION MODE
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        try:
            payment_data = {
                "amount": amount_paise,
                "currency": "INR",
                "accept_partial": False,
                "description": f"Payment for Vehicle #{vehicle.id} - {vehicle.model}",
                "customer": {
                    "name": customer.name,
                    "contact": customer.phone, # Ensure this field exists in Customer model
                    "email": customer.email    # Ensure this field exists in Customer model
                },
                "notify": {
                    "sms": True,
                    "email": True
                },
                "reminder_enable": True,
                # Ideally, this callback should be your frontend success page or backend verify API
                "callback_url": "http://localhost:8000/api/pdi/payment/callback/", 
                "callback_method": "get"
            }

            # Call Razorpay API
            response = client.payment_link.create(payment_data)

            # Update DB with real data
            vehicle.payment_link_id = response['id']
            vehicle.payment_status = response['status']
            vehicle.save()

            return Response({
                "status": "success",
                "message": "Payment Link Sent Successfully",
                "data": PaymentLinkResponseSerializer(vehicle, context={'short_url': response['short_url']}).data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "status": "error",
                "message": "Failed to generate payment link.",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class RazorpayCallbackAPI(APIView):
    """
    Handles the callback from Razorpay after a Payment Link transaction.
    Security: STRICT. Validates ownership via Email Matching or Staff role.
    Verifies payment status directly with Razorpay (Live Mode) to prevent URL tampering.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 1. Get Params from URL
        payment_id = request.GET.get('razorpay_payment_id')
        link_id = request.GET.get('razorpay_payment_link_id')
        link_status = request.GET.get('razorpay_payment_link_status')

        # Basic Validation
        if not link_id:
            return Response({
                "status": "error",
                "message": "Missing payment link ID."
            }, status=status.HTTP_400_BAD_REQUEST)

        # 2. Find Vehicle by Link ID
        # Note: Ensure your model field name matches (previous code used 'payment_link_id')
        vehicle = Vehicle.objects.filter(payment_link_id=link_id).first()

        if not vehicle:
            return Response({
                "status": "error",
                "message": "No vehicle found associated with this payment link."
            }, status=status.HTTP_404_NOT_FOUND)

        
        # SECURITY CHECK: Ownership (Email Matching) & Role Validation
        is_staff_or_admin = (
            request.user.is_staff or 
            request.user.is_superuser or 
            UserRole.objects.filter(user=request.user, role__name__in=['Admin', 'Manager', 'Staff']).exists()
        )

        try:
            customer_email = vehicle.customer.email
            user_email = request.user.email
            is_owner = (customer_email == user_email) and (user_email is not None)
        except AttributeError:
            is_owner = False

        if not is_staff_or_admin and not is_owner:
             return Response({
                "status": "error",
                "message": "Permission Denied: You are not authorized to process this payment callback."
            }, status=status.HTTP_403_FORBIDDEN)

        # --- MODE 1: MOCK / DUMMY MODE ---
        if not getattr(settings, 'IS_RAZORPAY_LIVE', False):
            # In Mock mode, we trust the URL param 'status' for testing
            if link_status == "paid":
                vehicle.payment_status = "success" # Standardize status to 'success'
                vehicle.transaction_id = payment_id or f"pay_mock_{uuid.uuid4().hex[:10]}"
                vehicle.save()
                
                return Response({
                    "status": "success",
                    "message": "Payment Confirmed (MOCK MODE)",
                    "data": {
                        "vehicle_id": vehicle.id,
                        "payment_status": "success"
                    }
                }, status=status.HTTP_200_OK)
            else:
                vehicle.payment_status = "failed"
                vehicle.save()
                return Response({
                    "status": "failed",
                    "message": "Payment Failed (MOCK MODE)"
                }, status=status.HTTP_400_BAD_REQUEST)

        # --- MODE 2: LIVE MODE (Secure Verification) ---
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        try:
            # SECURITY: Don't trust 'link_status' from URL. Fetch actual status from Razorpay.
            fetched_link = client.payment_link.fetch(link_id)
            
            real_status = fetched_link.get('status') # paid, expired, cancelled
            
            if real_status == "paid":
                # Get the latest payment ID associated with this link
                # Razorpay sends a list of payments for a link, we take the last one
                payments = fetched_link.get('payments', [])
                real_payment_id = payments[-1]['payment_id'] if payments else payment_id

                vehicle.payment_status = "success"
                vehicle.transaction_id = real_payment_id
                vehicle.save()

                return Response({
                    "status": "success",
                    "message": "Payment Verified & Updated Successfully",
                    "data": {
                        "vehicle_id": vehicle.id,
                        "payment_status": "success",
                        "transaction_id": real_payment_id
                    }
                }, status=status.HTTP_200_OK)
            
            else:
                vehicle.payment_status = "failed"
                vehicle.save()
                return Response({
                    "status": "failed",
                    "message": f"Payment not completed. Current status: {real_status}",
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "status": "error",
                "message": "Error verifying payment with Razorpay.",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class CreateCustomerAPI(APIView):
    """
    Step 1 of PDI Process: Create a new Customer profile.
    Security: RESTRICTED. Only Staff/Managers can add new customers.
    Returns: Customer ID (to be used in the next step: Vehicle Creation).
    """
    permission_classes = [IsAuthenticated, IsStaffOrManager]

    def post(self, request):
        serializer = CustomerSerializer(data=request.data)
        
        if serializer.is_valid():
            customer = serializer.save()
            
            return Response({
                "status": "success",
                "message": "Customer Created Successfully. Proceed to add Vehicle.",
                "data": serializer.data 
                # Frontend needs 'data.id' for the next step
            }, status=status.HTTP_201_CREATED)
            
        return Response({
            "status": "error",
            "message": "Invalid customer data.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    # CarPDI/api_views.py

class CreateVehicleAPI(APIView):
    """
    Step 2 of PDI Process: Create or Update Vehicle details.
    Handles Custom Foreign Keys (Engine, Fuel, Transmission) dynamically.
    Security: Staff/Manager only.
    """
    permission_classes = [IsAuthenticated, IsStaffOrManager]

    def _handle_custom_field(self, model, selected_value, custom_text):
        """
        Helper method: Smartly handles IDs, Names, and Custom Creations.
        """
        # Case 1: Agar user ne Custom select kiya
        if str(selected_value) == '__custom__' and custom_text:
            obj, created = model.objects.get_or_create(
                name__iexact=custom_text,
                defaults={'name': custom_text}
            )
            return obj.id
            
        # Case 2: Agar user ne already ID bheji hai (e.g., "1")
        if str(selected_value).isdigit():
            return int(selected_value)

        # Case 3: Agar user ne Naam bheja hai (e.g., "manual", "diesel")
        # Toh hum DB me dhoondhenge ki ye naam exist karta hai ya nahi
        if selected_value:
            obj = model.objects.filter(name__iexact=str(selected_value)).first()
            if obj:
                return obj.id
        
        # Agar kuch samajh nahi aaya to waisa hi bhej do (Serializer error dega)
        return selected_value

    def post(self, request):
        # 1. Data Dictionary me convert karo
        try:
            data = request.data.dict()
        except AttributeError:
            data = request.data.copy()
        
        # 2. Customer ID Check
        customer_id = data.get('customer')
        if not customer_id:
             return Response({
                "status": "error",
                "message": "Customer ID is required."
            }, status=status.HTTP_400_BAD_REQUEST)

        customer = get_object_or_404(Customer, id=customer_id)

        # 3. Handle Foreign Keys (Ab ye Naam se bhi ID dhoondh lega)
        
        # Transmission
        data['transmission'] = self._handle_custom_field(
            VehicleTransmission, 
            data.get('transmission'), 
            data.get('custom_transmission')
        )

        # Engine
        data['engine_type'] = self._handle_custom_field(
            VehicleEngineType, 
            data.get('engine_type'), 
            data.get('custom_engine')
        )

        # Fuel
        data['fuel_type'] = self._handle_custom_field(
            VehicleFuelType, 
            data.get('fuel_type'), 
            data.get('custom_fuel')
        )

        # 4. Create or Update Logic
        instance = Vehicle.objects.filter(customer=customer).first()
        
        if instance:
            serializer = VehicleSerializer(instance, data=data, partial=True)
            message = "Vehicle Details Updated Successfully."
        else:
            serializer = VehicleSerializer(data=data)
            message = "Vehicle Created Successfully."

        # 5. Save
        if serializer.is_valid():
            vehicle = serializer.save(
                customer=customer,
                inspected_by=request.user,
                inspection_date=instance.inspection_date if (instance and instance.inspection_date) else timezone.now().date()
            )

            return Response({
                "status": "success",
                "message": message,
                "data": serializer.data 
            }, status=status.HTTP_201_CREATED)

        return Response({
            "status": "error",
            "message": "Invalid vehicle data.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    

class CreateOBDReadingAPI(APIView):
    """
    Step 3 of PDI Process: Record OBD Readings.
    Create or Update OBD data for a specific vehicle.
    Security: Staff/Manager only.
    """
    permission_classes = [IsAuthenticated, IsStaffOrManager]

    def post(self, request):
        data = request.data
        
        # 1. Vehicle ID Validate karo
        vehicle_id = data.get('vehicle')
        if not vehicle_id:
             return Response({
                "status": "error",
                "message": "Vehicle ID is required."
            }, status=status.HTTP_400_BAD_REQUEST)

        vehicle = get_object_or_404(Vehicle, id=vehicle_id)

        # 2. Check if OBD Data already exists for this vehicle (Update Logic)
        instance = OBDReading.objects.filter(vehicle=vehicle).first()
        
        if instance:
            serializer = OBDReadingSerializer(instance, data=data, partial=True)
            message = "OBD Readings Updated Successfully."
        else:
            serializer = OBDReadingSerializer(data=data)
            message = "OBD Readings Recorded Successfully."

        # 3. Validation & Save
        if serializer.is_valid():
            serializer.save(vehicle=vehicle) # Link to Vehicle

            return Response({
                "status": "success",
                "message": message,
                "data": serializer.data 
                # Frontend is now ready for Step 4: System Check
            }, status=status.HTTP_201_CREATED)

        return Response({
            "status": "error",
            "message": "Invalid OBD data.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
# CarPDI/api_views.py

class CreateSystemCheckAPI(APIView):
    """
    Step 4 of PDI Process: Record System Checks (Bulk Operation).
    Receives a list of checks for different systems.
    Security: Staff/Manager only.
    """
    permission_classes = [IsAuthenticated, IsStaffOrManager]

    def _get_or_create_status(self, value):
        """
        Helper: Handles Status ID or Custom Status Name.
        """
        if str(value).isdigit():
            return int(value)
        
        if value:
            obj, _ = Status.objects.get_or_create(
                name__iexact=value.strip(),
                defaults={'name': value.strip()}
            )
            return obj.id
        return None

    def post(self, request):
        data = request.data
        
        # 1. Vehicle ID Validate
        vehicle_id = data.get('vehicle_id')
        if not vehicle_id:
            return Response({"status": "error", "message": "Vehicle ID is required."}, status=400)

        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        
        checks_list = data.get('checks', [])
        if not checks_list:
            return Response({"status": "error", "message": "No checks provided."}, status=400)

        saved_checks = []

        # 2. Transaction Block
        try:
            with transaction.atomic():
                for item in checks_list:
                    system_id = item.get('system_id')
                    status_val = item.get('status')
                    issues_count = item.get('number_of_issues', 0)

                    if not system_id or not status_val:
                        continue 

                    system_obj = get_object_or_404(System, id=system_id)
                    status_id = self._get_or_create_status(status_val)

                    # Update or Create Check
                    check_obj, created = SystemCheck.objects.update_or_create(
                        vehicle=vehicle,
                        system=system_obj,
                        defaults={
                            'status_id': status_id,
                            'number_of_issues': int(issues_count)
                        }
                    )
                    saved_checks.append(check_obj)

            # --- UPDATED RESPONSE LOGIC ---
            # Ab hum saved data ko wapis user ko dikhayenge
            response_serializer = SystemCheckSerializer(saved_checks, many=True)

            return Response({
                "status": "success",
                "message": f"Successfully recorded {len(saved_checks)} system checks.",
                "data": {
                    "vehicle_id": vehicle.id,
                    "processed_count": len(saved_checks),
                    "details": response_serializer.data  # <--- Ye naya data hai
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "status": "error",
                "message": "Error processing checks.",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class CreateNetworkSystemAPI(APIView):
    """
    Step 5 of PDI Process: Record Network System Checks (Bulk Operation).
    Handles CAN Bus, Electrical Network areas, etc.
    Security: Staff/Manager only.
    """
    permission_classes = [IsAuthenticated, IsStaffOrManager]

    def _get_or_create_status(self, value):
        """
        Helper: Handles Status ID or Custom Status Name.
        """
        if str(value).isdigit():
            return int(value)
        
        if value:
            obj, _ = Status.objects.get_or_create(
                name__iexact=value.strip(),
                defaults={'name': value.strip()}
            )
            return obj.id
        return None

    def post(self, request):
        data = request.data
        
        # 1. Vehicle ID Validate
        vehicle_id = data.get('vehicle_id')
        if not vehicle_id:
            return Response({"status": "error", "message": "Vehicle ID is required."}, status=400)

        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        
        # 2. Get List of Checks
        checks_list = data.get('checks', [])
        if not checks_list:
            return Response({"status": "error", "message": "No network checks provided."}, status=400)

        saved_items = []

        # 3. Transaction Block
        try:
            with transaction.atomic():
                for item in checks_list:
                    area_id = item.get('area_id')
                    status_val = item.get('status')
                    remark_text = item.get('remark', "")

                    if not area_id or not status_val:
                        continue 

                    # Verify Area Exists
                    area_obj = get_object_or_404(NetworkArea, id=area_id)
                    
                    # Get/Create Status
                    status_id = self._get_or_create_status(status_val)

                    # 4. Save to DB (Update or Create)
                    # Logic: Ek gadi ka Ek Area ka Ek hi record hoga
                    network_obj, created = NetworkSystem.objects.update_or_create(
                        vehicle=vehicle,
                        area=area_obj,
                        defaults={
                            'status_id': status_id,
                            'remark': remark_text
                        }
                    )
                    saved_items.append(network_obj)

            # 5. Return Response with Names (Improved UX)
            response_serializer = NetworkSystemSerializer(saved_items, many=True)

            return Response({
                "status": "success",
                "message": f"Successfully recorded {len(saved_items)} network system checks.",
                "data": {
                    "vehicle_id": vehicle.id,
                    "processed_count": len(saved_items),
                    "details": response_serializer.data 
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "status": "error",
                "message": "Error processing network checks.",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class LiveParametersAPI(APIView):
    """
    Step 6 of PDI Process: Live Data Parameters API.
    
    GET:  Fetch all saved live parameters for a specific vehicle.
    POST: Create or Update live parameters (Bulk Upload).
    
    Security: Staff/Manager only.
    """
    permission_classes = [IsAuthenticated, IsStaffOrManager]

    # --- HELPER METHODS (For POST Logic) ---
    def _get_or_create_system(self, value):
        """Helper to handle Parameter ID or Custom Name."""
        if str(value).isdigit():
            return int(value)
        if value:
            # Create new Parameter if text provided
            obj, _ = Parameters.objects.get_or_create(
                name__iexact=value.strip(),
                defaults={'name': value.strip()}
            )
            return obj.id
        return None

    def _get_or_create_inference(self, value):
        """Helper to handle Inference ID or Custom Voltage/Value."""
        if str(value).isdigit():
            return int(value)
        if value:
            # Create new Inference if text provided
            # Note: Field name 'interence' typo is maintained as per your model
            obj, _ = VoltageInference.objects.get_or_create(
                voltage__iexact=value.strip(),
                defaults={
                    'voltage': value.strip(),
                    'engine_state': '',
                    'interence': '', 
                    'recommendation': ''
                }
            )
            return obj.id
        return None

    # --- GET METHOD (Data Dekhne Ke Liye) ---
    def get(self, request):
        """
        Fetch Live Parameters for a specific vehicle.
        Usage: /api/pdi/live-parameters/?vehicle_id=1
        """
        vehicle_id = request.query_params.get('vehicle_id')

        if not vehicle_id:
            return Response({
                "status": "error",
                "message": "Please provide 'vehicle_id' in query params."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Database se data nikalo
        live_params = LiveParameters.objects.filter(vehicle_id=vehicle_id)
        
        # Serializer ke through JSON banao
        serializer = LiveParameterSerializer(live_params, many=True)

        return Response({
            "status": "success",
            "message": "Live parameters fetched successfully.",
            "data": {
                "vehicle_id": vehicle_id,
                "count": live_params.count(),
                "details": serializer.data
            }
        }, status=status.HTTP_200_OK)

    # --- POST METHOD (Data Bharne Ke Liye) ---
    def post(self, request):
        data = request.data
        
        # 1. Vehicle Validation
        vehicle_id = data.get('vehicle_id')
        if not vehicle_id:
            return Response({"status": "error", "message": "Vehicle ID is required."}, status=400)

        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        
        # 2. Get Data List
        params_list = data.get('parameters', [])
        if not params_list:
            return Response({"status": "error", "message": "No parameters provided."}, status=400)

        saved_items = []

        # 3. Transaction Block
        try:
            with transaction.atomic():
                for item in params_list:
                    system_val = item.get('system')     # Can be ID or "Custom Name"
                    inference_val = item.get('inference') # Can be ID or "Custom Value"

                    if not system_val or not inference_val:
                        continue 

                    # Smart Helpers call karo
                    system_id = self._get_or_create_system(system_val)
                    inference_id = self._get_or_create_inference(inference_val)

                    # Get Objects safely
                    system_obj = get_object_or_404(Parameters, id=system_id)
                    inference_obj = get_object_or_404(VoltageInference, id=inference_id)

                    # 4. Save to DB (Update or Create)
                    live_param_obj, created = LiveParameters.objects.update_or_create(
                        vehicle=vehicle,
                        system=system_obj,
                        defaults={
                            'interence': inference_obj 
                        }
                    )
                    saved_items.append(live_param_obj)

            # 5. Return Response
            response_serializer = LiveParameterSerializer(saved_items, many=True)

            return Response({
                "status": "success",
                "message": f"Successfully recorded {len(saved_items)} live parameters.",
                "data": {
                    "vehicle_id": vehicle.id,
                    "processed_count": len(saved_items),
                    "details": response_serializer.data 
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "status": "error",
                "message": "Error processing live parameters.",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



        
class PerformanceCheckAPI(APIView):
    """
    Step 7 of PDI Process: Performance Check API.
    
    GET:  Fetch saved performance checks for a vehicle.
    POST: Create or Update performance checks (Bulk Upload).
    
    Security: Staff/Manager only.
    """
    permission_classes = [IsAuthenticated, IsStaffOrManager]

    # --- HELPER 1: Handle System (Performance Parameter) ---
    def _get_or_create_system(self, value):
        # Agar ID bheji hai (e.g. "1")
        if str(value).isdigit():
            return int(value)
        # Agar Naya Naam bheja hai (e.g. "Nitro Boost")
        if value:
            obj, _ = Performance.objects.get_or_create(
                name__iexact=value.strip(),
                defaults={'name': value.strip()}
            )
            return obj.id
        return None

    # --- HELPER 2: Handle Status ---
    def _get_or_create_status(self, value):
        if str(value).isdigit():
            return int(value)
        if value:
            obj, _ = Status.objects.get_or_create(
                name__iexact=value.strip(),
                defaults={'name': value.strip()}
            )
            return obj.id
        return None

    # --- GET METHOD (Data Dekhne ke liye) ---
    def get(self, request):
        vehicle_id = request.query_params.get('vehicle_id')

        if not vehicle_id:
            return Response({
                "status": "error",
                "message": "Please provide 'vehicle_id' in query params."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Database se data uthao
        checks = PerformanceCheck.objects.filter(vehicle_id=vehicle_id)
        serializer = PerformanceCheckSerializer(checks, many=True)

        return Response({
            "status": "success",
            "message": "Performance checks fetched successfully.",
            "data": {
                "vehicle_id": vehicle_id,
                "count": checks.count(),
                "details": serializer.data
            }
        }, status=status.HTTP_200_OK)

    # --- POST METHOD (Data Save karne ke liye) ---
    def post(self, request):
        data = request.data
        
        # 1. Vehicle ID Check
        vehicle_id = data.get('vehicle_id')
        if not vehicle_id:
            return Response({"status": "error", "message": "Vehicle ID is required."}, status=400)

        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        
        # 2. List of Checks Check
        checks_list = data.get('checks', [])
        if not checks_list:
            return Response({"status": "error", "message": "No checks provided."}, status=400)

        saved_items = []

        try:
            with transaction.atomic():
                for item in checks_list:
                    system_val = item.get('system')
                    status_val = item.get('status')
                    recommendation_text = item.get('recommendation', "")

                    if not system_val or not status_val:
                        continue 

                    # Smart Helpers call karo (ID ya Name dono chalega)
                    system_id = self._get_or_create_system(system_val)
                    status_id = self._get_or_create_status(status_val)

                    # Objects fetch karo
                    system_obj = get_object_or_404(Performance, id=system_id)
                    
                    # Note: Status ID agar naya banaya hai to direct object use karo,
                    # warna ID se fetch karo. Helper ID return karta hai usually.
                    if status_id:
                        status_obj = Status.objects.get(id=status_id)
                    else:
                        continue

                    # 3. Save to DB (Update or Create)
                    # Logic: Ek Gadi + Ek System = Ek Record
                    check_obj, created = PerformanceCheck.objects.update_or_create(
                        vehicle=vehicle,
                        system=system_obj,
                        defaults={
                            'status': status_obj,
                            'recommendation': recommendation_text
                        }
                    )
                    saved_items.append(check_obj)

            # 4. Success Response
            response_serializer = PerformanceCheckSerializer(saved_items, many=True)

            return Response({
                "status": "success",
                "message": f"Successfully recorded {len(saved_items)} performance checks.",
                "data": {
                    "vehicle_id": vehicle.id,
                    "processed_count": len(saved_items),
                    "details": response_serializer.data 
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "status": "error",
                "message": "Error processing performance checks.",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class FluidLevelAPI(APIView):
    """
    Step 8: Fluid Level Inspection API.
    GET: Fetch fluid check history for a vehicle.
    POST: Bulk record fluid levels (Engine Oil, Coolant, etc.).
    """
    permission_classes = [IsAuthenticated, IsStaffOrManager]

    # --- SMART HELPERS ---
    def _handle_master_data(self, model, value):
        if not value: return None
        if str(value).isdigit(): return int(value)
        # Agar text hai toh dhoondo ya naya banao
        obj, _ = model.objects.get_or_create(
            name__iexact=str(value).strip(),
            defaults={'name': str(value).strip()}
        )
        return obj.id

    # --- GET: Fetch Data ---
    def get(self, request):
        vehicle_id = request.query_params.get('vehicle_id')
        if not vehicle_id:
            return Response({"status": "error", "message": "vehicle_id query param is required."}, status=400)

        data = FluidLevel.objects.filter(vehicle_id=vehicle_id)
        serializer = FluidLevelSerializer(data, many=True)
        return Response({
            "status": "success",
            "data": {"vehicle_id": vehicle_id, "details": serializer.data}
        })

    # --- POST: Save Data ---
    def post(self, request):
        data = request.data
        vehicle_id = data.get('vehicle_id')
        checks_list = data.get('checks', [])

        if not vehicle_id or not checks_list:
            return Response({"status": "error", "message": "Missing vehicle_id or checks list."}, status=400)

        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        saved_items = []

        try:
            with transaction.atomic():
                for item in checks_list:
                    # Smart matching for Area, Range, and Status
                    area_id = self._handle_master_data(FluidArea, item.get('area'))
                    range_id = self._handle_master_data(FluidRange, item.get('range'))
                    contam_id = self._handle_master_data(Status, item.get('contamination'))

                    if not area_id or not range_id or not contam_id:
                        continue

                    # Update or Create (Prevents duplicates for same area)
                    obj, _ = FluidLevel.objects.update_or_create(
                        vehicle=vehicle,
                        area_id=area_id,
                        defaults={
                            'in_range_id': range_id,
                            'contamination_id': contam_id,
                            'recommendation': item.get('recommendation', "").strip()
                        }
                    )
                    saved_items.append(obj)

            serializer = FluidLevelSerializer(saved_items, many=True)
            return Response({
                "status": "success",
                "message": f"Recorded {len(saved_items)} fluid checks.",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=500)
        
# CarPDI/api_views.py

class TyreConditionAPI(APIView):
    """
    Step 9: Tyre Condition Inspection API.
    GET: View saved tyre details for a vehicle.
    POST: Bulk update tyre status (Brand, Life, Condition).
    """
    permission_classes = [IsAuthenticated, IsStaffOrManager]

    def _get_status_obj(self, value):
        """Helper to get Status ID or create custom status."""
        if not value: return None
        if str(value).isdigit(): return int(value)
        
        obj, _ = Status.objects.get_or_create(
            name__iexact=str(value).strip(),
            defaults={'name': str(value).strip()}
        )
        return obj.id

    def get(self, request):
        vehicle_id = request.query_params.get('vehicle_id')
        
        # 1. Check if ID is provided
        if not vehicle_id:
            return Response({
                "status": "error", 
                "message": "vehicle_id is required in query parameters."
            }, status=status.HTTP_400_BAD_REQUEST)

        # 2. FIX: Check if Vehicle actually exists in Database
        if not Vehicle.objects.filter(id=vehicle_id).exists():
            return Response({
                "status": "error",
                "message": f"No vehicle found with ID {vehicle_id}."
            }, status=status.HTTP_404_NOT_FOUND)

        # 3. Fetch tyres only if vehicle exists
        tyres = TyreCondition.objects.filter(vehicle_id=vehicle_id)
        serializer = TyreConditionSerializer(tyres, many=True)
        
        return Response({
            "status": "success",
            "message": f"Retrieved {tyres.count()} tyre records.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        vehicle_id = data.get('vehicle_id')
        tyre_data = data.get('tyres', []) 

        # 1. Validation for input data
        if not vehicle_id:
            return Response({"status": "error", "message": "vehicle_id is required."}, status=400)
        
        if not tyre_data:
            return Response({"status": "error", "message": "Tyre data list cannot be empty."}, status=400)

        # 2. Verify Vehicle exists before processing
        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        saved_records = []

        try:
            with transaction.atomic():
                for entry in tyre_data:
                    # Position logic
                    pos_name = entry.get('position')
                    if not pos_name: continue
                    
                    pos_obj, _ = TyrePosition.objects.get_or_create(name=pos_name)

                    # Condition logic
                    cond_id = self._get_status_obj(entry.get('condition'))

                    # Update or Create
                    obj, created = TyreCondition.objects.update_or_create(
                        vehicle=vehicle,
                        position=pos_obj,
                        defaults={
                            'brand': entry.get('brand', 'Unknown'),
                            'condition_id': cond_id,
                            'remaining_life_percent': entry.get('remaining_life', 0)
                        }
                    )
                    saved_records.append(obj)

            serializer = TyreConditionSerializer(saved_records, many=True)
            return Response({
                "status": "success",
                "message": f"Successfully updated {len(saved_records)} tyres.",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "status": "error", 
                "message": "Internal server error during processing.",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



class PaintFinishAPI(APIView):
    """
    Step 10: Paint & Finish Quality API.
    GET:  View saved paint inspection details for a vehicle.
    POST: Bulk save/update paint status for body panels.
    """
    permission_classes = [IsAuthenticated, IsStaffOrManager]

    def _get_master_id(self, model, value):
        """Helper to get ID from master tables or create custom entries."""
        if not value: return None
        if str(value).isdigit(): return int(value)
        
        obj, _ = model.objects.get_or_create(
            name__iexact=str(value).strip(),
            defaults={'name': str(value).strip()}
        )
        return obj.id

    def get(self, request):
        vehicle_id = request.query_params.get('vehicle_id')
        
        if not vehicle_id:
            return Response({"status": "error", "message": "vehicle_id is required."}, status=400)

        # Industry Standard: Check if vehicle exists
        if not Vehicle.objects.filter(id=vehicle_id).exists():
            return Response({"status": "error", "message": f"No vehicle found with ID {vehicle_id}."}, status=404)

        data = PaintFinish.objects.filter(vehicle_id=vehicle_id)
        serializer = PaintFinishSerializer(data, many=True)
        return Response({
            "status": "success",
            "data": {"count": data.count(), "details": serializer.data}
        }, status=200)

    def post(self, request):
        data = request.data
        vehicle_id = data.get('vehicle_id')
        paint_checks = data.get('checks', [])

        if not vehicle_id or not paint_checks:
            return Response({"status": "error", "message": "Missing vehicle_id or checks data."}, status=400)

        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        saved_records = []

        try:
            with transaction.atomic():
                for item in paint_checks:
                    # Resolve IDs for Panel Area and Condition
                    area_id = self._get_master_id(PaintArea, item.get('area'))
                    condition_id = self._get_master_id(Status, item.get('condition'))

                    if not area_id or not condition_id: continue

                    # Update or Create (Ek gaadi ke ek panel ka ek hi status rahega)
                    obj, _ = PaintFinish.objects.update_or_create(
                        vehicle=vehicle,
                        area_id=area_id,
                        defaults={
                            'repainted': item.get('repainted', False),
                            'condition_id': condition_id,
                            'action': item.get('action', 'NIL').strip() or 'NIL'
                        }
                    )
                    saved_records.append(obj)

            serializer = PaintFinishSerializer(saved_records, many=True)
            return Response({
                "status": "success",
                "message": f"Recorded paint status for {len(saved_records)} panels.",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=500)



class FlushGapAPI(APIView):
    """
    Step 11: Flush and Gap Inspection API.
    GET:  View existing flush/gap records for a vehicle.
    POST: Bulk record panel alignment observations and actions.
    """
    permission_classes = [IsAuthenticated, IsStaffOrManager]

    def _get_master_id(self, model, value):
        """Helper to resolve ID or create custom Master Data."""
        if not value: return None
        if str(value).isdigit(): return int(value)
        
        obj, _ = model.objects.get_or_create(
            name__iexact=str(value).strip(),
            defaults={'name': str(value).strip()}
        )
        return obj.id

    def get(self, request):
        vehicle_id = request.query_params.get('vehicle_id')
        
        if not vehicle_id:
            return Response({"status": "error", "message": "vehicle_id is required."}, status=400)

        # Validation: Check if vehicle exists
        if not Vehicle.objects.filter(id=vehicle_id).exists():
            return Response({"status": "error", "message": f"No vehicle found with ID {vehicle_id}."}, status=404)

        data = FlushGap.objects.filter(vehicle_id=vehicle_id)
        serializer = FlushGapSerializer(data, many=True)
        
        return Response({
            "status": "success",
            "message": f"Retrieved {data.count()} flush gap records.",
            "data": serializer.data
        }, status=200)

    def post(self, request):
        data = request.data
        vehicle_id = data.get('vehicle_id')
        checks = data.get('checks', [])

        if not vehicle_id or not checks:
            return Response({"status": "error", "message": "Missing vehicle_id or checks data."}, status=400)

        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        saved_records = []

        try:
            with transaction.atomic():
                for item in checks:
                    # Resolve IDs for Area and Operation
                    area_id = self._get_master_id(FlushArea, item.get('area'))
                    op_id = self._get_master_id(Operations, item.get('operation'))

                    if not area_id or not op_id: continue

                    # Update or Create (Maintaining one record per vehicle-area-operation combo)
                    obj, _ = FlushGap.objects.update_or_create(
                        vehicle=vehicle,
                        area_id=area_id,
                        operation_id=op_id,
                        defaults={
                            'observation_gap': item.get('observation', 'No'),
                            'action': item.get('action', 'NIL').strip() or 'NIL'
                        }
                    )
                    saved_records.append(obj)

            serializer = FlushGapSerializer(saved_records, many=True)
            return Response({
                "status": "success",
                "message": f"Successfully updated {len(saved_records)} alignment records.",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=500)
        

class RubberComponentAPI(APIView):
    """
    Step 12: Rubber Components Inspection API.
    GET:  Retrieve saved rubber component checks for a vehicle.
    POST: Bulk record or update rubber part conditions.
    """
    permission_classes = [IsAuthenticated, IsStaffOrManager]

    def _resolve_master_id(self, model, value):
        """Helper to get ID or create custom entries for Rubber areas/Status."""
        if not value: return None
        if str(value).isdigit(): return int(value)
        
        obj, _ = model.objects.get_or_create(
            name__iexact=str(value).strip(),
            defaults={'name': str(value).strip()}
        )
        return obj.id

    def get(self, request):
        vehicle_id = request.query_params.get('vehicle_id')
        
        if not vehicle_id:
            return Response({"status": "error", "message": "vehicle_id is required."}, status=400)

        # Validation: Vehicle existance check
        if not Vehicle.objects.filter(id=vehicle_id).exists():
            return Response({"status": "error", "message": f"Vehicle with ID {vehicle_id} not found."}, status=404)

        data = RubberComponent.objects.filter(vehicle_id=vehicle_id)
        serializer = RubberComponentSerializer(data, many=True)
        
        return Response({
            "status": "success",
            "message": "Rubber component data fetched.",
            "data": serializer.data
        }, status=200)

    def post(self, request):
        data = request.data
        vehicle_id = data.get('vehicle_id')
        checks = data.get('checks', [])

        if not vehicle_id or not checks:
            return Response({"status": "error", "message": "Missing vehicle_id or checks list."}, status=400)

        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        saved_items = []

        try:
            with transaction.atomic():
                for item in checks:
                    # Resolve IDs
                    area_id = self._resolve_master_id(RubberArea, item.get('area'))
                    condition_id = self._resolve_master_id(Status, item.get('condition'))

                    if not area_id or not condition_id: continue

                    # Update or Create
                    obj, _ = RubberComponent.objects.update_or_create(
                        vehicle=vehicle,
                        area_id=area_id,
                        defaults={
                            'condition_id': condition_id,
                            'recommendation': item.get('recommendation', 'NIL').strip() or 'NIL'
                        }
                    )
                    saved_items.append(obj)

            serializer = RubberComponentSerializer(saved_items, many=True)
            return Response({
                "status": "success",
                "message": f"Successfully updated {len(saved_items)} rubber components.",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=500)


class GlassComponentAPI(APIView):
    """
    Step 13: Glass Components Inspection API.
    GET:  View saved glass inspection details for a vehicle.
    POST: Bulk save/update glass status (Brand, Cracks, Scratches).
    """
    permission_classes = [IsAuthenticated, IsStaffOrManager]

    def _resolve_master_id(self, model, value):
        """Helper to get ID or create custom Master Data."""
        if not value: return None
        if str(value).isdigit(): return int(value)
        
        obj, _ = model.objects.get_or_create(
            name__iexact=str(value).strip(),
            defaults={'name': str(value).strip()}
        )
        return obj.id

    def get(self, request):
        vehicle_id = request.query_params.get('vehicle_id')
        
        if not vehicle_id:
            return Response({"status": "error", "message": "vehicle_id is required."}, status=400)

        # Industry Standard: Strict 404 check
        if not Vehicle.objects.filter(id=vehicle_id).exists():
            return Response({"status": "error", "message": f"No vehicle found with ID {vehicle_id}."}, status=404)

        data = GlassComponent.objects.filter(vehicle_id=vehicle_id)
        serializer = GlassComponentSerializer(data, many=True)
        return Response({
            "status": "success",
            "message": "Glass component records retrieved.",
            "data": {"count": data.count(), "details": serializer.data}
        }, status=200)

    def post(self, request):
        data = request.data
        vehicle_id = data.get('vehicle_id')
        glass_checks = data.get('checks', [])

        if not vehicle_id or not glass_checks:
            return Response({"status": "error", "message": "Missing vehicle_id or checks data."}, status=400)

        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        saved_records = []

        try:
            with transaction.atomic():
                for item in glass_checks:
                    # Resolve IDs for Area and Condition
                    area_id = self._resolve_master_id(GlassArea, item.get('area'))
                    condition_id = self._resolve_master_id(Status, item.get('condition'))

                    if not area_id or not condition_id: continue

                    # Update or Create (Maintaining one record per vehicle-area combo)
                    obj, _ = GlassComponent.objects.update_or_create(
                        vehicle=vehicle,
                        area_id=area_id,
                        defaults={
                            'brand': item.get('brand', 'Original').strip(),
                            'condition_id': condition_id,
                            'recommendation': item.get('recommendation', 'NIL').strip() or 'NIL'
                        }
                    )
                    saved_records.append(obj)

            serializer = GlassComponentSerializer(saved_records, many=True)
            return Response({
                "status": "success",
                "message": f"Recorded glass inspection for {len(saved_records)} components.",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=500)
        

class InteriorComponentAPI(APIView):
    """
    Step 14: Interior Components Inspection API.
    GET:  View saved interior inspection details for a vehicle.
    POST: Bulk update interior status (Dashboard, Seats, Upholstery).
    """
    permission_classes = [IsAuthenticated, IsStaffOrManager]

    def _resolve_master_id(self, model, value):
        """Helper to get ID or create custom Master Data on the fly."""
        if not value: return None
        if str(value).isdigit(): return int(value)
        
        obj, _ = model.objects.get_or_create(
            name__iexact=str(value).strip(),
            defaults={'name': str(value).strip()}
        )
        return obj.id

    def get(self, request):
        vehicle_id = request.query_params.get('vehicle_id')
        
        if not vehicle_id:
            return Response({"status": "error", "message": "vehicle_id is required."}, status=400)

        # 404 Validation: Vehicle check
        if not Vehicle.objects.filter(id=vehicle_id).exists():
            return Response({"status": "error", "message": f"No vehicle found with ID {vehicle_id}."}, status=404)

        data = InteriorComponent.objects.filter(vehicle_id=vehicle_id)
        serializer = InteriorComponentSerializer(data, many=True)
        return Response({
            "status": "success",
            "message": "Interior component records retrieved.",
            "data": {"count": data.count(), "details": serializer.data}
        }, status=200)

    def post(self, request):
        data = request.data
        vehicle_id = data.get('vehicle_id')
        interior_checks = data.get('checks', [])

        if not vehicle_id or not interior_checks:
            return Response({"status": "error", "message": "Missing vehicle_id or checks data."}, status=400)

        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        saved_records = []

        try:
            with transaction.atomic():
                for item in interior_checks:
                    # Resolve IDs for Category, Area and Condition
                    cat_id = self._resolve_master_id(InteriorCategory, item.get('category'))
                    area_id = self._resolve_master_id(InteriorArea, item.get('area'))
                    condition_id = self._resolve_master_id(Status, item.get('condition'))

                    if not cat_id or not area_id or not condition_id: continue

                    # Update or Create
                    obj, _ = InteriorComponent.objects.update_or_create(
                        vehicle=vehicle,
                        category_id=cat_id,
                        area_id=area_id,
                        defaults={
                            'condition_id': condition_id,
                            'recommendation': item.get('recommendation', 'NIL').strip() or 'NIL'
                        }
                    )
                    saved_records.append(obj)

            serializer = InteriorComponentSerializer(saved_records, many=True)
            return Response({
                "status": "success",
                "message": f"Recorded interior inspection for {len(saved_records)} components.",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=500)
        
class DocumentationAPI(APIView):
    """
    Step 15 (Final): Documentation Checklist API.
    GET:  View the checklist status for a vehicle.
    POST: Bulk update document statuses (Available/Missing/Pending).
    """
    permission_classes = [IsAuthenticated, IsStaffOrManager]

    def _get_master_id(self, model, value):
        """Helper for smart matching: ID or Text Name."""
        if not value: return None
        if str(value).isdigit(): return int(value)
        
        obj, _ = model.objects.get_or_create(
            name__iexact=str(value).strip(),
            defaults={'name': str(value).strip()}
        )
        return obj.id

    def get(self, request):
        vehicle_id = request.query_params.get('vehicle_id')
        
        if not vehicle_id:
            return Response({"status": "error", "message": "vehicle_id is required."}, status=400)

        # Strict Validation
        if not Vehicle.objects.filter(id=vehicle_id).exists():
            return Response({"status": "error", "message": f"No vehicle found with ID {vehicle_id}."}, status=404)

        docs = Documentation.objects.filter(vehicle_id=vehicle_id)
        serializer = DocumentationSerializer(docs, many=True)
        
        return Response({
            "status": "success",
            "message": "Documentation checklist retrieved.",
            "data": {"count": docs.count(), "details": serializer.data}
        }, status=200)

    def post(self, request):
        data = request.data
        vehicle_id = data.get('vehicle_id')
        doc_list = data.get('documents', [])

        if not vehicle_id or not doc_list:
            return Response({"status": "error", "message": "Missing vehicle_id or documents list."}, status=400)

        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        saved_records = []

        try:
            with transaction.atomic():
                for item in doc_list:
                    # Resolve IDs for Document Type and Status
                    doc_type_id = self._get_master_id(DocumentType, item.get('document'))
                    status_id = self._get_master_id(Status, item.get('status'))

                    if not doc_type_id or not status_id: continue

                    # Update or Create (Ek vehicle ke ek document ka ek hi status rahega)
                    obj, _ = Documentation.objects.update_or_create(
                        vehicle=vehicle,
                        document_id=doc_type_id,
                        defaults={
                            'status_id': status_id,
                            'remark': item.get('remark', '').strip()
                        }
                    )
                    saved_records.append(obj)

            serializer = DocumentationSerializer(saved_records, many=True)
            return Response({
                "status": "success",
                "message": f"Successfully processed {len(saved_records)} documents.",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=500)

