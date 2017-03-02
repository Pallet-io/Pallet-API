from decimal import Decimal

from django.test import TestCase

import mock
from gcoinrpc.data import TransactionInfo
from tornado.httpclient import HTTPResponse

from notification.daemon import AddressNotifyDaemon
from notification.models import AddressNotification, AddressSubscription, LastSeenBlock


class AddressNotifyDaemonTestCase(TestCase):

    def setUp(self):
        self.address_subscription1 = AddressSubscription.objects.create(
                                         address="1GvRsoxx67CzRxvMXofDEVSTX4m29V9kE5",
                                         callback_url="http://callback.com",
                                     )

        self.blocks = [
            {
                "hash" : "00000fd26fa800f46807ab6902ac081f88d3784e42f261c3807be6e1ceb2e63b",
                "confirmations" : 4,
                "size" : 330,
                "height" : 261,
                "version" : 3,
                "merkleroot" : "0379ece215589f364faeac2894968464094e9a3eb6494011529551c2615d7744",
                "tx" : [
                    "0379ece215589f364faeac2894968464094e9a3eb6494011529551c2615d7744"
                ],
                "time" : 1470207767,
                "starttime" : 1470207766,
                "nonce" : 920772,
                "bits" : "1e0ffff0",
                "difficulty" : 0.00024414,
                "chainwork" : "0000000000000000000000000000000000000000000000000000000010601060",
                "previousblockhash" : "000003f1fc8675b0b1c7e71e1a8e31dfadd9467f73e05074e0d7c5f3debf331e",
                "nextblockhash" : "000004db4292931695bedb621d8f21b1cfb7a7bd53266be1aecc8a87176423ce"
            },
            {
                "hash" : "000004db4292931695bedb621d8f21b1cfb7a7bd53266be1aecc8a87176423ce",
                "confirmations" : 3,
                "size" : 330,
                "height" : 262,
                "version" : 3,
                "merkleroot" : "664fbc810fb810a3d2d71f0f843be770b22906ab7713b03386eb1318140c596f",
                "tx" : [
                    "664fbc810fb810a3d2d71f0f843be770b22906ab7713b03386eb1318140c596f"
                ],
                "time" : 1470207767,
                "starttime" : 1470207766,
                "nonce" : 16984,
                "bits" : "1e0ffff0",
                "difficulty" : 0.00024414,
                "chainwork" : "0000000000000000000000000000000000000000000000000000000010701070",
                "previousblockhash" : "00000fd26fa800f46807ab6902ac081f88d3784e42f261c3807be6e1ceb2e63b",
                "nextblockhash" : "00000b92c5ed60e1f8e637c0a546cf13592e8b958f5952ade1f1825f42e15b9f"
            },
            {
                "hash" : "00000b92c5ed60e1f8e637c0a546cf13592e8b958f5952ade1f1825f42e15b9f",
                "confirmations" : 2,
                "size" : 331,
                "height" : 263,
                "version" : 3,
                "merkleroot" : "01adc751f69b756c87afd4219b98895db611ce388c51decaf2c20381ba16041f",
                "tx" : [
                    "01adc751f69b756c87afd4219b98895db611ce388c51decaf2c20381ba16041f",
                    "7cd0c5ac40c6391a982801f1b05df48f056f3fc774543f3bf0fb2568c0b0c566",
                    "1bf6fe6ff8e9c68a8d158d955f8c9297f364695ede31308399be1c41db294ad2",
                    "0c70b2b5e6c6618bd397f2d4024367d19264093e5c603d483644f20c183eaf7a",
                ],
                "time" : 1470207768,
                "starttime" : 1470207767,
                "nonce" : 237760,
                "bits" : "1e0ffff0",
                "difficulty" : 0.00024414,
                "chainwork" : "0000000000000000000000000000000000000000000000000000000010801080",
                "previousblockhash" : "000004db4292931695bedb621d8f21b1cfb7a7bd53266be1aecc8a87176423ce",
                "nextblockhash" : "00000070b0bc8334373e8565bc419349ae476f676c12e75e156ab2b8fc16dd1a"
            },
            {
                "hash" : "00000070b0bc8334373e8565bc419349ae476f676c12e75e156ab2b8fc16dd1a",
                "confirmations" : 1,
                "size" : 330,
                "height" : 264,
                "version" : 3,
                "merkleroot" : "6b91a66c096ea475ec7cad61d3a795a06c7bdc81ca3b7b5b7ca9341480bd29a4",
                "tx" : [
                    "6b91a66c096ea475ec7cad61d3a795a06c7bdc81ca3b7b5b7ca9341480bd29a4"
                ],
                "time" : 1470207769,
                "starttime" : 1470207767,
                "nonce" : 2356050,
                "bits" : "1e0ffff0",
                "difficulty" : 0.00024414,
                "chainwork" : "0000000000000000000000000000000000000000000000000000000010901090",
                "previousblockhash" : "00000b92c5ed60e1f8e637c0a546cf13592e8b958f5952ade1f1825f42e15b9f"
            }
        ]

        # fork from "000004db4292931695bedb621d8f21b1cfb7a7bd53266be1aecc8a87176423ce",
        self.blocks_in_fork_chain = [
            {
                "hash" : "00000073cddfe3ce3a406ba66e030b2b8d819d2a39518e3ac25893e970cd5aa3",
                "confirmations" : -1,
                "size" : 330,
                "height" : 263,
                "version" : 3,
                "merkleroot" : "4894dab129d143fef3035f75660889b104696ee11ce7195bde9989b6a00de8f5",
                "tx" : [
                    "4894dab129d143fef3035f75660889b104696ee11ce7195bde9989b6a00de8f5"
                ],
                "time" : 1469079674,
                "starttime" : 1469079673,
                "nonce" : 347215,
                "bits" : "1e0ffff0",
                "difficulty" : 0.00024414,
                "chainwork" : "0000000000000000000000000000000000000000000000000000000006400640",
                "previousblockhash" : "000004db4292931695bedb621d8f21b1cfb7a7bd53266be1aecc8a87176423ce",
                "nextblockhash" : "00000e1b6ee4a60a65e7308bcb053b20a957693d8949bfbe5c040f50302f706b"
            },
            {
                "hash" : "00000e1b6ee4a60a65e7308bcb053b20a957693d8949bfbe5c040f50302f706b",
                "confirmations" : -1,
                "size" : 330,
                "height" : 264,
                "version" : 3,
                "merkleroot" : "4d9c319d73a1164406a49f6a8e0ccd6dce3e198061da68532909d05a6247b2f5",
                "tx" : [
                    "4d9c319d73a1164406a49f6a8e0ccd6dce3e198061da68532909d05a6247b2f5"
                ],
                "time" : 1469079674,
                "starttime" : 1469079673,
                "nonce" : 833892,
                "bits" : "1e0ffff0",
                "difficulty" : 0.00024414,
                "chainwork" : "0000000000000000000000000000000000000000000000000000000006500650",
                "previousblockhash" : "00000073cddfe3ce3a406ba66e030b2b8d819d2a39518e3ac25893e970cd5aa3",
                "nextblockhash" : "00000066577098e86c3ab868c2a47fdd007ac67fc505994c2d402f830fbf238a"
            }
        ]

        self.block_map = {block['hash']: block for block in self.blocks + self.blocks_in_fork_chain}

        self.txs = [
            {
                "hex" : "01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff49483045022100b64782e2c263782b2a7bf378502c17f09dcbbd7b52b0600f28486a982e77bd4902202915600ecebece142b9196119188e0ebe4aa4f7b4fed109760c05ec2896d939501ffffffff010000000000000000232103975587646662443ecd55cc0cfa3608b6d35f72a4dc86974e7d19e42d3f039d27ac000000001797a15700000000",
                "txid" : "01adc751f69b756c87afd4219b98895db611ce388c51decaf2c20381ba16041f",
                "version" : 1,
                "locktime" : 1470207767,
                "type" : "NORMAL",
                "size" : 176,
                "vin" : [
                    {
                        "coinbase" : "483045022100b64782e2c263782b2a7bf378502c17f09dcbbd7b52b0600f28486a982e77bd4902202915600ecebece142b9196119188e0ebe4aa4f7b4fed109760c05ec2896d939501",
                        "scriptSig" : {
                            "asm" : "3045022100b64782e2c263782b2a7bf378502c17f09dcbbd7b52b0600f28486a982e77bd4902202915600ecebece142b9196119188e0ebe4aa4f7b4fed109760c05ec2896d939501",
                            "hex" : "483045022100b64782e2c263782b2a7bf378502c17f09dcbbd7b52b0600f28486a982e77bd4902202915600ecebece142b9196119188e0ebe4aa4f7b4fed109760c05ec2896d939501"
                        },
                        "sequence" : 4294967295
                    }
                ],
                "vout" : [
                    {
                        "value" : 0,
                        "n" : 0,
                        "scriptPubKey" : {
                            "asm" : "03975587646662443ecd55cc0cfa3608b6d35f72a4dc86974e7d19e42d3f039d27 OP_CHECKSIG",
                            "hex" : "2103975587646662443ecd55cc0cfa3608b6d35f72a4dc86974e7d19e42d3f039d27ac",
                            "reqSigs" : 1,
                            "type" : "pubkey",
                            "addresses" : [
                                "18f49V4Xm8rou489HjujHbF1e3HyxUSwH3"
                            ]
                        },
                        "color" : 0
                    }
                ],
                "blockhash" : "00000b92c5ed60e1f8e637c0a546cf13592e8b958f5952ade1f1825f42e15b9f",
                "confirmations" : 13,
                "time" : 1470207768,
                "blocktime" : 1470207768
            },
            {
                "hex" : "010000000166c5b0c06825fbf03b3f5474c73f6f058ff45db0f10128981a39c640acc5d07c000000006a47304402204a2497e2fa8b56d1d408c20bba784d49540fbe97d681e7aecbd51bd0307d8f8602202bffc9ed78eb9f5fbbe0bf8cb1ea10b7065e9b90f4bd47d38e8a58dcc88ba3cb0121028541986daf38c326240c29de2405540fc803a61f79278bbc909d3a44e488023efeffffff02005ed0b2000000001976a91401b66251826119cdc887ed66af329a2006c377a188ac0100000000a5459b010000001976a914039706759a9bec287f26034ced30c57115e81f1c88ac01000000fe00000000000000",
                "txid" : "0c70b2b5e6c6618bd397f2d4024367d19264093e5c603d483644f20c183eaf7a",
                "version" : 1,
                "locktime" : 254,
                "type" : "NORMAL",
                "size" : 237,
                "vin" : [
                    {
                        "txid" : "7cd0c5ac40c6391a982801f1b05df48f056f3fc774543f3bf0fb2568c0b0c566",
                        "vout" : 0,
                        "scriptSig" : {
                            "asm" : "304402204a2497e2fa8b56d1d408c20bba784d49540fbe97d681e7aecbd51bd0307d8f8602202bffc9ed78eb9f5fbbe0bf8cb1ea10b7065e9b90f4bd47d38e8a58dcc88ba3cb01 028541986daf38c326240c29de2405540fc803a61f79278bbc909d3a44e488023e",
                            "hex" : "47304402204a2497e2fa8b56d1d408c20bba784d49540fbe97d681e7aecbd51bd0307d8f8602202bffc9ed78eb9f5fbbe0bf8cb1ea10b7065e9b90f4bd47d38e8a58dcc88ba3cb0121028541986daf38c326240c29de2405540fc803a61f79278bbc909d3a44e488023e"
                        },
                        "sequence" : 4294967294
                    }
                ],
                "vout" : [
                    {
                        "value" : 3000000000,
                        "n" : 0,
                        "scriptPubKey" : {
                            "asm" : "OP_DUP OP_HASH160 01b66251826119cdc887ed66af329a2006c377a1 OP_EQUALVERIFY OP_CHECKSIG",
                            "hex" : "76a91401b66251826119cdc887ed66af329a2006c377a188ac",
                            "reqSigs" : 1,
                            "type" : "pubkeyhash",
                            "addresses" : [
                                "1A4ATaSggTSxrce1sgGP3Aw3mLM4XZprF"
                            ]
                        },
                        "color" : 1
                    },
                    {
                        "value" : 6900000000,
                        "n" : 1,
                        "scriptPubKey" : {
                            "asm" : "OP_DUP OP_HASH160 039706759a9bec287f26034ced30c57115e81f1c OP_EQUALVERIFY OP_CHECKSIG",
                            "hex" : "76a914039706759a9bec287f26034ced30c57115e81f1c88ac",
                            "reqSigs" : 1,
                            "type" : "pubkeyhash",
                            "addresses" : [
                                "1Kywza1jgdacR5Wb1xzviTb76hwKyWQjU"
                            ]
                        },
                        "color" : 1
                    }
                ],
                "blockhash" : "00000b92c5ed60e1f8e637c0a546cf13592e8b958f5952ade1f1825f42e15b9f",
                "confirmations" : 11,
                "time" : 1470725030,
                "blocktime" : 1470725030
            },
            {
                "hex" : "0100000002a585a40399ec83a65c4993e491d859f5ab6d239480f6d9cdab5da870c17aa528000000006a4730440220273128ad2ef719bf2764ffbc09b648e6e05a907557f1ad370c1173a2d9be440502200f2eade7c3230f59268a9f01902e7edbb68b829ed825903d493b9c493b5cdc4201210366f972fa600de7f12ec28873e859c7f6953782308f6bd958cb06b3bde28273bafeffffff5ebb4b252587d4f299180b07b4fb9ea2fc750a5c5dd6cafc07d384cd9378a23d000000006b483045022100971c2c1e42ac8f10f241b2dfe45fb61fe8a73a59b5cf4aba5a01a3c47c3a450e022055736752cbbdd8400f367c28a7fb30ccba09be62c651d35846ba7bd345867a0801210366f972fa600de7f12ec28873e859c7f6953782308f6bd958cb06b3bde28273bafeffffff02007841cb020000001976a914039706759a9bec287f26034ced30c57115e81f1c88ac01000000006fe0d6010000001976a914aea4b2bcf13e1ba5e7793a759ef0503ae3e1ac0c88ac01000000fe00000000000000",
                "txid" : "1bf6fe6ff8e9c68a8d158d955f8c9297f364695ede31308399be1c41db294ad2",
                "version" : 1,
                "locktime" : 254,
                "type" : "NORMAL",
                "size" : 385,
                "vin" : [
                    {
                        "txid" : "28a57ac170a85dabcdd9f68094236dabf559d891e493495ca683ec9903a485a5",
                        "vout" : 0,
                        "scriptSig" : {
                            "asm" : "30440220273128ad2ef719bf2764ffbc09b648e6e05a907557f1ad370c1173a2d9be440502200f2eade7c3230f59268a9f01902e7edbb68b829ed825903d493b9c493b5cdc4201 0366f972fa600de7f12ec28873e859c7f6953782308f6bd958cb06b3bde28273ba",
                            "hex" : "4730440220273128ad2ef719bf2764ffbc09b648e6e05a907557f1ad370c1173a2d9be440502200f2eade7c3230f59268a9f01902e7edbb68b829ed825903d493b9c493b5cdc4201210366f972fa600de7f12ec28873e859c7f6953782308f6bd958cb06b3bde28273ba"
                        },
                        "sequence" : 4294967294
                    },
                    {
                        "txid" : "3da27893cd84d307fccad65d5c0a75fca29efbb4070b1899f2d48725254bbb5e",
                        "vout" : 0,
                        "scriptSig" : {
                            "asm" : "3045022100971c2c1e42ac8f10f241b2dfe45fb61fe8a73a59b5cf4aba5a01a3c47c3a450e022055736752cbbdd8400f367c28a7fb30ccba09be62c651d35846ba7bd345867a0801 0366f972fa600de7f12ec28873e859c7f6953782308f6bd958cb06b3bde28273ba",
                            "hex" : "483045022100971c2c1e42ac8f10f241b2dfe45fb61fe8a73a59b5cf4aba5a01a3c47c3a450e022055736752cbbdd8400f367c28a7fb30ccba09be62c651d35846ba7bd345867a0801210366f972fa600de7f12ec28873e859c7f6953782308f6bd958cb06b3bde28273ba"
                        },
                        "sequence" : 4294967294
                    }
                ],
                "vout" : [
                    {
                        "value" : 12000000000,
                        "n" : 0,
                        "scriptPubKey" : {
                            "asm" : "OP_DUP OP_HASH160 039706759a9bec287f26034ced30c57115e81f1c OP_EQUALVERIFY OP_CHECKSIG",
                            "hex" : "76a914039706759a9bec287f26034ced30c57115e81f1c88ac",
                            "reqSigs" : 1,
                            "type" : "pubkeyhash",
                            "addresses" : [
                                "1Kywza1jgdacR5Wb1xzviTb76hwKyWQjU"
                            ]
                        },
                        "color" : 1
                    },
                    {
                        "value" : 7900000000,
                        "n" : 1,
                        "scriptPubKey" : {
                            "asm" : "OP_DUP OP_HASH160 aea4b2bcf13e1ba5e7793a759ef0503ae3e1ac0c OP_EQUALVERIFY OP_CHECKSIG",
                            "hex" : "76a914aea4b2bcf13e1ba5e7793a759ef0503ae3e1ac0c88ac",
                            "reqSigs" : 1,
                            "type" : "pubkeyhash",
                            "addresses" : [
                                "1GvRsoxx67CzRxvMXofDEVSTX4m29V9kE5"
                            ]
                        },
                        "color" : 1
                    }
                ],
                "blockhash" : "00000b92c5ed60e1f8e637c0a546cf13592e8b958f5952ade1f1825f42e15b9f",
                "confirmations" : 11,
                "time" : 1470725030,
                "blocktime" : 1470725030
            },
            {
                "hex" : "01000000025e0634aae7563b44a8c8068c0bde2b1d6819ad17382ccbf27b04fa07a9994b94000000006b483045022100fc97445c7ab20c3013b5b17768b4d83b0e33b3a23f5c2943ade8ac7110d58351022068955d16f0b4ecb1ae574421a773ed93ee8fdde1d133c91b1a4dcb04187009aa01210366f972fa600de7f12ec28873e859c7f6953782308f6bd958cb06b3bde28273bafeffffff090214fd581630c3796f348e388d00a7df6f0306fed5c2a972fc9f9281e39b71000000006b4830450221009a1a273f94373438c86c487576b1d7464b52869475bf3b38182daa60e7aaf2fc0220769068348e578a54f4d614aa5cb62b406f1b945f0998672ea923a637793c397101210366f972fa600de7f12ec28873e859c7f6953782308f6bd958cb06b3bde28273bafeffffff0100e40b54020000001976a914039706759a9bec287f26034ced30c57115e81f1c88ac01000000fe00000000000000",
                "txid" : "7cd0c5ac40c6391a982801f1b05df48f056f3fc774543f3bf0fb2568c0b0c566",
                "version" : 1,
                "locktime" : 254,
                "type" : "NORMAL",
                "size" : 348,
                "vin" : [
                    {
                        "txid" : "944b99a907fa047bf2cb2c3817ad19681d2bde0b8c06c8a8443b56e7aa34065e",
                        "vout" : 0,
                        "scriptSig" : {
                            "asm" : "3045022100fc97445c7ab20c3013b5b17768b4d83b0e33b3a23f5c2943ade8ac7110d58351022068955d16f0b4ecb1ae574421a773ed93ee8fdde1d133c91b1a4dcb04187009aa01 0366f972fa600de7f12ec28873e859c7f6953782308f6bd958cb06b3bde28273ba",
                            "hex" : "483045022100fc97445c7ab20c3013b5b17768b4d83b0e33b3a23f5c2943ade8ac7110d58351022068955d16f0b4ecb1ae574421a773ed93ee8fdde1d133c91b1a4dcb04187009aa01210366f972fa600de7f12ec28873e859c7f6953782308f6bd958cb06b3bde28273ba"
                        },
                        "sequence" : 4294967294
                    },
                    {
                        "txid" : "719be381929ffc72a9c2d5fe06036fdfa7008d388e346f79c3301658fd140209",
                        "vout" : 0,
                        "scriptSig" : {
                            "asm" : "30450221009a1a273f94373438c86c487576b1d7464b52869475bf3b38182daa60e7aaf2fc0220769068348e578a54f4d614aa5cb62b406f1b945f0998672ea923a637793c397101 0366f972fa600de7f12ec28873e859c7f6953782308f6bd958cb06b3bde28273ba",
                            "hex" : "4830450221009a1a273f94373438c86c487576b1d7464b52869475bf3b38182daa60e7aaf2fc0220769068348e578a54f4d614aa5cb62b406f1b945f0998672ea923a637793c397101210366f972fa600de7f12ec28873e859c7f6953782308f6bd958cb06b3bde28273ba"
                        },
                        "sequence" : 4294967294
                    }
                ],
                "vout" : [
                    {
                        "value" : 10000000000,
                        "n" : 0,
                        "scriptPubKey" : {
                            "asm" : "OP_DUP OP_HASH160 039706759a9bec287f26034ced30c57115e81f1c OP_EQUALVERIFY OP_CHECKSIG",
                            "hex" : "76a914039706759a9bec287f26034ced30c57115e81f1c88ac",
                            "reqSigs" : 1,
                            "type" : "pubkeyhash",
                            "addresses" : [
                                "1Kywza1jgdacR5Wb1xzviTb76hwKyWQjU"
                            ]
                        },
                        "color" : 1
                    }
                ],
                "blockhash" : "00000b92c5ed60e1f8e637c0a546cf13592e8b958f5952ade1f1825f42e15b9f",
                "confirmations" : 11,
                "time" : 1470725030,
                "blocktime" : 1470725030
            },
            {
                "hex" : "01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff6b483045022100ad9e73ae31b7d826b0f2bad3295235007e619c03f32a29563499fb39347498b60220168fe649393d8dd79e109a7191bc70f2307d9eea89dd9c690174273a691bff2101210366f972fa600de7f12ec28873e859c7f6953782308f6bd958cb06b3bde28273baffffffff0100e1f505000000001976a914aea4b2bcf13e1ba5e7793a759ef0503ae3e1ac0c88ac010000000000000001000000",
                "txid" : "944b99a907fa047bf2cb2c3817ad19681d2bde0b8c06c8a8443b56e7aa34065e",
                "version" : 1,
                "locktime" : 0,
                "type" : "MINT",
                "size" : 200,
                "vin" : [
                    {
                        "coinbase" : "483045022100ad9e73ae31b7d826b0f2bad3295235007e619c03f32a29563499fb39347498b60220168fe649393d8dd79e109a7191bc70f2307d9eea89dd9c690174273a691bff2101210366f972fa600de7f12ec28873e859c7f6953782308f6bd958cb06b3bde28273ba",
                        "scriptSig" : {
                            "asm" : "3045022100ad9e73ae31b7d826b0f2bad3295235007e619c03f32a29563499fb39347498b60220168fe649393d8dd79e109a7191bc70f2307d9eea89dd9c690174273a691bff2101 0366f972fa600de7f12ec28873e859c7f6953782308f6bd958cb06b3bde28273ba",
                            "hex" : "483045022100ad9e73ae31b7d826b0f2bad3295235007e619c03f32a29563499fb39347498b60220168fe649393d8dd79e109a7191bc70f2307d9eea89dd9c690174273a691bff2101210366f972fa600de7f12ec28873e859c7f6953782308f6bd958cb06b3bde28273ba"
                        },
                        "sequence" : 4294967295
                    }
                ],
                "vout" : [
                    {
                        "value" : 100000000,
                        "n" : 0,
                        "scriptPubKey" : {
                            "asm" : "OP_DUP OP_HASH160 aea4b2bcf13e1ba5e7793a759ef0503ae3e1ac0c OP_EQUALVERIFY OP_CHECKSIG",
                            "hex" : "76a914aea4b2bcf13e1ba5e7793a759ef0503ae3e1ac0c88ac",
                            "reqSigs" : 1,
                            "type" : "pubkeyhash",
                            "addresses" : [
                                "1GvRsoxx67CzRxvMXofDEVSTX4m29V9kE5"
                            ]
                        },
                        "color" : 1
                    }
                ],
                "blockhash" : "000005681bd6214742bf9494957e4c3166f90b50ba9901bcbb1f37c4b7fea757",
                "confirmations" : 77,
                "time" : 1470108698,
                "blocktime" : 1470108698
            },
            {
                "hex" : "01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff6b483045022100f69db9d4c91fbb3f29c74415b49e3f68fb0485dd54770f4de6b858bfea42c4b802204e02c6184b3a1466e888d250f1427f6aba71e00af02fce1585dce964e983b6ec01210366f972fa600de7f12ec28873e859c7f6953782308f6bd958cb06b3bde28273baffffffff0100e40b54020000001976a914aea4b2bcf13e1ba5e7793a759ef0503ae3e1ac0c88ac010000000000000001000000",
                "txid" : "719be381929ffc72a9c2d5fe06036fdfa7008d388e346f79c3301658fd140209",
                "version" : 1,
                "locktime" : 0,
                "type" : "MINT",
                "size" : 200,
                "vin" : [
                    {
                        "coinbase" : "483045022100f69db9d4c91fbb3f29c74415b49e3f68fb0485dd54770f4de6b858bfea42c4b802204e02c6184b3a1466e888d250f1427f6aba71e00af02fce1585dce964e983b6ec01210366f972fa600de7f12ec28873e859c7f6953782308f6bd958cb06b3bde28273ba",
                        "scriptSig" : {
                            "asm" : "3045022100f69db9d4c91fbb3f29c74415b49e3f68fb0485dd54770f4de6b858bfea42c4b802204e02c6184b3a1466e888d250f1427f6aba71e00af02fce1585dce964e983b6ec01 0366f972fa600de7f12ec28873e859c7f6953782308f6bd958cb06b3bde28273ba",
                            "hex" : "483045022100f69db9d4c91fbb3f29c74415b49e3f68fb0485dd54770f4de6b858bfea42c4b802204e02c6184b3a1466e888d250f1427f6aba71e00af02fce1585dce964e983b6ec01210366f972fa600de7f12ec28873e859c7f6953782308f6bd958cb06b3bde28273ba"
                        },
                        "sequence" : 4294967295
                    }
                ],
                "vout" : [
                    {
                        "value" : 10000000000,
                        "n" : 0,
                        "scriptPubKey" : {
                            "asm" : "OP_DUP OP_HASH160 aea4b2bcf13e1ba5e7793a759ef0503ae3e1ac0c OP_EQUALVERIFY OP_CHECKSIG",
                            "hex" : "76a914aea4b2bcf13e1ba5e7793a759ef0503ae3e1ac0c88ac",
                            "reqSigs" : 1,
                            "type" : "pubkeyhash",
                            "addresses" : [
                                "1GvRsoxx67CzRxvMXofDEVSTX4m29V9kE5"
                            ]
                        },
                        "color" : 1
                    }
                ],
                "blockhash" : "000003c16b741561b18f1204280f89306ffaeb2bf2331af73733703f719f0b8f",
                "confirmations" : 44,
                "time" : 1470206362,
                "blocktime" : 1470206362
            },
            {
                "hex" : "01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff6b483045022100cf4470233c6cf357eaf69d3ef6e120651d94672ed0c8cccd184cca7b59641866022034be6b21e992134919dd8dbf6d0565845154a5c07f6502bcdc6502b9dc72c39001210366f972fa600de7f12ec28873e859c7f6953782308f6bd958cb06b3bde28273baffffffff0100e40b54020000001976a914aea4b2bcf13e1ba5e7793a759ef0503ae3e1ac0c88ac010000000000000001000000",
                "txid" : "28a57ac170a85dabcdd9f68094236dabf559d891e493495ca683ec9903a485a5",
                "version" : 1,
                "locktime" : 0,
                "type" : "MINT",
                "size" : 200,
                "vin" : [
                    {
                        "coinbase" : "483045022100cf4470233c6cf357eaf69d3ef6e120651d94672ed0c8cccd184cca7b59641866022034be6b21e992134919dd8dbf6d0565845154a5c07f6502bcdc6502b9dc72c39001210366f972fa600de7f12ec28873e859c7f6953782308f6bd958cb06b3bde28273ba",
                        "scriptSig" : {
                            "asm" : "3045022100cf4470233c6cf357eaf69d3ef6e120651d94672ed0c8cccd184cca7b59641866022034be6b21e992134919dd8dbf6d0565845154a5c07f6502bcdc6502b9dc72c39001 0366f972fa600de7f12ec28873e859c7f6953782308f6bd958cb06b3bde28273ba",
                            "hex" : "483045022100cf4470233c6cf357eaf69d3ef6e120651d94672ed0c8cccd184cca7b59641866022034be6b21e992134919dd8dbf6d0565845154a5c07f6502bcdc6502b9dc72c39001210366f972fa600de7f12ec28873e859c7f6953782308f6bd958cb06b3bde28273ba"
                        },
                        "sequence" : 4294967295
                    }
                ],
                "vout" : [
                    {
                        "value" : 10000000000,
                        "n" : 0,
                        "scriptPubKey" : {
                            "asm" : "OP_DUP OP_HASH160 aea4b2bcf13e1ba5e7793a759ef0503ae3e1ac0c OP_EQUALVERIFY OP_CHECKSIG",
                            "hex" : "76a914aea4b2bcf13e1ba5e7793a759ef0503ae3e1ac0c88ac",
                            "reqSigs" : 1,
                            "type" : "pubkeyhash",
                            "addresses" : [
                                "1GvRsoxx67CzRxvMXofDEVSTX4m29V9kE5"
                            ]
                        },
                        "color" : 1
                    }
                ],
                "blockhash" : "000008c76047365528738e6a9816fad96d1dc24d17e9a5ddb51165fb946fcd41",
                "confirmations" : 55,
                "time" : 1470205951,
                "blocktime" : 1470205951
            },
            {
                "hex" : "01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff6b4830450221009b1db0692690af5b1b6559e47d1a4605b8fa2516704e9ebde673622461a1987c022008c58973dbf685170511b10a3a8a52c8a69f46c3a7213bc4fedb377112fe56ef01210366f972fa600de7f12ec28873e859c7f6953782308f6bd958cb06b3bde28273baffffffff0100e40b54020000001976a914aea4b2bcf13e1ba5e7793a759ef0503ae3e1ac0c88ac010000000000000001000000",
                "txid" : "3da27893cd84d307fccad65d5c0a75fca29efbb4070b1899f2d48725254bbb5e",
                "version" : 1,
                "locktime" : 0,
                "type" : "MINT",
                "size" : 200,
                "vin" : [
                    {
                        "coinbase" : "4830450221009b1db0692690af5b1b6559e47d1a4605b8fa2516704e9ebde673622461a1987c022008c58973dbf685170511b10a3a8a52c8a69f46c3a7213bc4fedb377112fe56ef01210366f972fa600de7f12ec28873e859c7f6953782308f6bd958cb06b3bde28273ba",
                        "scriptSig" : {
                            "asm" : "30450221009b1db0692690af5b1b6559e47d1a4605b8fa2516704e9ebde673622461a1987c022008c58973dbf685170511b10a3a8a52c8a69f46c3a7213bc4fedb377112fe56ef01 0366f972fa600de7f12ec28873e859c7f6953782308f6bd958cb06b3bde28273ba",
                            "hex" : "4830450221009b1db0692690af5b1b6559e47d1a4605b8fa2516704e9ebde673622461a1987c022008c58973dbf685170511b10a3a8a52c8a69f46c3a7213bc4fedb377112fe56ef01210366f972fa600de7f12ec28873e859c7f6953782308f6bd958cb06b3bde28273ba"
                        },
                        "sequence" : 4294967295
                    }
                ],
                "vout" : [
                    {
                        "value" : 10000000000,
                        "n" : 0,
                        "scriptPubKey" : {
                            "asm" : "OP_DUP OP_HASH160 aea4b2bcf13e1ba5e7793a759ef0503ae3e1ac0c OP_EQUALVERIFY OP_CHECKSIG",
                            "hex" : "76a914aea4b2bcf13e1ba5e7793a759ef0503ae3e1ac0c88ac",
                            "reqSigs" : 1,
                            "type" : "pubkeyhash",
                            "addresses" : [
                                "1GvRsoxx67CzRxvMXofDEVSTX4m29V9kE5"
                            ]
                        },
                        "color" : 1
                    }
                ],
                "blockhash" : "00000c771a4fddac120115415b97a5668ed43d8f22a43ac6d3e1db1181f5c98b",
                "confirmations" : 22,
                "time" : 1470207763,
                "blocktime" : 1470207763
            }

        ]

        self.txs = [TransactionInfo(**tx) for tx in self.txs]

        self.tx_map = {tx.txid: tx for tx in self.txs}
        self.patcher = mock.patch('notification.daemon.get_rpc_connection')
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def clean(self):
        AddressSubscription.objects.all().delete()
        AddressNotification.objects.all().delete()
        LastSeenBlock.objects.all().delete()

    @mock.patch('notification.daemon.AddressNotifyDaemon.get_block')
    @mock.patch('notification.daemon.AddressNotifyDaemon.get_best_block')
    @mock.patch('notification.daemon.AddressNotifyDaemon.get_last_seen_block')
    def test_get_new_blocks(self, mock_get_last_seen_block, mock_get_best_block, mock_get_block):
        mock_get_last_seen_block.return_value = self.blocks[0]
        mock_get_best_block.return_value = self.blocks[-1]
        mock_get_block.side_effect = lambda block_hash: self.block_map[block_hash]

        daemon = AddressNotifyDaemon()
        new_blocks = daemon.get_new_blocks()

        self.assertEqual(len(new_blocks), 3)
        for b1, b2 in zip(new_blocks, self.blocks[1:]):
            self.assertEqual(b1['hash'], b2['hash'])

    @mock.patch('notification.daemon.AddressNotifyDaemon.get_block')
    @mock.patch('notification.daemon.AddressNotifyDaemon.get_best_block')
    @mock.patch('notification.daemon.AddressNotifyDaemon.get_last_seen_block')
    def test_get_new_blocks_with_fork(self, mock_get_last_seen_block, mock_get_best_block, mock_get_block):
        mock_get_last_seen_block.return_value = self.blocks_in_fork_chain[-1]
        mock_get_best_block.return_value = self.blocks[-1]
        mock_get_block.side_effect = lambda block_hash: self.block_map[block_hash]

        daemon = AddressNotifyDaemon()
        new_blocks = daemon.get_new_blocks()

        self.assertEqual(len(new_blocks), 2)
        for b1, b2 in zip(new_blocks, self.blocks[2:]):
            self.assertEqual(b1['hash'], b2['hash'])

    @mock.patch('notification.daemon.AddressNotifyDaemon.get_transaction')
    def test_create_address_txs_map(self, mock_get_transaction):
        mock_get_transaction.side_effect = lambda tx_hash: self.tx_map[tx_hash]

        daemon = AddressNotifyDaemon()
        expected_map = {
            '1GvRsoxx67CzRxvMXofDEVSTX4m29V9kE5': [
                "7cd0c5ac40c6391a982801f1b05df48f056f3fc774543f3bf0fb2568c0b0c566",
                "1bf6fe6ff8e9c68a8d158d955f8c9297f364695ede31308399be1c41db294ad2",
            ],
            '1A4ATaSggTSxrce1sgGP3Aw3mLM4XZprF': [
                "0c70b2b5e6c6618bd397f2d4024367d19264093e5c603d483644f20c183eaf7a",
            ],
            '1Kywza1jgdacR5Wb1xzviTb76hwKyWQjU': [
                "1bf6fe6ff8e9c68a8d158d955f8c9297f364695ede31308399be1c41db294ad2",
                "7cd0c5ac40c6391a982801f1b05df48f056f3fc774543f3bf0fb2568c0b0c566",
                "0c70b2b5e6c6618bd397f2d4024367d19264093e5c603d483644f20c183eaf7a",
            ]
        }
        address_txs_map = daemon.create_address_txs_map(self.blocks[2:3])
        self.assertEqual(set(address_txs_map.keys()), set(expected_map.keys()))
        for address, txs in address_txs_map.iteritems():
            self.assertEqual(set([tx.txid for tx in txs]), set(expected_map[address]))

    def test_create_notification(self):

        address_txs_map = {
            '1GvRsoxx67CzRxvMXofDEVSTX4m29V9kE5': [
                self.tx_map["7cd0c5ac40c6391a982801f1b05df48f056f3fc774543f3bf0fb2568c0b0c566"],
                self.tx_map["1bf6fe6ff8e9c68a8d158d955f8c9297f364695ede31308399be1c41db294ad2"]
            ],
            '1A4ATaSggTSxrce1sgGP3Aw3mLM4XZprF': [
                self.tx_map["0c70b2b5e6c6618bd397f2d4024367d19264093e5c603d483644f20c183eaf7a"],
            ],
            '1Kywza1jgdacR5Wb1xzviTb76hwKyWQjU': [
                self.tx_map["1bf6fe6ff8e9c68a8d158d955f8c9297f364695ede31308399be1c41db294ad2"],
                self.tx_map["7cd0c5ac40c6391a982801f1b05df48f056f3fc774543f3bf0fb2568c0b0c566"],
                self.tx_map["0c70b2b5e6c6618bd397f2d4024367d19264093e5c603d483644f20c183eaf7a"]
            ]
        }

        daemon = AddressNotifyDaemon()
        daemon.create_notifications(address_txs_map)

        notifications = AddressNotification.objects.filter(is_notified=False)
        self.assertEqual(notifications.count(), 2)
        self.assertTrue(
            notifications.filter(tx_hash="7cd0c5ac40c6391a982801f1b05df48f056f3fc774543f3bf0fb2568c0b0c566").exists()
        )
        self.assertTrue(
            notifications.filter(tx_hash="1bf6fe6ff8e9c68a8d158d955f8c9297f364695ede31308399be1c41db294ad2").exists()
        )

    @mock.patch('notification.daemon.ioloop.IOLoop.instance')
    @mock.patch('notification.daemon.AsyncHTTPClient')
    def test_start_notify(self, mock_asynchttpclient, mock_ioloop_instance):

        # mock client.fetch
        mock_asynchttpclient_instance = mock.MagicMock(fetch=mock.MagicMock())
        mock_asynchttpclient.return_value = mock_asynchttpclient_instance

        # mock ioloop.IOLoop.instance().start() and ioloop.IOLoop.instance().stop()
        mock_ioloop_instance_obj = mock.MagicMock(start=mock.MagicMock(), stop=mock.MagicMock())
        mock_ioloop_instance.return_value = mock_ioloop_instance_obj

        # prepare notification to notify
        AddressNotification.objects.bulk_create([
            AddressNotification(
                subscription=self.address_subscription1,
                tx_hash="7cd0c5ac40c6391a982801f1b05df48f056f3fc774543f3bf0fb2568c0b0c566"
            ),
            AddressNotification(
                subscription=self.address_subscription1,
                tx_hash="1bf6fe6ff8e9c68a8d158d955f8c9297f364695ede31308399be1c41db294ad2"
            )
        ])
        daemon = AddressNotifyDaemon()
        daemon.start_notify()

        notifications = AddressNotification.objects.filter(is_notified=False)
        # test fetch call
        call_list = mock_asynchttpclient_instance.fetch.call_args_list
        requests = []
        callback_funcs = []
        for index, notification in enumerate(notifications):
            request = call_list[index][0][0]
            requests.append(request)
            callback_funcs.append(call_list[index][0][1])
            self.assertEqual(request.url, notification.subscription.callback_url)

        # mock responses and manually call all callback_funcs
        responses = [
            HTTPResponse(request=requests[0], code=200),
            HTTPResponse(request=requests[1], code=404)
        ]
        for index, callback in enumerate(callback_funcs):
            callback(responses[index])

        for notification in notifications:
            notification.refresh_from_db()

        # test notification instance is updated in callback func
        self.assertTrue(notifications[0].is_notified)
        self.assertEqual(notifications[0].notification_attempts, 1)

        self.assertFalse(notifications[1].is_notified)
        self.assertEqual(notifications[1].notification_attempts, 1)

        # start and stop is called once and only once
        self.assertEqual(mock_ioloop_instance_obj.stop.call_count, 1)
        self.assertTrue(mock_ioloop_instance_obj.start.call_count, 1)

    @mock.patch('notification.daemon.ioloop.IOLoop.instance')
    @mock.patch('notification.daemon.AsyncHTTPClient')
    def test_start_notify_no_notifications(self, mock_asynchttpclient, mock_ioloop_instance):

        # mock client.fetch
        mock_asynchttpclient_instance = mock.MagicMock(fetch=mock.MagicMock())
        mock_asynchttpclient.return_value = mock_asynchttpclient_instance

        # mock ioloop.IOLoop.instance().start() and ioloop.IOLoop.instance().stop()
        mock_ioloop_instance_obj = mock.MagicMock(start=mock.MagicMock(), stop=mock.MagicMock())
        mock_ioloop_instance.return_value = mock_ioloop_instance_obj

        daemon = AddressNotifyDaemon()
        daemon.start_notify()

        self.assertFalse(mock_ioloop_instance_obj.start.called)
        self.assertFalse(mock_ioloop_instance_obj.stop.called)

