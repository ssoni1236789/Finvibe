from django.contrib import admin
from .models import BankAccount, Transaction, DeletedAccount

@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('account_holder_name', 'bank_name', 'account_number', 'account_type', 'amount', 'user')
    list_filter = ('account_type', 'bank_name', 'user')
    search_fields = ('account_holder_name', 'account_number', 'bank_name')
    ordering = ('account_holder_name',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'source_account', 'receiver_name', 'amount', 'transaction_type', 'status', 'date')
    list_filter = ('transaction_type', 'status', 'date', 'user')
    search_fields = ('description', 'receiver_name', 'recipient_account')
    ordering = ('-date',)
    list_per_page = 25

@admin.register(DeletedAccount)
class DeletedAccountAdmin(admin.ModelAdmin):
    list_display = ('account_holder_name', 'bank_name', 'account_number', 'account_type', 'amount', 'deletion_date', 'user')
    list_filter = ('account_type', 'bank_name', 'deletion_date', 'user')
    search_fields = ('account_holder_name', 'account_number', 'bank_name')
    ordering = ('-deletion_date',)
    list_per_page = 25