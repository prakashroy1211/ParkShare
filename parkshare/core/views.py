from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import CustomUserSerializer
from django.contrib.auth import authenticate, login, logout
import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import CustomUser

logger = logging.getLogger(__name__)

class RegisterView(APIView):
    def post(self, request):
        username = request.data.get("username")  # Email as username
        password = request.data.get("password")
        roles = request.data.get("role", [])

        # Ensure roles are stored as a list
        if isinstance(roles, str):  
            roles = [roles]
        roles = list(set(roles))  # Remove duplicates

        user = CustomUser.objects.filter(username=username).first()

        if user:
            # User exists, check if the provided password is correct
            if not user.check_password(password):
                return Response(
                    {
                        "error": "Incorrect password. You already have an account registered with another role."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            existing_roles = user.role if isinstance(user.role, list) else []
            
            # Check if the user is trying to register the same role
            if any(role in existing_roles for role in roles):
                return Response(
                    {"error": "You already have this role assigned to your account."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Add new roles
            new_roles = [role for role in roles if role not in existing_roles]
            user.role = existing_roles + new_roles
            user.save()

            return Response(
                {"message": "Roles updated successfully!", "roles": user.role},
                status=status.HTTP_200_OK,
            )

        # If user does not exist, create a new account
        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {"message": "User created successfully!", "roles": user.role},
                status=status.HTTP_201_CREATED,
            )

        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
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

def logout_view(request):
    logout(request)  # Ends the session
    return redirect('login')  # Redirect to login page

# Driver Home View
@login_required
def driver_home_view(request):
    return render(request, 'core/user_dashboard.html')

# Owner Home View
@login_required
def owner_home_view(request):
    return render(request, 'core/owner_dashboard.html')

@login_required
def role_selection_view(request):
    return render(request, 'core/role_selection.html')

@login_required
def role_redirect_view(request):
    if request.method == "POST":
        selected_role = request.POST.get("role")
        print(f"Received role: {selected_role}")  # Debugging: Check received role in terminal

        if selected_role == "Driver":
            return redirect("user_dashboard")
        elif selected_role == "Owner":
            return redirect("owner_dashboard")

    # If no role was selected or it's a GET request, render the selection page again
    return render(request, "core/role_selection.html")