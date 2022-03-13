from django.contrib import admin

from sortiment.transactions.models import CreditTransaction, ItemTransferTransaction, ItemPurchaseTransaction, \
    ItemRestockTransaction


@admin.register(CreditTransaction)
class CreditTransactionAdmin(admin.ModelAdmin):
    pass


@admin.register(ItemTransferTransaction)
class ItemTransferTransactionAdmin(admin.ModelAdmin):
    pass


@admin.register(ItemPurchaseTransaction)
class ItemPurchaseTransactionAdmin(admin.ModelAdmin):
    pass


@admin.register(ItemRestockTransaction)
class ItemRestockTransactionAdmin(admin.ModelAdmin):
    pass
