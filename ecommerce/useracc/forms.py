# from django import forms
# from django.contrib.auth.models import User

# class RegisterForm (forms.Form) :
#     username = forms.CharField(max_length=150,widget=forms.TextInput(attrs={'class':'form-control','id':'name','placeholder':'enter a name'}))
#     email = forms.EmailField(widget=forms.EmailInput(attrs={'class':'form-control','id':'email','placeholder':'email'}))
#     mobile = forms.CharField(max_length=12,widget=forms.TextInput(attrs={'class':'form-control','id':'mob','placeholder':'ph'}))
#     password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control','id':'pass1','placeholder':'password 1'}))
#     confirmpassword = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control','id':'pass1','placeholder':'password 2'}))

#     def clean(self) :
#         cleaned_data = super().clean()
#         username = self.cleaned_data['username']
#         password = cleaned_data.get('password')
#         confirmpassword = cleaned_data.get('confirmpassword')

#         if password and confirmpassword and password != confirmpassword:
#             self.add_error('confirmpassword','pass do not match')

#         if not username :
#             self.add_error('username','name field is needed')

#         return cleaned_data

#     def process_registration(self):
#         if self.is_valid():
#             username = self.cleaned_data['username']
#             email = self.cleaned_data['email']
#             password = self.cleaned_data['password']
#             return {'username': username, 'email': email , 'password': password}
