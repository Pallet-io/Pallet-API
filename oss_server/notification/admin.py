from django.contrib import admin

from .models import AddressNotification, AddressSubscription, LastSeenBlock, TxNotification, TxSubscription


class TxSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'tx_hash', 'callback_url']


class TxNotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'subscription_id', 'tx_hash', 'is_notified', 'notification_attempts', 'notification_time']

    def tx_hash(self, instance):
        return instance.subscription.tx_hash

    def subscription_id(self, instance):
        return str(instance.subscription.id)


class AddressSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'address', 'callback_url']


class AddressNotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'subscription_id_str', 'tx_hash', 'is_notified', 'notification_attempts', 'notification_time']

    def subscription_id_str(self, instance):
        return str(instance.subscription.id)


class LastSeenBlockAdmin(admin.ModelAdmin):
    list_display = ['id', 'block_hash']


admin.site.register(AddressNotification, AddressNotificationAdmin)
admin.site.register(AddressSubscription, AddressSubscriptionAdmin)
admin.site.register(LastSeenBlock, LastSeenBlockAdmin)
admin.site.register(TxNotification, TxNotificationAdmin)
admin.site.register(TxSubscription, TxSubscriptionAdmin)
