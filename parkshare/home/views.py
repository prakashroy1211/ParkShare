from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .forms import SignUpForm

def login_view(request):
    return LoginView.as_view()(request)

def home(request):
    return render(request, 'home/home.html')

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully! You can now log in.')
            return redirect('login')  # Redirect to login page after successful signup
    else:
        form = SignUpForm()

    return render(request, 'home/signup.html', {'form': form})