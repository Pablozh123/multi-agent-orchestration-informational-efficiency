"""Einmaliges Setzen der On-Chain-Allowances fuer den CLOB-Handel (Polygon).

Approvals (nur falls noch nicht gesetzt):
- USDC (0x2791...) approve fuer CTF Exchange, NegRisk Exchange, NegRisk Adapter
- ConditionalTokens (0x4D97...) setApprovalForAll fuer dieselben Spender

Benoetigt .env: POLY_PRIVATE_KEY und POLYGON_RPC_URL. Sendet nur dann
Transaktionen, wenn eine Allowance fehlt. Gas zahlt die Wallet (POL).

Aufruf: python -m operations.pipeline.set_allowances [--check]
--check zeigt nur den Status, sendet nichts.
"""

from __future__ import annotations

import argparse
import os

# CLOB V2 (seit 2026-04-28): Collateral ist pUSD, gehandelt wird ueber die
# V2-Exchanges. Adressen aus py_clob_client_v2.config, gegengeprueft mit
# docs.polymarket.com/resources/contracts.
USDC = "0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB"  # pUSD (V2-Collateral)
CTF = "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"
SPENDER = {
    "ctf_exchange_v2": "0xE111180000d2663C0091e4f400237545B87B996B",
    "neg_risk_exchange_v2": "0xe2222d279d744050d28e00520010520000310F59",
}

ERC20_ABI = [
    {"name": "allowance", "type": "function", "stateMutability": "view",
     "inputs": [{"name": "owner", "type": "address"},
                {"name": "spender", "type": "address"}],
     "outputs": [{"name": "", "type": "uint256"}]},
    {"name": "approve", "type": "function", "stateMutability": "nonpayable",
     "inputs": [{"name": "spender", "type": "address"},
                {"name": "amount", "type": "uint256"}],
     "outputs": [{"name": "", "type": "bool"}]},
]
ERC1155_ABI = [
    {"name": "isApprovedForAll", "type": "function", "stateMutability": "view",
     "inputs": [{"name": "owner", "type": "address"},
                {"name": "operator", "type": "address"}],
     "outputs": [{"name": "", "type": "bool"}]},
    {"name": "setApprovalForAll", "type": "function",
     "stateMutability": "nonpayable",
     "inputs": [{"name": "operator", "type": "address"},
                {"name": "approved", "type": "bool"}],
     "outputs": []},
]

MAX_UINT = 2**256 - 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="nur Status zeigen")
    argv = parser.parse_args()

    from dotenv import load_dotenv
    from web3 import Web3

    load_dotenv()
    key = os.environ.get("POLY_PRIVATE_KEY")
    rpc = os.environ.get("POLYGON_RPC_URL", "https://polygon-rpc.com")
    if not key:
        raise SystemExit("POLY_PRIVATE_KEY fehlt in .env")

    w3 = Web3(Web3.HTTPProvider(rpc))
    konto = w3.eth.account.from_key(key)
    adresse = konto.address
    print(f"Wallet: {adresse}")
    print(f"POL-Balance: {w3.from_wei(w3.eth.get_balance(adresse), 'ether')}")

    usdc = w3.eth.contract(Web3.to_checksum_address(USDC), abi=ERC20_ABI)
    ctf = w3.eth.contract(Web3.to_checksum_address(CTF), abi=ERC1155_ABI)

    # Lokale Nonce-Zaehlung: load-balancierte RPCs liefern 'latest' teils
    # verzoegert, was bei Tx-Serien zu 'replacement underpriced' fuehrt.
    naechste_nonce = w3.eth.get_transaction_count(adresse, "pending")

    def sende(fn) -> None:
        nonlocal naechste_nonce
        # Dynamische Gebuehren: doppelter aktueller Gaspreis, damit die Tx
        # auch bei Lastspitzen zuegig gemined wird (Polygon, Cent-Betraege).
        gas_preis = w3.eth.gas_price
        prio = max(w3.to_wei(30, "gwei"), int(gas_preis * 0.2))
        tx = fn.build_transaction({
            "from": adresse,
            "nonce": naechste_nonce,
            "gas": 100_000,
            "maxFeePerGas": int(gas_preis * 2) + prio,
            "maxPriorityFeePerGas": prio,
        })
        signiert = konto.sign_transaction(tx)
        h = w3.eth.send_raw_transaction(signiert.raw_transaction)
        print(f"  tx: {h.hex()}")
        w3.eth.wait_for_transaction_receipt(h, timeout=180)
        naechste_nonce += 1

    for name, spender in SPENDER.items():
        sp = Web3.to_checksum_address(spender)
        erlaubt = usdc.functions.allowance(adresse, sp).call()
        ok1155 = ctf.functions.isApprovedForAll(adresse, sp).call()
        print(f"{name}: USDC-Allowance={'ok' if erlaubt > 0 else 'FEHLT'}, "
              f"CTF-Approval={'ok' if ok1155 else 'FEHLT'}")
        if argv.check:
            continue
        if erlaubt == 0:
            print(f"  setze USDC-Approve fuer {name} ...")
            sende(usdc.functions.approve(sp, MAX_UINT))
        if not ok1155:
            print(f"  setze CTF setApprovalForAll fuer {name} ...")
            sende(ctf.functions.setApprovalForAll(sp, True))
    print("fertig.")


if __name__ == "__main__":
    main()
