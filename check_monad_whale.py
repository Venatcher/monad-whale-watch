import os
import requests
from web3 import Web3

# Config
RPC_URL = os.getenv("MONAD_RPC_URL")
POOL_ADDRESS = Web3.to_checksum_address("0x5323821de342c56b80c99fbc7cd725f2da8eb87b")
TOKEN0_DECIMALS = 6  # USDC = token0 (selon GeckoTerminal)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
THRESHOLD = float(os.getenv("THRESHOLD_USDC", "10000"))

# Setup Web3
w3 = Web3(Web3.HTTPProvider(RPC_URL))
PAIR_ABI = [{
    "anonymous": False,
    "inputs": [
        {"indexed": True, "internalType": "address","name": "sender","type": "address"},
        {"indexed": False,"internalType": "uint256","name": "amount0In","type": "uint256"},
        {"indexed": False,"internalType": "uint256","name": "amount1In","type": "uint256"},
        {"indexed": False,"internalType": "uint256","name": "amount0Out","type": "uint256"},
        {"indexed": False,"internalType": "uint256","name": "amount1Out","type": "uint256"},
        {"indexed": True, "internalType": "address","name": "to","type": "address"},
    ],
    "name": "Swap","type": "event"
}]
pair_contract = w3.eth.contract(address=POOL_ADDRESS, abi=PAIR_ABI)

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})

def check_swaps():
    send_telegram("Search whale transaction on Monad ...")
    latest = w3.eth.block_number
    logs = pair_contract.events.Swap().get_logs(fromBlock=latest-100, toBlock=latest)
    for e in logs:
        amt0 = e.args.amount0In + e.args.amount0Out
        amt1 = e.args.amount1In + e.args.amount1Out
        usdc_amount = amt0 / (10 ** TOKEN0_DECIMALS)
        if usdc_amount >= THRESHOLD:
            tx = e.transactionHash.hex()
            msg = (f"💰 Uniswap V2 large swap detected:\n"
                   f"USDC volume: {usdc_amount:.2f}\n"
                   f"Tx: https://testnet.monadexplorer.com/tx/{tx}")
            print(msg)
            send_telegram(msg)
    send_telegram("End of the search")

if __name__ == "__main__":
    check_swaps()
