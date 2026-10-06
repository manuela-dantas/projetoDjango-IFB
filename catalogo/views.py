from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Book, Loan


# ========== VIEWS PARA USUÁRIOS COMUNS ==========

@login_required
def book_list(request):
    """Lista todos os livros com quantidade disponível."""
    # Anotação: adiciona campo calculado 'active_loans' em cada livro
    books = Book.objects.annotate(
        active_loans=Count('loans', filter=Q(loans__returned_at__isnull=True))
    )
    return render(request, 'catalogo/book_list.html', {'books': books})


@login_required
def borrow_book(request, book_id):
    """Permite emprestar um livro."""
    if request.method != 'POST':
        return redirect('catalogo:book_list')
    
    book = get_object_or_404(Book, pk=book_id)
    
    # Verifica se há cópias disponíveis
    if book.copies_available <= 0:
        messages.error(request, f"Não há cópias disponíveis de '{book.title}'.")
        return redirect('catalogo:book_list')
    
    # Cria o empréstimo com prazo de 14 dias
    due_date = timezone.localdate() + timedelta(days=14)
    Loan.objects.create(
        book=book,
        user=request.user,
        due_date=due_date
    )
    
    messages.success(
        request, 
        f"Livro '{book.title}' emprestado com sucesso! Devolva até {due_date.strftime('%d/%m/%Y')}."
    )
    return redirect('catalogo:book_list')


@login_required
def return_book(request, loan_id):
    """Permite devolver um livro."""
    if request.method != 'POST':
        return redirect('catalogo:my_loans')
    
    loan = get_object_or_404(Loan, pk=loan_id)
    
    # Verifica se é o dono do empréstimo
    if loan.user != request.user:
        messages.error(request, "Você não pode devolver um empréstimo de outro usuário.")
        return redirect('catalogo:my_loans')
    
    # Verifica se já foi devolvido
    if loan.returned_at:
        messages.warning(request, "Este livro já foi devolvido.")
        return redirect('catalogo:my_loans')
    
    # Marca como devolvido
    loan.mark_returned()
    messages.success(request, f"Livro '{loan.book.title}' devolvido com sucesso!")
    return redirect('catalogo:my_loans')


@login_required
def my_loans(request):
    """Lista todos os empréstimos do usuário logado."""
    loans = Loan.objects.filter(user=request.user).select_related('book')
    return render(request, 'catalogo/my_loans.html', {'loans': loans})

# ========== VIEWS PARA ADMINISTRADORES (STAFF) ==========

def _is_staff(user):
    """Verifica se o usuário é staff (administrador)."""
    return user.is_staff


@login_required
@user_passes_test(_is_staff)
def admin_overdue_loans(request):
    """Lista todos os empréstimos atrasados."""
    today = timezone.localdate()
    loans = Loan.objects.filter(
        returned_at__isnull=True,  # Ainda não devolvidos
        due_date__lt=today  # Data de devolução passou
    ).select_related('book', 'user')
    
    return render(request, 'catalogo/admin_overdue.html', {'loans': loans})


@login_required
@user_passes_test(_is_staff)
def admin_book_borrowers(request, book_id):
    """Mostra quem está com um livro específico."""
    book = get_object_or_404(Book, pk=book_id)
    active_loans = book.loans.filter(returned_at__isnull=True).select_related('user')
    
    return render(request, 'catalogo/admin_book_borrowers.html', {
        'book': book,
        'active_loans': active_loans
    })


@login_required
@user_passes_test(_is_staff)
def admin_mark_returned(request, loan_id):
    """Permite admin marcar empréstimo como devolvido."""
    if request.method != 'POST':
        return redirect('catalogo:admin_overdue_loans')
    
    loan = get_object_or_404(Loan, pk=loan_id)
    
    if loan.returned_at:
        messages.warning(request, "Este empréstimo já foi marcado como devolvido.")
    else:
        loan.mark_returned()
        messages.success(request, f"Empréstimo de '{loan.book.title}' marcado como devolvido.")
    
    return redirect('catalogo:admin_overdue_loans')