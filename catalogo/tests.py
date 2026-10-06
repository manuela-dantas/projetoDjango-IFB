from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Book, Loan

User = get_user_model()


class LoanModelTests(TestCase):
    """Testes para o modelo Loan."""

    def setUp(self):
        """Prepara dados para os testes."""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.book = Book.objects.create(
            title='Livro Teste',
            author='Autor Teste',
            isbn='1234567890123',
            copies_total=1
        )

    def test_overdue_logic(self):
        """Testa se empréstimo atrasado é detectado corretamente."""
        # Cria empréstimo com data passada
        loan = Loan.objects.create(
            book=self.book,
            user=self.user,
            due_date=timezone.localdate() - timedelta(days=1)
        )
        self.assertTrue(loan.is_overdue)
        self.assertTrue(loan.is_active)

    def test_mark_returned_sets_timestamp(self):
        """Testa se marcar como devolvido define timestamp."""
        loan = Loan.objects.create(
            book=self.book,
            user=self.user,
            due_date=timezone.localdate() + timedelta(days=7)
        )
        
        self.assertIsNone(loan.returned_at)
        loan.mark_returned()
        self.assertIsNotNone(loan.returned_at)
        self.assertFalse(loan.is_active)

    def test_copies_available_counts_active_loans(self):
        """Testa cálculo de cópias disponíveis."""
        # Inicialmente tem 1 cópia disponível
        self.assertEqual(self.book.copies_available, 1)
        
        # Empresta o livro
        Loan.objects.create(
            book=self.book,
            user=self.user,
            due_date=timezone.localdate() + timedelta(days=7)
        )
        
        # Agora tem 0 cópias disponíveis
        self.assertEqual(self.book.copies_available, 0)


class AuthViewsTests(TestCase):
    """Testes para views de autenticação."""

    def test_logout_requires_post_and_redirects(self):
        """Testa se logout requer POST e redireciona."""
        user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')
        
        # POST deve funcionar
        response = self.client.post(reverse('catalogo:logout'))
        self.assertEqual(response.status_code, 302)  # Redirect
        
        # GET não deve funcionar (Django 5.x)
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('catalogo:logout'))
        self.assertEqual(response.status_code, 405)  # Method Not Allowed