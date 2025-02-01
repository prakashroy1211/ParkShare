from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import CustomUserSerializer
from django.contrib.auth import authenticate, login
import logging

def home_view(request):
    return render(request, 'core/home.html')

logger = logging.getLogger(__name__)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CustomUserSerializer
import logging

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
        if user is not None:
            login(request, user)
            return Response({"message": "Login successful!"}, status=status.HTTP_200_OK)
        logger.error("Invalid credentials for username: %s", username)
        return Response({"errors": {"username": ["Invalid username or password."]}}, status=status.HTTP_401_UNAUTHORIZED)
    
from django.shortcuts import render

def signup_view(request):
    return render(request, 'core/signup.html')

def login_view(request):
    return render(request, 'core/login.html')