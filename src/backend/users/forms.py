from django import forms
from django.conf import settings
from .models import User


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number', 'date_of_birth',
            'profile_image', 'department', 'position', 'bio',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country'
        ]

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        # Add simple normalization or validation if needed
        return phone
