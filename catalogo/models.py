from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Cast
from django.utils import timezone


class Book(models.Model):
    """Livro do acervo da biblioteca."""
    
    # Campos básicos
    title = models.CharField(max_length=255, verbose_name="Título")
    author = models.CharField(max_length=255, verbose_name="Autor")
    isbn = models.CharField(max_length=13, unique=True, verbose_name="ISBN")
    copies_total = models.PositiveIntegerField(default=1, verbose_name="Total de cópias")
    
    # Campo para upload de imagem (capa do livro)
    # blank=True: permite vazio no formulário
    # null=True: permite NULL no banco de dados
    # upload_to: subpasta onde as imagens serão salvas
    image = models.ImageField(
        upload_to='book_covers/', 
        blank=True, 
        null=True,
        verbose_name="Capa"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Cadastrado em")

    class Meta:
        ordering = ["title"]  # Ordena por título
        verbose_name = "Livro"
        verbose_name_plural = "Livros"

    def __str__(self):
        """Representação em texto do objeto."""
        return f"{self.title} — {self.author}"

    @property
    def copies_available(self):
        """Calcula quantas cópias estão disponíveis agora."""
        # Conta empréstimos ativos (returned_at é NULL)
        active_loans = self.loans.filter(returned_at__isnull=True).count()
        return max(self.copies_total - active_loans, 0)

class Loan(models.Model):
    """Empréstimo de um livro para um usuário."""

    # Relacionamentos (ForeignKey = chave estrangeira)
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="loans",
        verbose_name="Livro"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="loans",
        verbose_name="Usuário"
    )

    # Datas
    borrowed_at = models.DateTimeField(auto_now_add=True, verbose_name="Emprestado em")
    due_date = models.DateField(verbose_name="Devolver até")
    returned_at = models.DateTimeField(null=True, blank=True, verbose_name="Devolvido em")

    class Meta:
        ordering = ["-borrowed_at"]
        verbose_name = "Empréstimo"
        verbose_name_plural = "Empréstimos"


    def __str__(self):
        status = "devolvido" if self.returned_at else "emprestado"
        return f"{self.book.title} para {self.user.username} ({status})"

    @property
    def is_active(self):
        """Verifica se o empréstimo está ativo (não devolvido)."""
        return self.returned_at is None

    @property
    def is_overdue(self):
        """Verifica se o empréstimo está atrasado."""
        return self.is_active and timezone.localdate() > self.due_date

    def mark_returned(self):
        """Marca o empréstimo como devolvido."""
        if not self.returned_at:
            self.returned_at = timezone.now()
            self.save(update_fields=["returned_at"])