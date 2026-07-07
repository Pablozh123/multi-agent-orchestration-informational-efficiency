"""USDC.e in pUSD wrappen (CLOB-V2-Collateral, 1:1, offizieller Onramp).

Ablauf: USDC.e-Approve fuer den CollateralOnramp, dann
wrap(USDC.e, eigene Adresse, Betrag). Adressen verifiziert gegen
docs.polymarket.com/resources/contracts (Stand 2026-07-03).

Aufruf: python -m operations.pipeline.wrap_pusd --usd 20 [--check]
"""

from __future__ import annotations

import argparse
import os

USDC_E = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
PUSD = "0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB"
ONRAMP = "0x93070a847efEf7F70739046A929D47a521F5B8ee"

ERC20_ABI = [
    {"name": "balanceOf", "type": "function", "stateMutability": "view",
     "inputs": [{"name": "", "type": "address"}],
     "outputs": [{"name": "", "type": "uint256"}]},
    {"name": "allowance", "type": "function", "stateMutability": "view",
     "inputs": [{"name": "owner", "type": "address"},
                {"name": "spender", "type": "address"}],
     "outputs": [{"name": "", "type": "uint256"}]},
    {"name": "approve", "type": "function", "stateMutability": "nonpayable",
     "inputs": [{"name": "spender", "type": "address"},
                {"name": "amount", "type": "uint256"}],
     "outputs": [{"name": "", "type": "bool"}]},
]
ONRAMP_ABI = [
    {"name": "wrap", "type": "function", "stateMutability": "nonpayable",
     "inputs": [{"name": "_asset", "type": "address"},
                {"name": "_to", "type": "address"},
                {"name": "_amount", "type": "uint256"}],
     "outputs": []},
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--usd", type=float, default=20.0)
    parser.add_argument("--check", action="store_true", help="nur Balancen zeigen")
    argv = parser.parse_args()

    from dotenv import load_dotenv
    from web3 import Web3

    load_dotenv()
    rpc = os.environ.get("POLYGON_RPC_URL", "https://polygon-bor-rpc.publicnode.com")
    if "polygon-rpc.com" in rpc:
        rpc = "https://polygon-bor-rpc.publicnode.com"
    w3 = Web3(Web3.HTTPProvider(rpc))
    konto = w3.eth.account.from_key(os.environ["POLY_PRIVATE_KEY"])
    adresse = konto.address

    usdce = w3.eth.contract(Web3.to_checksum_address(USDC_E), abi=ERC20_ABI)
    pusd = w3.eth.contract(Web3.to_checksum_address(PUSD), abi=ERC20_ABI)
    onramp = w3.eth.contract(Web3.to_checksum_address(ONRAMP), abi=ONRAMP_ABI)

    b_usdce = usdce.functions.balanceOf(adresse).call() / 1e6
    b_pusd = pusd.functions.balanceOf(adresse).call() / 1e6
    print(f"Wallet: {adresse}")
    print(f"USDC.e: {b_usdce} | pUSD: {b_pusd}")
    if argv.check:
        return

    betrag = int(argv.usd * 1e6)
    if b_usdce * 1e6 < betrag:
        raise SystemExit(f"USDC.e-Balance {b_usdce} < {argv.usd}")

    def sende(fn) -> None:
        gas_preis = w3.eth.gas_price
        prio = max(w3.to_wei(30, "gwei"), int(gas_preis * 0.2))
        tx = fn.build_transaction({
            "from": adresse,
            "nonce": w3.eth.get_transaction_count(adresse, "latest"),
            "gas": 200_000,
            "maxFeePerGas": int(gas_preis * 2) + prio,
            "maxPriorityFeePerGas": prio,
        })
        signiert = konto.sign_transaction(tx)
        h = w3.eth.send_raw_transaction(signiert.raw_transaction)
        print(f"  tx: {h.hex()}")
        r = w3.eth.wait_for_transaction_receipt(h, timeout=300)
        if r.status != 1:
            raise SystemExit(f"Transaktion fehlgeschlagen: {h.hex()}")

    erlaubt = usdce.functions.allowance(
        adresse, Web3.to_checksum_address(ONRAMP)).call()
    if erlaubt < betrag:
        print(f"Approve Onramp fuer {argv.usd} USDC.e ...")
        sende(usdce.functions.approve(Web3.to_checksum_address(ONRAMP), betrag))

    print(f"wrap({argv.usd} USDC.e -> pUSD) ...")
    sende(onramp.functions.wrap(
        Web3.to_checksum_address(USDC_E), adresse, betrag))

    print(f"USDC.e: {usdce.functions.balanceOf(adresse).call() / 1e6} | "
          f"pUSD: {pusd.functions.balanceOf(adresse).call() / 1e6}")


if __name__ == "__main__":
    main()
