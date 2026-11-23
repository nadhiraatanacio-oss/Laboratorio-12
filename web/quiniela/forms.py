from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Sala


class RegistroForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username",)


class SalaForm(forms.ModelForm):
    class Meta:
        model = Sala
        fields = ("nombre",)
        labels = {"nombre": "Nombre de la sala"}


class UnirseForm(forms.Form):
    codigo = forms.CharField(max_length=8, label="Código de invitación")

    def clean_codigo(self):
        codigo = self.cleaned_data["codigo"].strip().upper()
        if not Sala.objects.filter(codigo=codigo).exists():
            raise forms.ValidationError("No existe una sala con ese código.")
        return codigo
