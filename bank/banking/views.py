from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.serializers import serialize
import json
from .models import BankAccount, Transaction, DeletedAccount
from .forms import BankAccountForm, TransferForm, ExpenseForm
from django.http import HttpResponse

@login_required(login_url='login')
def HomePage(request):
    accounts = BankAccount.objects.filter(user=request.user)
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    total_balance = sum(account.amount for account in accounts)

    # Prepare account-specific transaction data
    account_transactions = []
    for account in accounts:
        # Incoming: income transactions and transfers where this account is the recipient
        incoming = transactions.filter(
            source_account=account,
            transaction_type='income'
        ) | Transaction.objects.filter(
            recipient_account=account.account_number,
            transaction_type='transfer',
            status='completed'
        )
        # Outgoing: expense and transfer transactions where this account is the source
        outgoing = transactions.filter(
            source_account=account,
            transaction_type__in=['expense', 'transfer']
        )
        # Combine and sort by date
        account_txs = (incoming | outgoing).order_by('date')
        tx_data = []
        for tx in account_txs:
            amount = tx.amount
            if tx.transaction_type == 'income' or tx.recipient_account == account.account_number:
                direction = 'incoming'
            else:
                direction = 'outgoing'
            tx_data.append({
                'date': tx.date.isoformat(),
                'amount': float(abs(amount)),
                'direction': direction
            })
        account_transactions.append({
            'account_id': account.id,
            'account_name': f"{account.account_holder_name} - {account.bank_name}",
            'transactions': tx_data
        })

    transactions_json = json.dumps(account_transactions)
    return render(request, 'home.html', {
        'total_balance': total_balance,
        'transactions': transactions,
        'transactions_json': transactions_json,
        'accounts': accounts
    })

def SignupPage(request):
    if request.method == 'POST':
        uname = request.POST.get('username')
        email = request.POST.get('email')
        pass1 = request.POST.get('password1')
        pass2 = request.POST.get('password2')
        if pass1 != pass2:
            messages.error(request, "Passwords do not match!")
            return redirect('signup')
        try:
            my_user = User.objects.create_user(uname, email, pass1)
            my_user.save()
            messages.success(request, "Account created successfully! Please log in.")
            return redirect('login')
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('signup')
    return render(request, 'signup.html')

def LoginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        pass1 = request.POST.get('pass')
        user = authenticate(request, username=username, password=pass1)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Username or Password is incorrect!")
            return redirect('login')
    return render(request, 'login.html')

@login_required(login_url='login')
def LogoutPage(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def view_accounts(request):
    accounts = BankAccount.objects.filter(user=request.user)
    return render(request, 'accounts.html', {'accounts': accounts})

@login_required(login_url='login')
def view_transactions(request):
    accounts = BankAccount.objects.filter(user=request.user)
    selected_account_id = request.GET.get('account_id')
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    
    if selected_account_id:
        try:
            selected_account = BankAccount.objects.get(id=selected_account_id, user=request.user)
            transactions = transactions.filter(source_account=selected_account)
        except BankAccount.DoesNotExist:
            selected_account = None
    else:
        selected_account = None

    return render(request, 'transactions.html', {
        'accounts': accounts,
        'transactions': transactions,
        'selected_account': selected_account
    })

@login_required(login_url='login')
def TransferPage(request):
    if request.method == 'POST':
        form = TransferForm(request.POST, user=request.user)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.transaction_type = 'transfer'
            source_account = transaction.source_account
            transfer_type = form.cleaned_data['transfer_type']
            amount = transaction.amount

            if source_account.amount >= amount:
                source_account.amount -= amount
                source_account.save()

                if transfer_type == 'internal':
                    recipient_account = form.cleaned_data['recipient_account']
                    recipient_account.amount += amount
                    recipient_account.save()
                    transaction.receiver_name = recipient_account.account_holder_name
                    transaction.recipient_account = recipient_account.account_number
                    transaction.status = 'completed'
                else:
                    recipient_account_no = form.cleaned_data['recipient_account_no']
                    try:
                        recipient_account = BankAccount.objects.get(account_number=recipient_account_no)
                        recipient_account.amount += amount
                        recipient_account.save()
                        transaction.receiver_name = form.cleaned_data['receiver_name']
                        transaction.recipient_account = recipient_account_no
                        transaction.status = 'completed'
                    except BankAccount.DoesNotExist:
                        transaction.status = 'failed'
                        transaction.save()
                        messages.error(request, "Recipient account not found!")
                        return redirect('transfer')

                transaction.save()
                messages.success(request, "Transfer completed successfully!")
                return redirect('transactions')
            else:
                transaction.status = 'failed'
                transaction.save()
                messages.error(request, "Insufficient funds!")
                return redirect('transfer')
        else:
            messages.error(request, "Invalid form data. Please check the details.")
            return render(request, 'transfer.html', {'form': form})
    else:
        form = TransferForm(user=request.user)
    return render(request, 'transfer.html', {'form': form})

@login_required(login_url='login')
def add_account(request):
    if request.method == "POST":
        form = BankAccountForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.user = request.user
            account.save()
            messages.success(request, "Bank account added successfully!")
            return redirect('view_accounts')
        else:
            messages.error(request, "Error adding account. Please check the details.")
    else:
        form = BankAccountForm()
    return render(request, 'add_account.html', {'form': form})

@login_required(login_url='login')
def delete_account(request, account_id):
    account = BankAccount.objects.get(id=account_id, user=request.user)
    if request.method == "POST":
        # Save deleted account details
        DeletedAccount.objects.create(
            user=request.user,
            account_holder_name=account.account_holder_name,
            bank_name=account.bank_name,
            account_number=account.account_number,
            account_type=account.account_type,
            ifsc_code=account.ifsc_code,
            amount=account.amount
        )
        # Delete the account
        account.delete()
        messages.success(request, "Account deleted successfully!")
        return redirect('view_accounts')
    return render(request, 'delete_account.html', {'account': account})

@login_required(login_url='login')
def ExpensesPage(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            source_account = transaction.source_account
            
            # Validate amount and update source account
            if transaction.transaction_type == 'expense' and source_account.amount >= abs(transaction.amount):
                source_account.amount -= abs(transaction.amount)
                source_account.save()
                transaction.status = 'completed'
                transaction.receiver_name = "Expense"
                transaction.recipient_account = "N/A"
                transaction.save()
                messages.success(request, "Expense recorded successfully!")
                return redirect('expenses')
            elif transaction.transaction_type == 'income':
                source_account.amount += transaction.amount
                source_account.save()
                transaction.status = 'completed'
                transaction.receiver_name = "Income"
                transaction.recipient_account = "N/A"
                transaction.save()
                messages.success(request, "Income recorded successfully!")
                return redirect('expenses')
            else:
                transaction.status = 'failed'
                transaction.save()
                messages.error(request, "Insufficient funds for this expense!")
                return redirect('expenses')
    else:
        form = ExpenseForm()
        form.fields['source_account'].queryset = BankAccount.objects.filter(user=request.user)

    transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    total_balance = sum(account.amount for account in BankAccount.objects.filter(user=request.user))
    income = sum(t.amount for t in transactions if t.amount > 0)
    expenses = sum(abs(t.amount) for t in transactions if t.amount < 0)
    return render(request, 'expenses.html', {
        'form': form,
        'total_balance': total_balance,
        'income': income,
        'expenses': expenses,
        'transactions': transactions
    })