from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import CustomUserSerializer
from django.contrib.auth import authenticate, login
import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.shortcuts import redirect
from .models import CustomUser
logger = logging.getLogger(__name__)

class RegisterView(APIView):
    def post(self, request):
        username = request.data.get('username')

        # Check if user already exists in the database
        user = CustomUser.objects.filter(username=username).first()

        if user:
            # User exists, so just update the roles
            roles = request.data.get('role', [])
            
            # Ensure roles are passed as a list of strings
            if isinstance(roles, str):
                roles = roles.split(',')  # Convert comma-separated string into a list
            elif not isinstance(roles, list):
                return Response({"error": "Roles must be a list of strings."}, status=status.HTTP_400_BAD_REQUEST)
            
            roles = [role.strip() for role in roles]  # Clean up any extra spaces
            
            existing_roles = user.role if isinstance(user.role, list) else [user.role] if user.role else []

            if 'driver' in roles and 'driver' in existing_roles:
                return Response({"error": "You already have the 'driver' role."}, status=status.HTTP_400_BAD_REQUEST)

            if 'owner' in roles and 'owner' in existing_roles:
                return Response({"error": "You already have the 'owner' role."}, status=status.HTTP_400_BAD_REQUEST)

            # Ensure that the user doesn't have the same role already
            new_roles = [role for role in roles if role not in existing_roles]
            if new_roles:
                # Only add new roles
                user.role = existing_roles + new_roles
                user.save()

            return Response({
                "message": "User roles updated successfully!",
                "roles": user.role
            }, status=status.HTTP_200_OK)
        else:
            # If user doesn't exist, create new user
            serializer = CustomUserSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()  # Save the user
                return Response({
                    "message": "User created successfully!",
                    "roles": user.role
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        logger.info("Received data: %s", request.data)
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_authenticated:
            login(request, user)  # Creates a session for the user
            request.session['user_id'] = user.id  # Store user ID in session
            
            # Fetch user's roles from the database
            roles = user.role if isinstance(user.role, list) else [user.role]
            valid_roles = [role for role in roles if role in ['driver', 'owner']]

            return Response({
                "message": "Login successful!",
                "roles": valid_roles
            }, status=status.HTTP_200_OK)

        logger.error("Invalid credentials for username: %s", username)
        return Response({
            "errors": {"username": ["Invalid username or password."]}
        }, status=status.HTTP_401_UNAUTHORIZED)
    
def home_view(request):
    return render(request, 'core/home.html')

def signup_view(request):
    return render(request, 'core/signup.html')

def login_view(request):
    return render(request, 'core/login.html')

# Driver Home View
@login_required
def driver_home_view(request):
    return render(request, 'core/book_parking_space.html')

# Owner Home View
@login_required
def owner_home_view(request):
    return render(request, 'core/add_parking_space.html')

@login_required
def role_selection_view(request):
    return render(request, 'core/role_selection.html')

@login_required
def role_redirect_view(request):
    if request.method == "POST":
        selected_role = request.POST.get("role")
        print(f"Received role: {selected_role}")  # Debugging: Check received role in terminal

        if selected_role == "Driver":
            return redirect("book_parking_space")
        elif selected_role == "Owner":
            return redirect("add_parking_space")

    # If no role was selected or it's a GET request, render the selection page again
    return render(request, "core/role_selection.html")