from django.core.management.base import BaseCommand

from explorer.update_db import BlockUpdateDaemon

class Command(BaseCommand):
    help = 'Update explorer blocks'

    def handle(self, *args, **kwargs):
        daemon = BlockUpdateDaemon()
        daemon.run_forever()
