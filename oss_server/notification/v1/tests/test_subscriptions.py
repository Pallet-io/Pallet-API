import json
import uuid
from collections import OrderedDict


from django.core.serializers.json import DjangoJSONEncoder
from django.test import TestCase

from notification.models import AddressSubscription, TxSubscription


class AddressSubscriptionTest(TestCase):
    maxDiff = None

    def setUp(self):
        self.address_subscription = AddressSubscription.objects.create(
                                         address="1AceWFDUHRahFxgHDSdz89cdbZQPv6uarY",
                                         callback_url="http://callback.com"
                                    )

    def clean(self):
        AddressSubscription.objects.all().delete()

    def test_as_dict_func(self):
        obj_dict = self.address_subscription.as_dict()
        expected_data =  OrderedDict([
            ('id', self.address_subscription.id),
            ('address', self.address_subscription.address),
            ('callback_url', self.address_subscription.callback_url),
            ('created_time', self.address_subscription.created_time.strftime('%d-%m-%Y %H:%M:%S'))
        ])
        self.assertEqual(obj_dict, expected_data)

    def test_detail_view(self):
        obj_id = str(self.address_subscription.id)
        response = self.client.get('/notification/v1/address/subscription/{}'.format(obj_id))
        expected_data = json.dumps(self.address_subscription.as_dict(), cls=DjangoJSONEncoder)
        self.assertJSONEqual(response.content, expected_data)

    def test_detail_not_found(self):
        obj_id = str(uuid.uuid4())
        response = self.client.get('/notification/v1/address/subscription/{}'.format(obj_id))
        self.assertEqual(response.status_code, 404)
        expected_data = json.dumps({
            "error": {
                "type": "invalid_request_error",
                "params": [
                    {"name": "id", "message": "not found"}
                ]
            }
        })
        self.assertEqual(response.content, expected_data)

    def test_create_view(self):
        post_data = {
            "address": "112iazuQmHL7UcfE4ftYzAD1RxpwyAQd6n",
            "callback_url": "http://example.com"
        }
        response = self.client.post('/notification/v1/address/subscription', data=post_data)

        new_obj = AddressSubscription.objects.get(**post_data)
        expected_data = json.dumps(new_obj.as_dict(), cls=DjangoJSONEncoder)
        self.assertJSONEqual(response.content, expected_data)

    def _test_create_view_bad_params(self, post_data, expected_data):
        address_subscription_count = AddressSubscription.objects.count()
        response = self.client.post('/notification/v1/address/subscription', data=post_data)
        self.assertEqual(response.status_code, 400)
        # no new TxSubscription is created
        self.assertEqual(address_subscription_count, AddressSubscription.objects.count())
        self.assertJSONEqual(response.content, expected_data)

    def test_create_view_invalid_params(self):
        post_data = {
            "address": "112iazuQmHL7UcfE4ftYzAD1RxpwyAQd6",
            "callback_url": "abc"
        }
        expected_data = {
            "error": {
                "type": "invalid_request_error",
                "params": [
                    {
                        "name": "callback_url",
                        "message": "callback_url is invalid"
                    },
                    {
                        "name": "address",
                        "message": "112iazuQmHL7UcfE4ftYzAD1RxpwyAQd6 is not a valid address"
                    },
                ]
            }
        }
        self._test_create_view_bad_params(post_data, expected_data)

    def test_delete_view(self):
        obj_id = str(self.address_subscription.id)
        response = self.client.post('/notification/v1/address/subscription/{}/delete'.format(obj_id))
        expected_data = json.dumps({
            "id": obj_id,
            "deleted": True
        })
        self.assertJSONEqual(response.content, expected_data)

    def test_delete_view_not_found(self):
        obj_id = str(uuid.uuid4())
        response = self.client.post('/notification/v1/address/subscription/{}/delete'.format(obj_id))
        self.assertEqual(response.status_code, 404)
        expected_data = json.dumps({
            "error": {
                "type": "invalid_request_error",
                "params": [
                    {"name": "id", "message": "not found"}
                ]
            }
        })
        self.assertEqual(response.content, expected_data)


