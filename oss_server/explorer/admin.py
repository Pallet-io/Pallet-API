from django.contrib import admin
from .models import Address, Block, Datadir, Tx, TxIn, TxOut


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    pass


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ('hash', 'height', 'in_longest')
    list_filter = ('in_longest',)
    search_fields = ('hash', '=height')


@admin.register(Datadir)
class DatadirAdmin(admin.ModelAdmin):
    pass


@admin.register(Tx)
class TxAdmin(admin.ModelAdmin):
    pass


@admin.register(TxIn)
class TxInAdmin(admin.ModelAdmin):
    pass


@admin.register(TxOut)
class TxOutAdmin(admin.ModelAdmin):
    pass
