from django.core.management.base import BaseCommand


from notification.daemon import AddressNotifyDaemon


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        daemon = AddressNotifyDaemon()
        daemon.run_forever()

