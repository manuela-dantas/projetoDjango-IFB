from datetime import timedelta  # representa um intervalo de tempo (ex.: 14 dias)

from django.contrib import messages  # mensagens de retorno ("Empréstimo feito!")
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Book, Loan

LOAN_DAYS = 14  # prazo padrão de empréstimo, em dias


@login_required  # só usuários logados; os outros são mandados para o login
def book_list(request):
    """Mostra todos os livros do acervo."""
    books = Book.objects.all()
    # render junta o template com os dados; cada chave do dicionário vira uma variável no template
    return render(request, "catalogo/book_list.html", {"books": books})


@login_required
@require_POST  # recusa pedidos GET com erro 405: emprestar só por formulário
def borrow_book(request, book_id):
    """Cria um empréstimo do livro para o usuário logado."""
    # Busca o livro pelo id; se não existir, responde 404 (página não encontrada)
    book = get_object_or_404(Book, pk=book_id)

    # Regra 1: precisa haver cópia disponível
    if book.copies_available == 0:
        messages.error(request, f"Não há cópias disponíveis de “{book.title}”.")
        return redirect("catalogo:book_list")

    # Regra 2: a pessoa não pode estar com este mesmo livro ainda sem devolver
    already_has = book.loans.filter(user=request.user, returned_at__isnull=True).exists()
    if already_has:
        messages.warning(request, f"Você já está com “{book.title}”.")
        return redirect("catalogo:book_list")

    # Tudo certo: calcula o prazo e cria o empréstimo
    due_date = timezone.localdate() + timedelta(days=LOAN_DAYS)
    Loan.objects.create(book=book, user=request.user, due_date=due_date)
    messages.success(request, f"Empréstimo feito! Devolva “{book.title}” até {due_date:%d/%m/%Y}.")
    # Depois de um POST, sempre redirecionamos (padrão Post/Redirect/Get)
    return redirect("catalogo:my_loans")


@login_required
def my_loans(request):
    """Lista os empréstimos do usuário logado (ativos e devolvidos)."""
    # select_related("book") traz o livro na mesma consulta, evitando uma consulta extra por empréstimo
    loans = Loan.objects.filter(user=request.user).select_related("book")
    return render(request, "catalogo/my_loans.html", {"loans": loans})


@login_required
@require_POST
def return_book(request, loan_id):
    """Registra a devolução de um empréstimo do próprio usuário."""
    # user=request.user impede devolver o empréstimo de outra pessoa trocando o número na URL
    loan = get_object_or_404(Loan, pk=loan_id, user=request.user)

    if loan.returned_at:
        messages.info(request, "Este livro já tinha sido devolvido.")
    else:
        loan.mark_returned()  # regra de negócio que fica no model
        messages.success(request, f"“{loan.book.title}” devolvido. Obrigado!")
    return redirect("catalogo:my_loans")


@login_required
def admin_overdue_loans(request):
    """Lista empréstimos atrasados para a equipe administrativa."""
    if not request.user.is_staff:
        return redirect("catalogo:book_list")

    overdue_loans = Loan.objects.filter(returned_at__isnull=True, due_date__lt=timezone.localdate()).select_related("book", "user")
    return render(request, "catalogo/admin_overdue.html", {"overdue_loans": overdue_loans})


@login_required
def admin_book_borrowers(request, book_id):
    """Mostra quem está com cada livro atualmente."""
    if not request.user.is_staff:
        return redirect("catalogo:book_list")

    book = get_object_or_404(Book, pk=book_id)
    active_loans = book.loans.filter(returned_at__isnull=True).select_related("user")
    return render(request, "catalogo/admin_book_borrowers.html", {"book": book, "active_loans": active_loans})


@login_required
@require_POST
def admin_mark_returned(request, loan_id):
    """Permite registrar devolução pela área administrativa."""
    if not request.user.is_staff:
        return redirect("catalogo:book_list")

    loan = get_object_or_404(Loan, pk=loan_id)
    if not loan.returned_at:
        loan.mark_returned()
        messages.success(request, f"“{loan.book.title}” foi marcado como devolvido.")
    else:
        messages.info(request, "Este empréstimo já estava registrado como devolvido.")

    return redirect("catalogo:admin_overdue_loans")