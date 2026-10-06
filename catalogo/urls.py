from django.urls import path
from . import views

# Namespace permite referenciar URLs como 'catalogo:book_list'
app_name = 'catalogo'

urlpatterns = [
    # URLs para usuários comuns
    path('', views.book_list, name='book_list'),
    path('borrow/<int:book_id>/', views.borrow_book, name='borrow_book'),
    path('return/<int:loan_id>/', views.return_book, name='return_book'),
    path('me/loans/', views.my_loans, name='my_loans'),
    
    # URLs para administradores (prefixo /staff/)
    path('staff/overdue/', views.admin_overdue_loans, name='admin_overdue_loans'),
    path('staff/book/<int:book_id>/borrowers/', views.admin_book_borrowers, name='admin_book_borrowers'),
    path('staff/loan/<int:loan_id>/return/', views.admin_mark_returned, name='admin_mark_returned'),
]