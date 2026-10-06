from django.contrib import admin
from django.utils import timezone
from .models import Book, Loan


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """Configuração do Book no Django Admin."""
    
    # Colunas exibidas na listagem
    list_display = ("title", "author", "isbn", "copies_total", "copies_available")
    
    # Campos pesquisáveis
    search_fields = ("title", "author", "isbn")
    
    # Campos somente leitura (calculados)
    readonly_fields = ("created_at",)


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    """Configuração do Loan no Django Admin."""
    
    list_display = ("book", "user", "borrowed_at", "due_date", "returned_at", "_is_overdue")
    list_filter = ("returned_at",)  # Filtro lateral
    search_fields = ("book__title", "user__username")  # Busca em relacionamentos
    actions = ("marcar_como_devolvido",)  # Ação customizada

    @admin.display(boolean=True, description="Atrasado")
    def _is_overdue(self, obj):
        """Exibe ícone de alerta se atrasado."""
        return obj.is_overdue

    @admin.action(description="Marcar como devolvido")
    def marcar_como_devolvido(self, request, queryset):
        """Ação em massa para marcar empréstimos como devolvidos."""
        updated = 0
        now = timezone.now()
        
        # Só marca os que ainda não foram devolvidos
        for loan in queryset.filter(returned_at__isnull=True):
            loan.returned_at = now
            loan.save(update_fields=["returned_at"])
            updated += 1
        
        # Mensagem de sucesso
        self.message_user(request, f"{updated} empréstimo(s) marcados como devolvidos.")