
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import SignupForm

from patients.models import Patient


def home(request):

    return render(
        request,
        "home.html"
    )


def signup_view(request):

    if request.method == "POST":

        form = SignupForm(request.POST)

        if form.is_valid():

            user = form.save()

            login(
                request,
                user
            )

            messages.success(
                request,
                "Account created successfully."
            )

            return redirect(
                "dashboard"
            )

        else:

            print(form.errors)

            messages.error(
                request,
                "Please correct the errors below."
            )

    else:

        form = SignupForm()

    return render(
        request,
        "accounts/signup.html",
        {
            "form": form
        }
    )


def login_view(request):

    if request.method == "POST":

        username = request.POST.get(
            "username"
        )

        password = request.POST.get(
            "password"
        )

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(
                request,
                user
            )

            messages.success(
                request,
                "Welcome back."
            )

            return redirect(
                "dashboard"
            )

        else:

            messages.error(
                request,
                "Invalid username or password."
            )

    return render(
        request,
        "accounts/login.html"
    )


def logout_view(request):

    logout(request)

    messages.success(
        request,
        "You have logged out successfully."
    )

    return redirect(
        "home"
    )

@login_required
def dashboard(request):

    patients = Patient.objects.order_by("-created_at")

    context = {
        "patients_count": patients.count(),
        "patients": patients[:5],
    }

    return render(
        request,
        "dashboard.html",
        context
    )

