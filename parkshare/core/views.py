from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import CustomUserSerializer
from django.contrib.auth import authenticate, login
import logging
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.shortcuts import redirect

logger = logging.getLogger(__name__)

class RegisterView(APIView):
    def post(self, request):
        logger.info("Received data: %s", request.data)
        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Registration successful!"}, status=status.HTTP_201_CREATED)
        logger.error("Validation errors: %s", serializer.errors)
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        logger.info("Received data: %s", request.data)
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_authenticated:
            login(request, user)
            roles = []

            if user.role == 'driver':
                roles.append('Driver')
            if user.role == 'owner':
                roles.append('Owner')

            if roles:
                return Response({"message": "Login successful!", "roles": roles}, status=status.HTTP_200_OK)
            else:
                logger.error("User has no valid roles: %s", username)
                return Response({"errors": {"roles": ["User has no valid roles."]}}, status=status.HTTP_400_BAD_REQUEST)

        logger.error("Invalid credentials for username: %s", username)
        return Response({"errors": {"username": ["Invalid username or password."]}}, status=status.HTTP_401_UNAUTHORIZED)

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
    if request.method == 'POST':
        selected_role = request.POST.get('role')

        if selected_role == 'Driver':
            return redirect('core/book_parking_space.html')  # Redirect to Driver's home page
        elif selected_role == 'Owner':
            return redirect('core/add_parking_space.html')  # Redirect to Owner's home page
        else:
            return JsonResponse({'error': 'Invalid role selected'}, status=400)
    
    return JsonResponse({'error': 'Bad request'}, status=400)