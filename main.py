import random
import time

from loguru import logger
from web3 import Web3

'------------------------------------------------ НАСТРОЙКИ -----------------------------------------------------------'

increase_gas = 1.1  # Збільшення газу на 10%
token_threshold = [2, 5]  # Скільки відсотків токена залишиться на гаманці
delay_between_accounts = [30, 60]  # Затримка між акаунтами (в секундах)
target_chains = ['ARB', 'AVAX']  # В якому чейні вивід на окекс
delay_between_chains = [30, 60]  # Затримка між чейнами (в секундах)
# ARB, AVAX, BASE, BNB, CELO, CORE, FTM, LINEA, MATIC, MOVR, OP, ZK

'-------------------------------------------------- ЧЕЙНИ -------------------------------------------------------------'

chains = {
    'ARB': {
        'rpc': 'https://arbitrum.llamarpc.com',
        'chainId': 42161
    },
    'AVAX': {
        'rpc': 'https://avalanche.drpc.org',
        'chainId': 43114
    },
    'BASE': {
        'rpc': 'https://base-pokt.nodies.app',
        'chainId': 8453
    },
    'BNB': {
        'rpc': 'https://bsc-pokt.nodies.app',
        'chainId': 56
    },
    'CELO': {
        'rpc': 'https://1rpc.io/celo',
        'chainId': 42220
    },
    'CORE': {
        'rpc': 'https://core.drpc.org',
        'chainId': 1116
    },
    'FTM': {
        'rpc': 'https://fantom-pokt.nodies.app',
        'chainId': 250
    },
    'LINEA': {
        'rpc': 'https://linea.decubate.com',
        'chainId': 59144
    },
    'MATIC': {
        'rpc': 'https://polygon-pokt.nodies.app',
        'chainId': 137
    },
    'MOVR': {
        'rpc': 'wss://moonriver-rpc.publicnode.com',
        'chainId': 1285
    },
    'OP': {
        'rpc': 'wss://optimism-rpc.publicnode.com',
        'chainId': 10
    },
    'ZK': {
        'rpc': 'https://1rpc.io/zksync2-era',
        'chainId': 324
    }
}

with open('accounts/private_keys.txt', 'r') as private_keys_file:
    private_keys = [line.strip() for line in private_keys_file]

with open('accounts/deposit_addresses.txt', 'r') as deposit_addresses_file:
    deposit_addresses = [line.strip() for line in deposit_addresses_file]


def main():
    for private_key, deposit_address in zip(private_keys, deposit_addresses):
        for target_chain in target_chains:
            chain_config = chains[target_chain]
            w3 = Web3(Web3.HTTPProvider(chain_config['rpc']))

            address = Web3.to_checksum_address(w3.eth.account.from_key(private_key).address)

            balance_wei = w3.eth.get_balance(address)
            threshold_percentage = random.uniform(token_threshold[0], token_threshold[1])
            threshold_wei = int(balance_wei * (threshold_percentage / 100))
            value_to_send = balance_wei - threshold_wei

            if value_to_send <= 0:
                logger.warning(f'{address} | Insufficient balance to send transaction on {target_chain}')
                continue

            logger.info(f'{address} | Sending {value_to_send / 1e18} {target_chain} to {deposit_address}')

            tx = {
                'chainId': chain_config['chainId'],
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
                    logger.success(f'{address} | {target_chain} transaction was successful | Hash: {tx_hash.hex()}')
                    logger.info(f'Transaction URL: {explorer_url(target_chain, tx_hash.hex())}')
                else:
                    logger.warning(f'{address} | {target_chain} transaction failed | {tx_hash.hex()}')
            except Exception as error:
                logger.warning(f'{address} | {target_chain} transaction failed | Error: {error}')

            chain_delay = random.randint(delay_between_chains[0], delay_between_chains[1])
            logger.info(f"Sleeping for {chain_delay} seconds before processing the next chain")
            time.sleep(chain_delay)

        account_delay = random.randint(delay_between_accounts[0], delay_between_accounts[1])
        logger.info(f'Sleeping for {account_delay} seconds')
        time.sleep(account_delay)

    logger.info("Finished processing all accounts")


def verif_tx(w3, address, tx_hash):
    try:
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=200)
        return receipt.status == 1
    except Exception as error:
        logger.error(f'{address} | Unexpected error in <verif_tx> function | {error}')
        return False


def check_keys_and_addresses():
    return len(private_keys) == len(deposit_addresses)


def explorer_url(chain_name, tx_hash):
    explorers = {
        'ARB': f'https://arbiscan.io/tx/{tx_hash}',
        'AVAX': f'https://snowtrace.io/tx/{tx_hash}',
        'BASE': f'https://basescan.org/tx/{tx_hash}',
        'BNB': f'https://bscscan/tx/{tx_hash}',
        'CELO': f'https://explorer.celo.org/mainnet/tx/{tx_hash}',
        'CORE': f'https://scan.coredao.org/tx/{tx_hash}',
        'FTM': f'https://ftmscan.com/tx/{tx_hash}',
        'LINEA': f'https://lineascan.build/tx/{tx_hash}',
        'MATIC': f'https://polygonscan.com/tx/{tx_hash}',
        'MOVR': f'https://moonriver.moonscan.io/tx/{tx_hash}',
        'OP': f'https://optimistic.etherscan.io/tx/{tx_hash}',
        'ZK': f'https://explorer.zksync.io/tx/{tx_hash}'
    }
    return explorers.get(chain_name, '#')


if __name__ == "__main__":
    if check_keys_and_addresses():
        main()
    else:
        logger.warning("The number of private keys does not match with deposit addresses")
