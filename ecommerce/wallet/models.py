from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

# Create your models here.
class Wallet(models.Model) :
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=12,decimal_places=2,default = 0.00)

    def __str__(self) :
        return f'{self.user.username},s wallet'
    
class Wallet_transactions(models.Model) :
    TRANSACTION_TYPE = (

        ('add' , 'Add'),
        ('withdrawal','Withdrawal'),
        ('refund' , 'Refund') 
    )

    wallet = models.ForeignKey(Wallet,on_delete=models.CASCADE)
    type = models.CharField(max_length=10,choices=TRANSACTION_TYPE,blank=True)
    amount = models.DecimalField(max_digits=10,decimal_places=2)
    transaction_id = models.CharField(max_length=10,null=True,blank=True)
    description = models.CharField(max_length=255,blank=True)
    time_stamp = models.DateTimeField(auto_now_add=True)

@receiver(post_save,sender= User)
def Create_user_wallet(sender , instance, created , **kwargs):
    if created :
        Wallet.objects.create(user=instance)
        print(f'{instance.username} wallet createddd!!')