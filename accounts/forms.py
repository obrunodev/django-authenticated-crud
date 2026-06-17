from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="Endereço de E-mail",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "exemplo@email.com",
            }
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")
