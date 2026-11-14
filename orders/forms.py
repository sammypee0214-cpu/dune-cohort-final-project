from django import forms

from .models import Order


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["shipping_name", "shipping_address", "phone"]
        widgets = {"shipping_address": forms.Textarea(attrs={"rows": 3})}

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        digits = [ch for ch in phone if ch.isdigit()]
        if len(digits) < 7:
            raise forms.ValidationError("Enter a valid phone number (at least 7 digits).")
        return phone
