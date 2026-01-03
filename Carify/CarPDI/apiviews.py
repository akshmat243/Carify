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
    

class CreateSystemCheckAPI(APIView):
    """
    Step 4 of PDI Process: Record System Checks (Bulk Operation).
    Receives a list of checks for different systems (Engine, Brakes, etc.).
    Security: Staff/Manager only.
    """
    permission_classes = [IsAuthenticated, IsStaffOrManager]

    def _get_or_create_status(self, value):
        """
        Helper: Handles Status ID or Custom Status Name.
        Example: Input '1' -> Returns ID 1. Input 'Leaking' -> Creates 'Leaking' & returns new ID.
        """
        if str(value).isdigit():
            return int(value)
        
        # Agar text bheja hai (e.g. "Rusting"), to find or create karo
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
        
        # 2. 'checks_list' expect kar rahe hain jisme saara data hoga
        checks_list = data.get('checks', [])

        if not checks_list:
            return Response({"status": "error", "message": "No checks provided."}, status=400)

        saved_checks = []

        # 3. Transaction Block (Safety ke liye)
        try:
            with transaction.atomic():
                # Loop through each check item
                for item in checks_list:
                    system_id = item.get('system_id')
                    status_val = item.get('status') # Can be ID "1" or Text "Rust Found"
                    issues_count = item.get('number_of_issues', 0)

                    if not system_id or not status_val:
                        continue # Skip incomplete data

                    # System Valid hai ya nahi?
                    system_obj = get_object_or_404(System, id=system_id)
                    
                    # Status logic (Smart Helper)
                    status_id = self._get_or_create_status(status_val)

                    # 4. Save to DB (Update_or_Create logic)
                    # Agar is gaadi ka is system ka check pehle se hai, to update karo
                    check_obj, created = SystemCheck.objects.update_or_create(
                        vehicle=vehicle,
                        system=system_obj,
                        defaults={
                            'status_id': status_id,
                            'number_of_issues': int(issues_count)
                        }
                    )
                    saved_checks.append(check_obj)

            # Response
            return Response({
                "status": "success",
                "message": f"Successfully recorded {len(saved_checks)} system checks.",
                "data": {
                    "vehicle_id": vehicle.id,
                    "processed_count": len(saved_checks)
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "status": "error",
                "message": "Error processing checks.",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


