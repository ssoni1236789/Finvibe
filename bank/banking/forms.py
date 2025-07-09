from django import forms
from .models import BankAccount, Transaction

class BankAccountForm(forms.ModelForm):
    class Meta:
        model = BankAccount
        fields = ['account_holder_name', 'bank_name', 'account_number', 'account_type', 'ifsc_code', 'amount']

class TransferForm(forms.ModelForm):
    transfer_type = forms.ChoiceField(choices=[('internal', 'Internal'), ('external', 'External')])
    recipient_account = forms.ModelChoiceField(queryset=BankAccount.objects.all(), required=False)
    recipient_account_no = forms.CharField(max_length=50, required=False)
    receiver_name = forms.CharField(max_length=100, required=False)
    sender_cvv = forms.CharField(max_length=4, required=False)

    class Meta:
        model = Transaction
        fields = ['source_account', 'transfer_type', 'recipient_account', 'recipient_account_no', 'receiver_name', 'amount', 'sender_cvv']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['source_account'].queryset = BankAccount.objects.filter(user=user)
            self.fields['recipient_account'].queryset = BankAccount.objects.exclude(user=user)

    def clean(self):
        cleaned_data = super().clean()
        transfer_type = cleaned_data.get('transfer_type')
        recipient_account = cleaned_data.get('recipient_account')
        recipient_account_no = cleaned_data.get('recipient_account_no')
        receiver_name = cleaned_data.get('receiver_name')
        sender_cvv = cleaned_data.get('sender_cvv')
        amount = cleaned_data.get('amount')

        if transfer_type == 'internal':
            if not recipient_account:
                self.add_error('recipient_account', "Recipient account is required for internal transfers.")
        else:
            if not recipient_account_no:
                self.add_error('recipient_account_no', "Recipient account number is required for external transfers.")
            if not receiver_name:
                self.add_error('receiver_name', "Receiver name is required for external transfers.")
            if not sender_cvv:
                self.add_error('sender_cvv', "CVV is required for external transfers.")

        if amount and amount <= 0:
            self.add_error('amount', "Amount must be greater than zero.")

        return cleaned_data

class ExpenseForm(forms.ModelForm):
    transaction_type = forms.ChoiceField(choices=[('income', 'Income'), ('expense', 'Expense')])
    amount = forms.DecimalField(max_digits=10, decimal_places=2)
    description = forms.CharField(max_length=200)

    class Meta:
        model = Transaction
        fields = ['source_account', 'description', 'amount', 'transaction_type']

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        transaction_type = self.cleaned_data['transaction_type']
        if transaction_type == 'expense' and amount > 0:
            return -amount
        elif transaction_type == 'income' and amount < 0:
            return abs(amount)
        return amount