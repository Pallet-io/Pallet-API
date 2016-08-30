import logging
import time
import urllib

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from gcoinrpc import connect_to_remote
from gcoinrpc.exceptions import InvalidAddressOrKey
from tornado import ioloop
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

from notification.models import AddressSubscription, TxSubscription
from notification.models import AddressNotification, TxNotification
from notification.models import LastSeenBlock


logger = logging.getLogger(__name__)
RETRY_TIMES = 5
SLEEP_TIME = 5

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

    def _get_callback_func(self, notification, total):
        def callback(response):
            self.count = self.count + 1
            logger.debug("-"*20)
            logger.debug("Request url: {}".format(response.request.url))
            logger.debug("Request effective url: {}".format(response.effective_url))
            logger.debug("Response code: {}".format(response.code))
            logger.debug("Notification id: {}".format(notification.id))
            if response.code == 200:
                TxNotification.objects.filter(id=notification.id).update(
                     is_notified=True,
                     notification_attempts=F('notification_attempts') + 1,
                     notification_time=timezone.now()
                )
            else:
                TxNotification.objects.filter(id=notification.id).update(
                     notification_attempts=F('notification_attempts') + 1,
                )

            if self.count == total:
                ioloop.IOLoop.instance().stop()
        return callback

    def start_notify(self, notifications):
        if notifications.count() == 0:
            return
        self.count = 0
        client = AsyncHTTPClient()
        headers = {'content-type': "application/x-www-form-urlencoded"}
        total = notifications.count()

        for notification in notifications:
            post_data = {
                'notification_id': notification.id,
                'subscription_id': notification.subscription.id,
                'tx_hash': notification.subscription.tx_hash,
            }
            request = HTTPRequest(
                          url=notification.subscription.callback_url,
                          headers=headers,
                          method='POST',
                          body=urllib.urlencode(post_data),
                          connect_timeout=180,
                          request_timeout=180
                      )

            client.fetch(request, self._get_callback_func(notification, total))

        logger.debug("start notify")
        logger.debug("total: {}".format(len(notifications)))

        # block until callback calls ioloop.IOLoop.instance().stop()
        ioloop.IOLoop.instance().start()

    def run_forever(self, test=False):

        while True:
            logger.debug("-"*20)
            logger.debug("Start a new round")
            best_block = self.get_best_block()
            logger.debug("best block: {}".format(best_block['hash']))
            if self.last_seen_block:
                logger.debug("last seen block: {}".format(self.last_seen_block['hash']))
            else:
                logger.debug("last seen block: None")

            if self.last_seen_block is None or self.last_seen_block['hash'] != best_block['hash']:
                logger.debug("there is new block since last update")

                new_notifications = []
                for tx_subscription in TxSubscription.objects.filter(txnotification=None):
                    logger.debug('check tx hash: {}'.format(tx_subscription.tx_hash))
                    try:
                        tx = self.get_transaction(tx_subscription.tx_hash)
                    except InvalidAddressOrKey:
                        # transaction not found, just skip
                        continue

                    if hasattr(tx, 'confirmations') and tx.confirmations >= tx_subscription.confirmation_count:
                       new_notifications.append(TxNotification(subscription=tx_subscription))

                TxNotification.objects.bulk_create(new_notifications)
            else:
                logger.debug("no new block since last update")

            notifications = TxNotification.objects.filter(is_notified=False, notification_attempts__lt=RETRY_TIMES)
            logger.debug("TxNotification number: {}".format(notifications.count()))
            self.start_notify(notifications)
            self.last_seen_block = best_block

            if test:
                return

            time.sleep(SLEEP_TIME)


