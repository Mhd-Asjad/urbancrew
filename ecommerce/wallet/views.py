from django.shortcuts import render , redirect , get_list_or_404
from django.contrib.auth.decorators import login_required
from django import forms
from django.utils.crypto import get_random_string
from .models import *
# Create your views here.


class AddFundForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0, max_value=10000, label="Amount")


def wallet_view(request):
    if request.user.is_authenticated :
        wallet = Wallet.objects.get(user = request.user)
        transactions = Wallet_transactions.objects.filter(wallet= wallet).order_by('-time_stamp')
        context = {

            'wallet' : wallet,
            'transactions' : transactions,
        }

        return render(request,'wallet.html',context)
    
    else : 

        return redirect('user_login')
        