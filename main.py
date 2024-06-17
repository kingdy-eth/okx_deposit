import random
import time

from web3 import Web3
from loguru import logger

increase_gas = 1.1
eth_threshold = [0.00023, 0.00053]  # скільки eth залишиться на гаманці
decimal_places = 5  # кількість цифр після 0.
delay_between_accounts = [30, 60]  # затримка між акаунтами

with open('accounts/private_keys.txt', 'r') as private_keys_file:
    private_keys = [line.strip() for line in private_keys_file]

with open('accounts/deposit_addresses.txt', 'r') as deposit_addresses_file:
    deposit_addresses = [line.strip() for line in deposit_addresses_file]


def main():
    w3 = Web3(Web3.HTTPProvider("https://mainnet.era.zksync.io"))

    for private_key, deposit_address in zip(private_keys, deposit_addresses):
        address = Web3.to_checksum_address(w3.eth.account.from_key(private_key).address)

        balance_wei = w3.eth.get_balance(address)
        amount = round(random.uniform(eth_threshold[0], eth_threshold[1]), decimal_places)
        threshold_wei = int(amount * 1e18)
        value_to_send = balance_wei - threshold_wei

        if value_to_send <= 0:
            logger.warning(f'{address} | Insufficient balance to send transaction')
            continue

        logger.info(f'{address} | Sending {value_to_send / 1e18} ETH to {deposit_address}')

        tx = {
            'chainId': 324,
            'nonce': w3.eth.get_transaction_count(address),
            'from': address,
            'to': Web3.to_checksum_address(deposit_address),
            'value': value_to_send,
            'gasPrice': w3.eth.gas_price
        }

        try:
            tx['gas'] = int(w3.eth.estimate_gas(tx) * increase_gas)
            sign = w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = w3.eth.send_raw_transaction(sign.rawTransaction)

            if verif_tx(w3, address, tx_hash):
                logger.success(f'{address} | Transaction was successful | Hash: {tx_hash.hex()}')
                logger.info(f'Transaction URL: https://explorer.zksync.io/tx/{tx_hash.hex()}')
            else:
                logger.warning(f'{address} | Transaction failed | {tx_hash.hex()}')
        except Exception as error:
            logger.warning(f'{address} | Transaction failed | Error: {error}')

        delay = random.randint(delay_between_accounts[0], delay_between_accounts[1])
        logger.info(f'Sleeping for {delay} seconds')
        time.sleep(delay)

    logger.info("Finished processing all accounts")


def verif_tx(w3, address, tx_hash):
    try:
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=200)
        if 'status' in receipt and receipt['status'] == 1:
            return True
        else:
            return False
    except Exception as error:
        logger.error(f'{address} | Unexpected error in <verif_tx> function | {error}')
        return False


def check_keys_and_addresses():
    if len(private_keys) != len(deposit_addresses):
        return False
    return True


if __name__ == "__main__":
    if check_keys_and_addresses():
        main()
    else:
        logger.warning("The number of private keys does not match with deposit addresses")
