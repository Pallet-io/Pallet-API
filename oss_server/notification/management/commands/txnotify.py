from django.core.management.base import BaseCommand

from notification.daemon import TxNotifyDaemon


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        daemon = TxNotifyDaemon()
        daemon.run_forever()
