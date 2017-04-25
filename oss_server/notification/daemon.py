import logging
import time

from django.conf import settings
from django.db import connections
from django.db.models import F
from django.utils import timezone

from gcoinrpc import connect_to_remote
import requests

from notification.models import AddressSubscription, TxSubscription
from notification.models import AddressNotification, TxNotification
from notification.models import LastSeenBlock


logger = logging.getLogger(__name__)
RETRY_TIMES = 5
SLEEP_TIME = 5

def close_old_connections():
    for conn in connections.all():
        conn.close_if_unusable_or_obsolete()

def get_rpc_connection():
    return connect_to_remote(settings.GCOIN_RPC['user'],
                             settings.GCOIN_RPC['password'],
                             settings.GCOIN_RPC['host'],
                             settings.GCOIN_RPC['port'])

class GcoinRPCMixin(object):

    def __init__(self):
        self.conn = get_rpc_connection()

    def get_block(self, block_hash):
        return self.conn.getblock(block_hash)

    def get_best_block(self):
        return self.get_block(self.conn.getbestblockhash())

    def get_transaction(self, tx_hash):
        return self.conn.getrawtransaction(tx_hash)


class TxNotifyDaemon(GcoinRPCMixin):

    def __init__(self):
        super(TxNotifyDaemon, self).__init__()
        self.last_seen_block = None

    def call_request(self, post_data, notification):
        headers = {'content-type': "application/x-www-form-urlencoded"}

        try:
            response = requests.post(notification.subscription.callback_url,
                              headers=headers,
                              data=post_data
                              )
            if response.status_code == 200:
                TxNotification.objects.filter(id=notification.id).update(
                    is_notified=True,
                    notification_attempts=F('notification_attempts') + 1,
                    notification_time=timezone.now()
                )
            else:
                TxNotification.objects.filter(id=notification.id).update(
                    notification_attempts=F('notification_attempts') + 1,
                )
        except Exception as e:
            logger.error("Request url: {}".format(notification.subscription.callback_url))
            logger.error("Notification id: {}".format(notification.id))
            try:
                TxNotification.objects.filter(id=notification.id).update(
                    notification_attempts=F('notification_attempts') + 1,
                )
            except Exception as e:
                logger.error(e)

    def start_notify(self, notifications):
        if notifications.count() == 0:
            return

        for notification in notifications:
            post_data = {
                'notification_id': notification.id,
                'subscription_id': notification.subscription.id,
                'tx_hash': notification.subscription.tx_hash,
            }
            self.call_request(post_data, notification)

    def run_forever(self, test=False):

        while True:
            try:
                best_block = self.get_best_block()

                if self.last_seen_block is None or self.last_seen_block['hash'] != best_block['hash']:

                    new_notifications = []
                    tx_subscriptions = TxSubscription.objects.filter(txnotification=None)
                    for tx_subscription in tx_subscriptions:
                        logger.debug('check tx hash: {}'.format(tx_subscription.tx_hash))
                        tx = self.get_transaction(tx_subscription.tx_hash)
                        if hasattr(tx, 'confirmations') and tx.confirmations >= tx_subscription.confirmation_count:
                            new_notifications.append(TxNotification(subscription=tx_subscription))

                    TxNotification.objects.bulk_create(new_notifications)

                notifications = TxNotification.objects.filter(is_notified=False,
                                                              notification_attempts__lt=RETRY_TIMES)
                self.start_notify(notifications)
                self.last_seen_block = best_block
            except Exception as e:
                logger.error(e)

            if test:
                return

            close_old_connections()
            time.sleep(SLEEP_TIME)


