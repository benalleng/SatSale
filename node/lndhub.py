import json
import logging
import qrcode
import time
from decimal import Decimal
from typing import Tuple

import config


class lndhub:
    def __init__(self, node_config: dict) -> None:
        from blue_wallet_client import BlueWalletClient

        self.config = node_config
        self.is_onchain = False

        for i in range(config.connection_attempts):
            try:
                logging.info("Attempting to initialize LNDHub client...")
                self.lndhub = BlueWalletClient(
                    bluewallet_login=self.config["bw_login"],
                    bluewallet_password=self.config["bw_password"],
                    root_url=self.config["backend_url"])
                logging.info("Getting LNDHub node info...")
                logging.info(json.dumps(self.get_info()))
                logging.info("Sucessfully contacted LNDHub.")
                break

            except Exception as e:
                logging.error(e)
                if i < 5:
                    time.sleep(2)
                else:
                    time.sleep(60)
                logging.info(
                    "Attempting again... {}/{}...".format(
                        i + 1, config.connection_attempts
                    )
                )
        else:
            raise Exception("Could not connect to LNDHub.")

        logging.info("Ready for payments requests.")
        return

    def get_info(self) -> dict:
        return self.lndhub.get_node_info()

    def create_qr(self, uuid: str, address: str, value: float) -> None:
        qr_str = "{}".format(address.upper())
        img = qrcode.make(qr_str)
        img.save("static/qr_codes/{}.png".format(uuid))
        return

    def create_lndhub_invoice(self, btc_amount: float, memo: str = None,
                              expiry: int = 3600) -> Tuple[str, str]:
        sats_amount = round(Decimal(btc_amount) * 10 ** 8)
        ret = self.lndhub.create_invoice(amt=sats_amount, memo=memo)
        return ret["payment_request"], ret["r_hash"]

    def get_address(self, btc_amount: float, label: str,
                    expiry: int) -> Tuple[str, str]:
        return self.create_lndhub_invoice(btc_amount, label, expiry)

    def pay_invoice(self, invoice: str) -> None:
        try:
            self.lndhub.payinvoice(invoice)
        except Exception as e:
            logging.error(e.repr())

    def check_payment(self, rhash: str) -> Tuple[float, float]:
        invoice = self.lndhub.lookup_invoice(rhash)

        if invoice["ispaid"]:
            conf_paid = (int(invoice["amt"]) + 1) / (10 ** 8)
            unconf_paid = 0
        else:
            conf_paid = 0
            unconf_paid = 0

        return conf_paid, unconf_paid
