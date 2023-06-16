from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth.forms import UsernameField
from django.forms import EmailField


def validate_email(value):
    if User.objects.filter(email=value).exists():
        raise ValidationError('Email Already Exists')
    return value


class CustomUserCreationForm(UserCreationForm):
    email = EmailField(validators=[validate_email])

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        field_classes = {"username": UsernameField}