class AddressNotifyDaemon(GcoinRPCMixin):

    def _get_callback_func(self, notification, total):
        def callback(response):
            self.count = self.count + 1
            logger.debug("-"*20)
            logger.debug("Request url: {}".format(response.request.url))
            logger.debug("Request effective url: {}".format(response.effective_url))
            logger.debug("Respons code: {}".format(response.code))
            logger.debug("Notification id: {}".format(notification.id))
            if response.code == 200:
                AddressNotification.objects.filter(id=notification.id).update(
                     is_notified=True,
                     notification_attempts=F('notification_attempts') + 1,
                     notification_time=timezone.now()
                )
            else:
                AddressNotification.objects.filter(id=notification.id).update(
                     notification_attempts=F('notification_attempts') + 1,
                )

            if self.count == total:
                ioloop.IOLoop.instance().stop()
        return callback

    def start_notify(self, notifications):
        if notifications.count() == 0:
            return

        self.count = 0
        client = AsyncHTTPClient()
        headers = {'content-type': "application/x-www-form-urlencoded"}
        total = notifications.count()

        for notification in notifications:
            post_data = {
                'notification_id': notification.id,
                'subscription_id': notification.subscription.id,
                'tx_hash': notification.tx_hash,
            }
            request = HTTPRequest(
                          url=notification.subscription.callback_url,
                          headers=headers,
                          method='POST',
                          body=urllib.urlencode(post_data),
                          connect_timeout=180,
                          request_timeout=180
                      )

            client.fetch(request, self._get_callback_func(notification, total))

        # block until callback calls ioloop.IOLoop.instance().stop()
        ioloop.IOLoop.instance().start()

    def run_forever(self):

        while True:
            time.sleep(SLEEP_TIME)

            # get new blocks since last round
            new_blocks = self.get_new_blocks()

            # create a address -> txs map from new blocks
            addr_txs_map = self.create_address_txs_map(new_blocks)

            # create AddressNotification instance in database
            self.create_notifications(addr_txs_map)

            notifications = AddressNotification.objects.filter(is_notified=False, notification_attempts__lt=RETRY_TIMES)
            self.start_notify(notifications)

            self.set_last_seen_block(new_blocks[-1]['hash'])

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
            logger.debug("no new blocks since last update")
            return new_blocks

        while block['hash'] != last_seen_block['hash']:
            new_blocks.append(block)
            block = self.get_block(block['previousblockhash'])
        logger.debug('{} new blocks since last update'.format(len(new_blocks)))
        return new_blocks[::-1]

    def create_address_txs_map(self, new_blocks):
        addr_txs_map = {}
        for block in new_blocks:
            # Note: this for loop can be optimized if core supports rpc to get all tx in a block
            for tx_hash in block['tx']:
                tx = self.get_transaction(tx_hash)

                # find all the addresses that related to this tx
                related_addresses = self.get_related_addresses(tx)

                for address in related_addresses:
                    if addr_txs_map.has_key(address):
                        addr_txs_map[address].append(tx)
                    else:
                        addr_txs_map[address] = [tx]

        return addr_txs_map

    def create_notifications(self, addr_txs_map):
        subscriptions = AddressSubscription.objects.all()
        new_notifications = []

        # Only the address that is in addr_txs_map and subscription need to be notify,
        # so iterate through the small one is more efficient
        if len(addr_txs_map) < subscriptions.count():
            for address, txs in addr_txs_map.iteritems():
                for tx in txs:
                    for subscription in subscriptions.filter(address=address):
                        new_notifications.append(AddressNotification(subscription=subscription, tx_hash=tx.txid))
        else:
            for subscription in subscriptions:
                if addr_txs_map.has_key(subscription.address):
                    for tx in addr_txs_map[subscription.address]:
                        new_notifications.append(AddressNotification(subscription=subscription, tx_hash=tx.txid))

        AddressNotification.objects.bulk_create(new_notifications)

    def get_related_addresses(self, tx):
        if tx.type == 'NORMAL' and tx.vin[0].has_key('coinbase'):
            # this tx is the first tx of every block, just skip
            return []

        addresses = []
        # addresses in vin
        for vin in tx.vin:
            if not vin.has_key('coinbase'):
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
        scriptPubKey = vout['scriptPubKey']
        if scriptPubKey['type'] == 'pubkey' or scriptPubKey['type'] == 'pubkeyhash':
            return scriptPubKey['addresses']
        else:
            return []

    def set_last_seen_block(self, block_hash):
        LastSeenBlock.objects.create(name='AddressNotifyDaemon', block_hash=block_hash)

    def get_last_seen_block(self):
        last_block = LastSeenBlock.objects.filter(name='AddressNotifyDaemon').latest('id')
        if last_block:
            return self.conn.getblock(last_block.block_hash)
        else:
            # return the genesis block if no last seen block
            return self.conn.getblock(self.conn.getblockhash(0))
