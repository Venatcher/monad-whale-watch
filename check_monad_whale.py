import os
import requests
from web3 import Web3

# === Configuration ===
RPC_URL = os.getenv("MONAD_RPC_URL")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
THRESHOLD = float(os.getenv("THRESHOLD_USDC") or "10000")  # default fallback

# Uniswap V2 Pair Contract Address
PAIR_ADDRESS = Web3.to_checksum_address("0x5323821de342c56b80c99fbc7cd725f2da8eb87b")

# USDC Testnet
USDC_ADDRESS = "0xf817257fed379853cDe0fa4F97AB987181B1E5Ea"

# Uniswap V2 Pair ABI (only the parts we need)
UNISWAP_V2_PAIR_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "sender", "type": "address"},
            {"indexed": False, "name": "amount0In", "type": "uint256"},
            {"indexed": False, "name": "amount1In", "type": "uint256"},
            {"indexed": False, "name": "amount0Out", "type": "uint256"},
            {"indexed": False, "name": "amount1Out", "type": "uint256"},
            {"indexed": True, "name": "to", "type": "address"},
        ],
        "name": "Swap",
        "type": "event",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "token0",
        "outputs": [{"name": "", "type": "address"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "token1",
        "outputs": [{"name": "", "type": "address"}],
        "type": "function"
    }
]

# === Initialisation Web3 ===
w3 = Web3(Web3.HTTPProvider(RPC_URL))
pair_contract = w3.eth.contract(address=PAIR_ADDRESS, abi=UNISWAP_V2_PAIR_ABI)

# === Détermination de la position d’USDC ===
token0 = pair_contract.functions.token0().call()
token1 = pair_contract.functions.token1().call()

usdc_is_token0 = token0.lower() == USDC_ADDRESS.lower()

# === Fonction Telegram ===
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Erreur en envoyant sur Telegram:", e)

# === Surveillance des swaps ===
def check_swaps():
    latest = w3.eth.block_number
    from_block = max(latest - 100, 0)

    try:
        logs = pair_contract.events.Swap().get_logs(from_block=from_block, to_block=latest)
    except Exception as e:
        print("Erreur pendant get_logs:", e)
        return

    for e in logs:
        # Sélectionne le bon côté du swap (USDC)
        if usdc_is_token0:
            usdc_raw = e.args.amount0In + e.args.amount0Out
        else:
            usdc_raw = e.args.amount1In + e.args.amount1Out

        usdc_amount = usdc_raw / 10**6

        if usdc_amount >= THRESHOLD:
            tx_hash = e.transactionHash.hex()
            if not tx_hash.startswith("0x"):
                tx_hash = "0x" + tx_hash

            msg = (
                f"🐋 Uniswap V2 large swap detected:\n"
                f"USDC volume: {usdc_amount:.2f}\n"
                f"Tx: https://testnet.monadexplorer.com/tx/{tx_hash}"
            )
            print(msg)
            send_telegram(msg)

# === Main ===
if __name__ == "__main__":
    check_swaps()
