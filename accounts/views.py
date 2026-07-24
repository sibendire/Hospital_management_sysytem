from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages

from .forms import SignupForm


def signup_view(request):

    if request.method == 'POST':

        form = SignupForm(request.POST)

        if form.is_valid():

            user = form.save()

            login(request, user)

            messages.success(
                request,
                "Signup successful!"
            )

            return redirect('dashboard')

    else:
        form = SignupForm()


    return render(
        request,
        'accounts/signup.html',
        {'form': form}
    )



def login_view(request):

    if request.method == 'POST':

        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect('dashboard')

        else:

            messages.error(
                request,
                "Invalid username or password"
            )


    return render(
        request,
        'accounts/login.html'
    )



def logout_view(request):

    logout(request)

    return redirect('login')



# ADD THIS FUNCTION
def dashboard(request):

    return render(
        request,
        'accounts/dashboard.html'
    )