class TxSubscriptionTest(TestCase):
    maxDiff = None

    def setUp(self):
        self.tx_subscription = TxSubscription.objects.create(
                                   tx_hash="75854130407a8b6b7777a2b690f2a893f7e95a7df77a06958924e7b6a3ce25b8",
                                   confirmation_count=10,
                                   callback_url="http://callback.com"
                               )

    def clean(self):
        TxSubscription.objects.all().delete()

    def test_as_dict_func(self):
        obj_dict = self.tx_subscription.as_dict()
        expected_data =  OrderedDict([
            ('id', self.tx_subscription.id),
            ('tx_hash', self.tx_subscription.tx_hash),
            ('confirmation_count', self.tx_subscription.confirmation_count),
            ('callback_url', self.tx_subscription.callback_url),
            ('created_time', self.tx_subscription.created_time.strftime('%d-%m-%Y %H:%M:%S'))
        ])
        self.assertEqual(obj_dict, expected_data)

    def test_detail_view(self):
        obj_id = str(self.tx_subscription.id)
        response = self.client.get('/notification/v1/tx/subscription/{}'.format(obj_id))
        expected_data = json.dumps(self.tx_subscription.as_dict(), cls=DjangoJSONEncoder)
        self.assertJSONEqual(response.content, expected_data)

    def test_detail_not_found(self):
        obj_id = str(uuid.uuid4())
        response = self.client.get('/notification/v1/tx/subscription/{}'.format(obj_id))
        self.assertEqual(response.status_code, 404)
        expected_data = json.dumps({
            "error": {
                "type": "invalid_request_error",
                "params": [
                    {"name": "id", "message": "not found"}
                ]
            }
        })
        self.assertEqual(response.content, expected_data)

    def test_create_view(self):
        post_data = {
            "tx_hash": "53d5a163e504cb4e3427e5e377ed5382837bbe7be35e6b17a28a386c021d015e",
            "confirmation_count": 13,
            "callback_url": "http://example.com"
        }
        response = self.client.post('/notification/v1/tx/subscription', data=post_data)

        new_obj = TxSubscription.objects.get(**post_data)
        expected_data = json.dumps(new_obj.as_dict(), cls=DjangoJSONEncoder)
        self.assertJSONEqual(response.content, expected_data)

    def _test_create_view_bad_params(self, post_data, expected_data):
        tx_subscription_count = TxSubscription.objects.count()
        response = self.client.post('/notification/v1/tx/subscription', data=post_data)
        self.assertEqual(response.status_code, 400)
        # no new TxSubscription is created
        self.assertEqual(tx_subscription_count, TxSubscription.objects.count())
        self.assertJSONEqual(response.content, expected_data)

    def test_create_view_invalid_params_1(self):
        post_data = {
            "tx_hash": "3d5a163e504cb4e3427e5e377ed5382837bbe7be35e6b17a28a386c021d0115e3",
            "confirmation_count": -1,
            "callback_url": "abc"
        }
        expected_data = {
            "error": {
                "type": "invalid_request_error",
                "params": [
                    {
                        "name": "tx_hash",
                        "message": "tx_hash is at most 64 characters"
                    },
                    {
                        "name": "callback_url",
                        "message": "callback_url is invalid"
                    },
                    {
                        "name": "confirmation_count",
                        "message": "confirmation_count needs to be greater than or equal to 1"
                    },
                ]
            }
        }
        self._test_create_view_bad_params(post_data, expected_data)

    def test_create_view_invalid_parmas_2(self):
        post_data = {
            "tx_hash": "53d5a163e504cb4e3427e5e377ed5382837bbe7be35e6b17a28a386c021d015*",
            "confirmation_count": 13,
            "callback_url": "http://example.com"
        }
        expected_data = json.dumps({
            "error": {
                "type": "invalid_request_error",
                "params": [
                    {
                        "name": "tx_hash",
                        "message": "tx_hash is invalid"
                    }
                ]
            }
        })
        self._test_create_view_bad_params(post_data, expected_data)

    def test_delete_view(self):
        obj_id = str(self.tx_subscription.id)
        response = self.client.post('/notification/v1/tx/subscription/{}/delete'.format(obj_id))
        expected_data = json.dumps({
            "id": obj_id,
            "deleted": True
        })
        self.assertJSONEqual(response.content, expected_data)

    def test_delete_view_not_found(self):
        obj_id = str(uuid.uuid4())
        response = self.client.post('/notification/v1/tx/subscription/{}/delete'.format(obj_id))
        self.assertEqual(response.status_code, 404)
        expected_data = json.dumps({
            "error": {
                "type": "invalid_request_error",
                "params": [
                    {"name": "id", "message": "not found"}
                ]
            }
        })
        self.assertEqual(response.content, expected_data)

