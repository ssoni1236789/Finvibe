from django.db import models
from django.contrib.auth.models import User

class BankAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    account_holder_name = models.CharField(max_length=255)
    bank_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50, unique=True)
    account_type = models.CharField(max_length=50, choices=[('savings', 'Savings'), ('current', 'Current')])
    ifsc_code = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.account_holder_name} - {self.bank_name}"

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source_account = models.ForeignKey(BankAccount, on_delete=models.SET_NULL, null=True, related_name='source_transactions')
    receiver_name = models.CharField(max_length=255)
    recipient_account = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('completed', 'Completed'), ('pending', 'Pending'), ('failed', 'Failed')], default='pending')
    transaction_type = models.CharField(max_length=10, choices=[('income', 'Income'), ('expense', 'Expense'), ('transfer', 'Transfer')], default='transfer')

    def __str__(self):
        return f"{self.source_account} -> {self.recipient_account} (${self.amount})"

class DeletedAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account_holder_name = models.CharField(max_length=255)
    bank_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50)
    account_type = models.CharField(max_length=50)
    ifsc_code = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    deletion_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Deleted: {self.account_holder_name} - {self.bank_name}"
    
    
    


