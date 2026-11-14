from django import forms

from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["category", "name", "description", "price", "stock", "image"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if len(name) < 3:
            raise forms.ValidationError("Product name must be at least 3 characters.")
        return name

    def clean_stock(self):
        stock = self.cleaned_data["stock"]
        if stock > 100_000:
            raise forms.ValidationError("Stock level looks unrealistic. Please check it.")
        return stock
