from django import forms

class ShopFilter (forms.Form):
    SORT_CHOICES = [
        ('', 'Select'),
        ('low_to_high', 'Price: Low To High'),
        ('high_to_low', 'Price: High To Low'),
        ('A-Z', 'Name: A-Z'),
        ('Z-A', 'Name: Z-A'),
    ]
    sort = forms.ChoiceField(choices=SORT_CHOICES , required=False,label='sort by')