class AddressNotifyDaemon(GcoinRPCMixin):

    def call_request(self, post_data, notification):
        headers = {'content-type': "application/x-www-form-urlencoded"}

        try:
            response = requests.post(notification.subscription.callback_url,
                                     headers=headers,
                                     data=post_data
                                     )
            if response.status_code == 200:
                AddressNotification.objects.filter(id=notification.id).update(
                    is_notified=True,
                    notification_attempts=F('notification_attempts') + 1,
                    notification_time=timezone.now()
                )
            else:
                AddressNotification.objects.filter(id=notification.id).update(
                    notification_attempts=F('notification_attempts') + 1,
                )
        except Exception as e:
            logger.error(e)
            logger.error("Request url: {}".format(notification.subscription.callback_url))
            logger.error("Notification id: {}".format(notification.id))
            try:
                AddressNotification.objects.filter(id=notification.id).update(
                    notification_attempts=F('notification_attempts') + 1,
                )
            except Exception as e:
                logger.error(e)

    def start_notify(self):

        notifications = AddressNotification.objects.filter(is_notified=False, notification_attempts__lt=RETRY_TIMES).prefetch_related('subscription')
        notifications = list(notifications)

        for notification in notifications:
            post_data = {
                'notification_id': notification.id,
                'subscription_id': notification.subscription.id,
                'tx_hash': notification.tx_hash,
            }

            self.call_request(post_data, notification)

    def run_forever(self):

        while True:
            try:
                # get new blocks since last round
                new_blocks = self.get_new_blocks()
                if new_blocks:
                    # create a address -> txs map from new blocks
                    for block in new_blocks:
                        addr_txs_map = self.create_address_txs_map(block)
                        if bool(addr_txs_map):
                            # create AddressNotification instance in database
                            self.create_notifications(addr_txs_map)
                            self.start_notify()
                        self.set_last_seen_block(block['hash'])
            except Exception as e:
                logger.error(e)

            close_old_connections()
            time.sleep(SLEEP_TIME)

    def get_new_blocks(self):
        """
        Get new blocks since last update
        """
        last_seen_block = self.get_last_seen_block()
        best_block = self.get_best_block()

        if last_seen_block['confirmations'] < 1:
            # fork happened, find the branching point and set it as last seen block
            block = last_seen_block
            while block['confirmations'] < 1:
                block = self.get_block(block['previousblockhash'])
            last_seen_block = block

        # find all new blocks since last seen block in main chain
        block = best_block
        new_blocks = []
        if block['hash'] == last_seen_block['hash']:
            return new_blocks

        while block['hash'] != last_seen_block['hash']:
            new_blocks.append(block)
            block = self.get_block(block['previousblockhash'])
        return new_blocks[::-1]

    def create_address_txs_map(self, block):
        addr_txs_map = {}
        # Note: this for loop can be optimized if core supports rpc to get all tx in a block
        try:
            for tx_hash in block['tx']:
                tx = self.get_transaction(tx_hash)

                # find all the addresses that related to this tx
                related_addresses = self.get_related_addresses(tx)
                for address in related_addresses:
                    if address in addr_txs_map:
                        addr_txs_map[address].append(tx)
                    else:
                        addr_txs_map[address] = [tx]
        except Exception as e:
            logger.error(e)

        return addr_txs_map

    def create_notifications(self, addr_txs_map):
        try:
            subscriptions = AddressSubscription.objects.all()
            new_notifications = []

            # Only the address that is in addr_txs_map and subscription needs to be notified,
            # so iterate through the small one is more efficient
            if len(addr_txs_map) < subscriptions.count():
                for address, txs in addr_txs_map.iteritems():
                    for tx in txs:
                        for subscription in subscriptions.filter(address=address):
                            new_notifications.append(AddressNotification(subscription=subscription, tx_hash=tx.txid))
            else:
                for subscription in subscriptions:
                    if subscription.address in addr_txs_map:
                        for tx in addr_txs_map[subscription.address]:
                            new_notifications.append(AddressNotification(subscription=subscription, tx_hash=tx.txid))

            AddressNotification.objects.bulk_create(new_notifications)
        except Exception as e:
            logger.error(e)

    def get_related_addresses(self, tx):
        if tx.type == 'NORMAL' and 'coinbase' in tx.vin[0]:
            # this tx is the first tx of every block, just skip
            return []

        addresses = []
        # addresses in vin
        for vin in tx.vin:
            if 'coinbase' not in vin:
                prev_vout = self.get_prev_vout(vin['txid'], vin['vout'])
                addresses.extend(self.get_address_from_vout(prev_vout))

        # addresses in vout
        for vout in tx.vout:
            addresses.extend(self.get_address_from_vout(vout))

        return list(set(addresses))

    def get_prev_vout(self, tx_hash, n):
        tx = self.get_transaction(tx_hash)
        return tx.vout[n]

    def get_address_from_vout(self, vout):
        script_pub_key = vout['scriptPubKey']
        return script_pub_key.get('addresses', [])

    def set_last_seen_block(self, block_hash):
        try:
            lastSeenBlock = LastSeenBlock.objects.filter(name='AddressNotifyDaemon').first()
            lastSeenBlock.name = 'AddressNotifyDaemon'
            lastSeenBlock.block_hash = block_hash
            lastSeenBlock.save()
        except Exception as e:
            logger.error(e)

    def get_last_seen_block(self):
        try:
            last_block = LastSeenBlock.objects.filter(name='AddressNotifyDaemon').first()
            if last_block:
                return self.conn.getblock(last_block.block_hash)
            else:
                genesis_block = self.conn.getblock(self.conn.getblockhash(0))
                LastSeenBlock.objects.create(name='AddressNotifyDaemon', block_hash=genesis_block['hash'])
                return genesis_block
        except LastSeenBlock.DoesNotExist as e:
            logger.error(e)
