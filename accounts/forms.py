from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class SignupForm(UserCreationForm):

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Enter email"
            }
        )
    )

    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter username"
            }
        )
    )


    password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Enter password"
            }
        )
    )


    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Confirm password"
            }
        )
    )


    class Meta:

        model = User

        fields = [
            "username",
            "email",
            "password1",
            "password2",
        ]