from django.contrib import admin
from django.urls import path
from banking import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.SignupPage, name='signup'),
    path('login/', views.LoginPage, name='login'),
    path('home/', views.HomePage, name='home'),
    path('logout/', views.LogoutPage, name='logout'),
    path('delete_account/<int:account_id>/', views.delete_account, name='delete_account'),
    path('transactions/', views.view_transactions, name='transactions'),
    path('accounts/', views.view_accounts, name='view_accounts'),
    path('transfer/', views.TransferPage, name='transfer'),
    path('add_account/', views.add_account, name='add_account'),
    path('expenses/', views.ExpensesPage, name='expenses'),
   
]