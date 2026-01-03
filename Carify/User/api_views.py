from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from .serializers import *
from django.contrib.auth import login
from rest_framework.permissions import IsAuthenticated , IsAdminUser
from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta
from django.contrib.sessions.models import Session
from rest_framework import generics
from .models import *
from CarPDI.models import *
from CarPDI.serializers import VehicleSerializer
from django.db.models import Count, Sum, F, ExpressionWrapper, DurationField
from django.shortcuts import get_object_or_404
import logging
import requests
from rest_framework.pagination import PageNumberPagination

class LoginAPIView(APIView):
    """
    Authenticates user and returns an Auth Token.
    Returns 'redirect_to' ('admin_dashboard' or 'profile') based on user verification status.
    """
    permission_classes = [AllowAny]  # anyone can login 

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Token Generate 
            token, created = Token.objects.get_or_create(user=user)
            
            if user.is_superuser or user.is_staff or user.is_verified_by_admin:
                destination = 'admin_dashboard'
                message = f'Welcome {user.first_name}!'
            else:
                destination = 'profile'  # Unverified users go to the profile 
                message = "Please complete your profile. Waiting for admin verification."

            # return Response 
            return Response({
                'token': token.key,
                'user': UserDetailSerializer(user).data,
                'redirect_to': destination,  
                'message': message,
                'success': True
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class LogoutAPIView(APIView):
    """
    Logs out the user by deleting their current Auth Token.
    Requires a valid 'Authorization' header.
    """
    permission_classes = [IsAuthenticated]  # only logged-in user can logout 

    def post(self, request):
        try:
            # delete present User token 
            request.user.auth_token.delete()
            
            return Response({
                "message": "Successfully logged out.",
                "success": True,
                "redirect_to": "login" 
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "message": "Something went wrong.",
                "error": str(e),
                "success": False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class RegisterAPIView(generics.CreateAPIView):
    """
    Registers a new user account.
    Public endpoint (no authentication required).
    """
    queryset = CustomUser.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]


class AdminDashboardAPIView(APIView):
    """
    Retrieves aggregated dashboard statistics (users, vehicles, health scores) and vehicle records.
    Restricted to Admin/Staff users.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        # ---  Aggregations (Counts & Averages) ---
        total_vehicles = Vehicle.objects.count()
        total_customers = Customer.objects.count()
        
        # Avg Health Score calculation
        avg_score_data = Vehicle.objects.aggregate(avg=Avg('health_score'))
        avg_health_score = avg_score_data['avg'] if avg_score_data['avg'] else 0
        
        # Recent Inspections (Last 7 days)
        last_week = timezone.now() - timedelta(days=7)
        recent_inspections = Vehicle.objects.filter(inspection_date__gte=last_week).count()

        # ---  User Stats ---
        users = CustomUser.objects.all()
        total_users = users.count()
        verified_users = users.filter(is_verified_by_admin=True).count()
        
        # Active Users Logic (Session based)
        active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
        active_user_ids = []
        for session in active_sessions:
            data = session.get_decoded()
            user_id = data.get('_auth_user_id')
            if user_id:
                active_user_ids.append(user_id)
        
        # Unique active users count
        active_users_count = users.filter(id__in=set(active_user_ids)).count()
        inactive_users = total_users - active_users_count

        # ---  Vehicle List ---
        # fetch all vehicles (Latest first)
        vehicles_qs = Vehicle.objects.select_related('customer').all().order_by('-inspection_date')
        vehicle_serializer = VehicleSerializer(vehicles_qs, many=True)

        # ---  Final JSON Response ---
        return Response({
            "stats": {
                "total_users": total_users,
                "active_users": active_users_count,
                "inactive_users": inactive_users,
                "verified_users": verified_users,
                "total_customers": total_customers,
                "total_vehicles": total_vehicles,
                "avg_health_score": round(avg_health_score, 1), # Round to 1 decimal
                "recent_inspections_count": recent_inspections
            },
            "vehicles": vehicle_serializer.data
        })
    


class UserManagementDashboardAPIView(generics.ListAPIView):
    """
    Retrieves a list of all users with calculated performance metrics (vehicle counts, login duration).
    
    **Query Parameters:**
    * `search` (optional): Filter users by email (e.g., `?search=admin@example.com`).
    
    Restricted to Admin/Staff users.
    """
    serializer_class = UserManagementSerializer
    permission_classes = [IsAuthenticated, IsAdminUser] # only admin can see

    def get_queryset(self):
        # Search Query
        search_query = self.request.query_params.get('search', '')
        users_qs = CustomUser.objects.all()

        if search_query:
            users_qs = users_qs.filter(email__icontains=search_query)

        # Annotations ( On Heavy lifting database)
        users = users_qs.annotate(
            vehicle_count=Count('inspected_vehicles', distinct=True),
            total_login_duration=Sum(
                ExpressionWrapper(
                    F('sessions__logout_time') - F('sessions__login_time'),
                    output_field=DurationField()
                ),
                distinct=True
            )
        )
        return users


class UserActionAPIView(APIView):
    """
    Performs administrative actions on a specific user account.

    **Supported Methods:**
    * `POST`: Change verification status. Action must be `verify` or `unverify`.
        * *Note:* Users cannot modify their own status.
    * `DELETE`: Permanently remove a user account.
        * *Permission:* Restricted to **Superusers** only. Cannot delete other Super Admins.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, action, user_id):
        # --- VERIFY / UNVERIFY ) ---
        user = get_object_or_404(CustomUser, id=user_id)
        
        # Safety Check: no one can get varify/unverify by itself 
        if user.id == request.user.id:
             return Response({"error": "You cannot change your own status."}, status=status.HTTP_403_FORBIDDEN)

        if action == 'verify':
            user.is_verified_by_admin = True
            msg = f"User {user.email} verified successfully."
        elif action == 'unverify':
            user.is_verified_by_admin = False
            msg = f"User {user.email} unverified successfully."
        else:
            return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)
            
        user.save()
        return Response({"message": msg, "success": True}, status=status.HTTP_200_OK)

    def delete(self, request, user_id):
        # --- DELETE (only Superuser/Owner can) ---
        if not request.user.is_superuser:
            return Response({
                "error": "Permission Denied. Only Super Admin can delete users.",
                "success": False
            }, status=status.HTTP_403_FORBIDDEN)

        user = get_object_or_404(CustomUser, id=user_id)
        
        if user.is_superuser:
             return Response({"error": "Cannot delete a Super Admin."}, status=status.HTTP_403_FORBIDDEN)

        user.delete()
        return Response({"message": "User deleted successfully.", "success": True}, status=status.HTTP_200_OK)
    




class EngineerListAPIView(generics.ListAPIView):
    """
    Retrieves verified engineers with inspection counts.
    Supports email search via '?search=' query param.
    """
    serializer_class = UserManagementSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        search_query = self.request.query_params.get('search', '')

        # Filter 1: Only Verified Users
        # Filter 2: Exclude Superusers (BOSS ko list mein mat dikhao)
        engineers = CustomUser.objects.filter(is_verified_by_admin=True).exclude(is_superuser=True)

        if search_query:
            engineers = engineers.filter(email__icontains=search_query)

        return engineers.annotate(vehicle_count=Count('inspected_vehicles'))
    


class StaffLeaveCalendarAPIView(APIView):
    """Retrieves leave history. Restricted to Owner or Superuser."""
    permission_classes = [IsAuthenticated] # Basic login required

    def get(self, request, user_id):
        # 1. Permission Check (Industry Standard)
        if not request.user.is_superuser and request.user.id != user_id:
            return Response(
                {"error": "You are not authorized to view another user's leaves."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        # 2. Data Fetch
        user = get_object_or_404(CustomUser, id=user_id)
        leaves = Leave.objects.filter(user=user).order_by('-start_date')

        return Response({
            "user": UserDetailSerializer(user).data,
            "leaves": LeaveSerializer(leaves, many=True).data
        })

class LeaveEventsAPIView(APIView):
    """Returns formatted JSON events for Frontend Calendar."""
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        # Security Check: Only Owner or Superuser can view
        if not request.user.is_superuser and request.user.id != user_id:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        leaves = Leave.objects.filter(user__id=user_id)
        serializer = LeaveCalendarSerializer(leaves, many=True)
        
        # 'safe=False' ki zaroorat nahi kyunki DRF automatically list handle karta hai
        return Response(serializer.data)
    


class UserProfileAPIView(APIView):
    """
    Retrieves or Updates the currently logged-in user's profile.
    Uses PATCH for partial updates (e.g., changing only the name).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Current user ka data fetch karo
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        # Current user ka data update karo
        # partial=True ka matlab hai saare fields bhejna zaroori nahi hai
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Profile updated successfully.",
                "data": serializer.data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class UserProfileDetailAPIView(generics.RetrieveAPIView):
    """
    Retrieves full profile details of a specific user.
    
    **Industry Standard Logic:**
    * Superusers can view ANY profile.
    * Staff can view profiles EXCEPT Superusers.
    * (Staff cannot spy on the Boss).
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'id'

    def get_queryset(self):
        # 1. Base Queryset (all users)
        queryset = CustomUser.objects.all()
        
        # 2. Check who is asking?
        current_user = self.request.user

       
        if not current_user.is_superuser:
            queryset = queryset.exclude(is_superuser=True)
            
        return queryset


logger = logging.getLogger(__name__)

class VerifyBankDetailsAPI(APIView):
    def post(self, request):
        # 1. Input Validation using Serializer
        serializer = BankVerificationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                "status": "error",
                "message": "Invalid input data.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validated data extract 
        account_number = serializer.validated_data['account_number']
        ifsc_code = serializer.validated_data['ifsc_code']

        # 2. External API Configuration
        api_url = getattr(settings, 'BANK_API_URL', "https://api.example.com/bank/verify")
        api_key = getattr(settings, 'BANK_VERIFICATION_API_KEY', "dummy_key")

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }
        payload = {
            'account_number': account_number,
            'ifsc': ifsc_code,
        }

        # 3. Third-Party API Call with Error Handling
        try:
            response = requests.post(api_url, json=payload, headers=headers, timeout=10)
            
            # if api return  500 or 404 error 
            response.raise_for_status() 
            
            result = response.json()

            # 4. Success Logic
            if result.get('verified'):
                return Response({
                    "status": "success",
                    "message": "Bank account verified successfully!",
                    "data": result 
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "status": "fail",
                    "message": "Bank verification failed. Details did not match.",
                    "data": result
                }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        except requests.exceptions.Timeout:
            logger.error(f"Bank API Timeout for Account: {account_number}")
            return Response({
                "status": "error",
                "message": "Bank verification service timed out. Please try again later."
            }, status=status.HTTP_504_GATEWAY_TIMEOUT)

        except requests.exceptions.RequestException as e:
            # Network error or connection error 
            logger.error(f"Bank API Error: {str(e)}")
            return Response({
                "status": "error",
                "message": "Unable to connect to verification service."
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        except Exception as e:
            logger.exception("Unexpected error in VerifyBankDetailsAPI")
            return Response({
                "status": "error",
                "message": "An internal server error occurred."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# ---  Apply Leave & List Leaves (Employee ) ---
class ApplyLeaveAPI(APIView):
    """
    Handles the leave application process for employees.
    """
    permission_classes = [IsAuthenticated]  

    def get(self, request):
        """
        Retrieve the history of all leaves applied by the logged-in user.
        """
        leaves = Leave.objects.filter(user=request.user).order_by('-created_at')
        serializer = LeaveSerializer(leaves, many=True)
        return Response({
            "status": "success",
            "message": "Leaves fetched successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Submit a new leave application. 
        Requires start_date, end_date, and reason.
        """
        serializer = LeaveSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({
                "status": "success",
                "message": "Leave applied successfully!",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": "error",
            "message": "Invalid data",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# ---  Approve Leave (Admin/Manager) ---
class ApproveLeaveAPI(APIView):
    """
    Handles the approval of leave requests.
    """
    permission_classes = [IsAuthenticated, IsAdminUser] 

    def patch(self, request, leave_id):
        """
        Approve a specific leave request by its ID.
        Restricted to Admins and Managers only.
        """
        leave = get_object_or_404(Leave, id=leave_id)
        
        # Status update logic
        leave.status = 'approved'
        leave.save()
        
        return Response({
            "status": "success",
            "message": f"Leave for {leave.user.email} has been Approved.",
            "data": {"leave_id": leave.id, "status": "approved"}
        }, status=status.HTTP_200_OK)


# --- Reject Leave (Admin/Manager) ---
class RejectLeaveAPI(APIView):
    """
    Handles the rejection of leave requests.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, leave_id):
        """
        Reject a specific leave request by its ID.
        Restricted to Admins and Managers only.
        """
        leave = get_object_or_404(Leave, id=leave_id)
        
        # Status update logic
        leave.status = 'rejected'
        leave.save()
        
        return Response({
            "status": "success",
            "message": f"Leave for {leave.user.email} has been Rejected.",
            "data": {"leave_id": leave.id, "status": "rejected"}
        }, status=status.HTTP_200_OK)


# Pagination Class (Taaki data pages mein aaye - Page 1, Page 2...)
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ManageLeavesAPI(APIView):
    """
    Admin View to list all leave applications with pagination.
    """
    permission_classes = [IsAuthenticated, IsAdminUser] 
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        """
        Retrieve a paginated list of all leaves for management.
        Supports filtering by status (e.g., ?status=pending).
        """
        # 1. Base Query
        leaves = Leave.objects.all().order_by('-created_at')

        # 2. Filtering (Optional Standard Feature)
        status_param = request.query_params.get('status')
        if status_param:
            leaves = leaves.filter(status=status_param)

        # 3. Pagination Logic (Industry Standard)
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(leaves, request)
        
        serializer = LeaveSerializer(result_page, many=True)

        # 4. Custom Response with Pagination Metadata
        return Response({
            "status": "success",
            "message": "All leaves fetched successfully",
            "data": {
                "count": paginator.page.paginator.count, # Total records
                "next": paginator.get_next_link(),       # Next page URL
                "previous": paginator.get_previous_link(), # Previous page URL
                "results": serializer.data               # Actual Data
            }
        }, status=status.HTTP_200_OK)
    



class UserLoginReportAPI(APIView):
    """
    Admin View to generate login/logout activity report for a specific user.
    """
    permission_classes = [IsAuthenticated, IsAdminUser] 
    pagination_class = StandardResultsSetPagination

    def get(self, request, user_id):
        """
        Retrieve paginated session logs and total active duration for a user.
        """
        user = get_object_or_404(CustomUser, id=user_id)
        
        # 1. Fetch Sessions Queryset
        sessions = user.sessions.all().order_by('-login_time')

        # 2. Calculate Total Duration (Aggregation)
        total_duration_delta = sessions.aggregate(
            total=Sum(ExpressionWrapper(
                F('logout_time') - F('login_time'),
                output_field=DurationField()
            ))
        )['total']

        # Duration ko Readable String mein convert karna
        formatted_duration = "0h 0m"
        if total_duration_delta:
            total_seconds = int(total_duration_delta.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            formatted_duration = f"{hours}h {minutes}m"

        # 3. Pagination Logic
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(sessions, request)
        serializer = UserSessionSerializer(result_page, many=True)

        # 4. Final Structured Response
        return Response({
            "status": "success",
            "message": f"Activity report for {user.email}",
            "data": {
                "user_details": {
                    "id": user.id,
                    "email": user.email,
                    "leave_count": user.leaves.count(),
                    "total_logged_in_duration": formatted_duration
                },
                "sessions": {
                    "count": paginator.page.paginator.count,
                    "next": paginator.get_next_link(),
                    "previous": paginator.get_previous_link(),
                    "results": serializer.data
                }
            }
        }, status=status.HTTP_200_OK)


# ---  Get Vehicles by Specific User (Filtered & Paginated) ---
class UserInspectedVehiclesAPI(APIView):
    """
    Retrieve paginated list of vehicles inspected by a specific user.
    Supports filtering by 'model' and 'date'.
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get(self, request, user_id):
        # 1. User Validation
        user = get_object_or_404(CustomUser, id=user_id)
        
        # 2. Base Query
        vehicles = Vehicle.objects.filter(inspected_by=user).order_by('-inspection_date')

        # 3. Apply Filters (Query Params)
        model_query = request.query_params.get('model')
        date_query = request.query_params.get('date')

        if model_query:
            vehicles = vehicles.filter(model__icontains=model_query)
        
        if date_query:
            vehicles = vehicles.filter(inspection_date=date_query)

        # 4. Pagination
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(vehicles, request)
        serializer = VehicleSerializer(result_page, many=True)

        return Response({
            "status": "success",
            "message": f"Vehicles inspected by {user.email}",
            "data": {
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": serializer.data
            }
        }, status=status.HTTP_200_OK)


# ---  Get All Vehicles (Filtered & Paginated) ---
class AllInspectedVehiclesAPI(APIView):
    """
    Retrieve paginated list of ALL inspected vehicles.
    Supports filtering by 'model' and 'date'.
    """
    permission_classes = [IsAuthenticated] # Agar sirf Admin ke liye chahiye to IsAdminUser laga dena
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        # 1. Base Query
        vehicles = Vehicle.objects.all().order_by('-inspection_date')

        # 2. Apply Filters
        model_query = request.query_params.get('model')
        date_query = request.query_params.get('date')

        if model_query:
            vehicles = vehicles.filter(model__icontains=model_query)
        
        if date_query:
            vehicles = vehicles.filter(inspection_date=date_query)

        # 3. Pagination
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(vehicles, request)
        serializer = VehicleSerializer(result_page, many=True)

        return Response({
            "status": "success",
            "message": "All inspected vehicles fetched successfully",
            "data": {
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": serializer.data
            }
        }, status=status.HTTP_200_OK)
    



# User/api_views.py

class VehicleReportAPI(APIView):
    """
    Retrieves a comprehensive report for a specific vehicle.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, vehicle_id):
        # Vehicle fetch karo
        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        
        # Helper function: Safe .values() retrieval
        def get_data(model_class):
            return list(model_class.objects.filter(vehicle=vehicle).values())

        # Response Data construct karte waqt 'getattr' use karenge safety ke liye
        response_data = {
            "vehicle_details": {
                "id": vehicle.id,
                "model": getattr(vehicle, 'model', 'Unknown Model'), # Safe access
                "inspection_date": getattr(vehicle, 'inspection_date', None),
                # "status": vehicle.status,  <-- YE LINE ERROR DE RAHI THI, HATA DI
                "vin": getattr(vehicle, 'vin', None),
            },
            # Related Data Sections
            "obd_readings": list(OBDReading.objects.filter(vehicle=vehicle).values()),
            "system_checks": get_data(SystemCheck),
            "network_systems": get_data(NetworkSystem),
            "fluid_levels": get_data(FluidLevel),
            "live_parameters": get_data(LiveParameters),
            "performance_checks": get_data(PerformanceCheck),
            "paint_finishes": get_data(PaintFinish),
            "tyre_conditions": get_data(TyreCondition),
            "flush_gaps": get_data(FlushGap),
            "rubber_components": get_data(RubberComponent),
            "glass_components": get_data(GlassComponent),
            "interior_components": get_data(InteriorComponent),
            "documentations": get_data(Documentation),
        }

        return Response({
            "status": "success",
            "message": f"Full report fetched successfully",
            "data": response_data
        }, status=status.HTTP_200_OK)


# ---  Delete Vehicle API ---
class DeleteVehicleAPI(APIView):
    """
    Deletes a specific vehicle record permanently.
    Restricted to Admins/Superusers.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request, pk):
        vehicle = get_object_or_404(Vehicle, pk=pk)
        vehicle_model = vehicle.model 
        
        vehicle.delete()
        
        return Response({
            "status": "success",
            "message": f"Vehicle '{vehicle_model}' has been deleted successfully."
        }, status=status.HTTP_204_NO_CONTENT)    
    


class CreateVehicleAPI(APIView):
    """
    API to register a new vehicle for inspection.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VehicleSerializer(data=request.data)
        
        if serializer.is_valid():
            vehicle = serializer.save(inspected_by=request.user)
            
            return Response({
                "status": "success",
                "message": "Vehicle created successfully!",
                "data": {
                    "id": vehicle.id, 
                    "model": vehicle.model,
                    # "status": vehicle.status
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            "status": "error",
            "message": "Invalid data provided.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)



# --- 1. Roles Management (Dashboard + Create Role) ---
class RoleManagementAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """List all roles with their assigned permissions."""
        roles = Roles.objects.prefetch_related('permissions').all()
        serializer = RoleSerializer(roles, many=True)
        return Response({"status": "success", "data": serializer.data}, status=200)

    def post(self, request):
        """Create a new role."""
        serializer = RoleSerializer(data=request.data)
        if serializer.is_valid():
            role = serializer.save()
            return Response({
                "status": "success", 
                "message": f"Role '{role.name}' created successfully.",
                "data": serializer.data
            }, status=201)
        return Response(serializer.errors, status=400)


# --- 2. Permissions Management (List & Create) ---
class PermissionManagementAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """List all available permissions."""
        perms = Permissions.objects.all()
        serializer = PermissionSerializer(perms, many=True)
        return Response({"status": "success", "data": serializer.data}, status=200)

    def post(self, request):
        """Create a new permission."""
        serializer = PermissionSerializer(data=request.data)
        if serializer.is_valid():
            perm = serializer.save()
            return Response({
                "status": "success", 
                "message": f"Permission '{perm.name}' created.",
                "data": serializer.data
            }, status=201)
        return Response(serializer.errors, status=400)


# --- 3. Assign Permissions to Role ---
class AssignRolePermissionsAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        """Update permissions for a specific role (Bulk Assign)."""
        serializer = AssignPermissionSerializer(data=request.data)
        if serializer.is_valid():
            role = get_object_or_404(Roles, id=serializer.data['role_id'])
            permission_ids = serializer.data['permission_ids']
            
            # Fetch Permissions safely
            permissions = Permissions.objects.filter(code__in=permission_ids)
            
            # Set Many-to-Many relationship
            role.permissions.set(permissions)
            
            return Response({
                "status": "success",
                "message": f"Updated permissions for role '{role.name}'",
                "total_permissions": permissions.count()
            }, status=200)
        return Response(serializer.errors, status=400)


# --- 4. User Role Management (Dashboard List & Assign) ---
class UserRoleManagementAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """List all users and their assigned roles."""
        user_roles = UserRole.objects.select_related('user', 'role').all()
        serializer = UserRoleSerializer(user_roles, many=True)
        return Response({"status": "success", "data": serializer.data}, status=200)

    def post(self, request):
        """Assign a role to a specific user (Update or Create)."""
        serializer = AssignUserRoleSerializer(data=request.data)
        if serializer.is_valid():
            user = get_object_or_404(CustomUser, id=serializer.data['user_id'])
            role = get_object_or_404(Roles, id=serializer.data['role_id'])
            
            # Industry Standard: Update existing or Create new
            UserRole.objects.update_or_create(
                user=user, 
                defaults={'role': role}
            )
            
            return Response({
                "status": "success",
                "message": f"Role '{role.name}' assigned to user {user.email}"
            }, status=200)
        return Response(serializer.errors, status=400)