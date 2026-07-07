"""Einmaliges Setup des Deposit-Wallet-Flows (CLOB V2, Pflicht seit 2026).

Schritte:
1. CLOB-API-Creds ableiten (L2-Auth).
2. Builder-API-Key selbst ausstellen (noetig fuer den Relayer) und in
   .env ablegen (BUILDER_API_KEY/SECRET/PASS_PHRASE), falls nicht da.
3. Deposit-Wallet-Adresse ableiten und via Relayer deployen (gasless).
4. pUSD vom EOA auf die Deposit-Wallet transferieren (--usd).
5. Approvals AUS der Deposit-Wallet (pUSD + CTF fuer beide V2-Exchanges)
   als Relayer-WALLET-Batch.
6. Adresse nach data/live/allin_july3/deposit_wallet.json schreiben.

Aufruf: python -m operations.pipeline.setup_deposit_wallet [--usd 20]
"""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone

from operations.pipeline import config

RELAYER_URL = "https://relayer-v2.polymarket.com"
RPC_URL = "https://polygon-bor-rpc.publicnode.com"
PUSD = "0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB"
CTF = "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"
EXCHANGE_V2 = "0xE111180000d2663C0091e4f400237545B87B996B"
NEG_RISK_EXCHANGE_V2 = "0xe2222d279d744050d28e00520010520000310F59"
MAX_UINT = 2**256 - 1
ENV_PFAD = config.REPO_ROOT / ".env"
WALLET_JSON = config.REPO_ROOT / "data" / "live" / "deposit_wallet.json"


def _env_nachladen() -> None:
    from dotenv import load_dotenv

    load_dotenv(ENV_PFAD, override=True)


def builder_creds_besorgen(clob) -> dict:
    """Builder-Key aus .env oder neu ausstellen (und in .env anhaengen)."""
    if os.environ.get("BUILDER_API_KEY"):
        return {
            "key": os.environ["BUILDER_API_KEY"],
            "secret": os.environ["BUILDER_SECRET"],
            "passphrase": os.environ["BUILDER_PASS_PHRASE"],
        }
    antwort = clob.create_builder_api_key()
    key = antwort.get("apiKey") or antwort.get("key")
    secret = antwort.get("secret")
    passphrase = antwort.get("passphrase")
    if not (key and secret and passphrase):
        raise SystemExit(f"Builder-Key-Antwort unvollstaendig: {list(antwort)}")
    with open(ENV_PFAD, "a", encoding="utf-8") as f:
        f.write(f"\nBUILDER_API_KEY={key}\nBUILDER_SECRET={secret}\n"
                f"BUILDER_PASS_PHRASE={passphrase}\n")
    print("Builder-API-Key ausgestellt und in .env gespeichert.")
    _env_nachladen()
    return {"key": key, "secret": secret, "passphrase": passphrase}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--usd", type=float, default=20.0,
                        help="pUSD-Betrag fuer die Deposit-Wallet")
    argv = parser.parse_args()

    from dotenv import load_dotenv

    load_dotenv()
    pk = os.environ["POLY_PRIVATE_KEY"]

    from py_clob_client_v2.client import ClobClient

    clob = ClobClient(config.CLOB_HOST, key=pk, chain_id=config.CHAIN_ID)
    clob.set_api_creds(clob.create_or_derive_api_key())
    print("CLOB-Creds ok.")

    creds = builder_creds_besorgen(clob)

    from py_builder_relayer_client.client import RelayClient
    from py_builder_signing_sdk.config import BuilderApiKeyCreds, BuilderConfig

    builder_config = BuilderConfig(
        local_builder_creds=BuilderApiKeyCreds(
            key=creds["key"], secret=creds["secret"],
            passphrase=creds["passphrase"],
        )
    )
    relayer = RelayClient(RELAYER_URL, config.CHAIN_ID, pk, builder_config,
                          rpc_url=RPC_URL)
    deposit = relayer.get_expected_deposit_wallet()
    print(f"Deposit-Wallet (deterministisch): {deposit}")

    from web3 import Web3

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    code = w3.eth.get_code(Web3.to_checksum_address(deposit))
    if len(code) > 0:
        print("Deposit-Wallet bereits deployed.")
    else:
        print("Deploye Deposit-Wallet via Relayer ...")
        antwort = relayer.deploy_deposit_wallet()
        antwort.wait()
        print("Deployed.")

    # pUSD auf die Deposit-Wallet bringen (EOA-Transfer, kostet Gas).
    erc20_abi = [
        {"name": "balanceOf", "type": "function", "stateMutability": "view",
         "inputs": [{"name": "", "type": "address"}],
         "outputs": [{"name": "", "type": "uint256"}]},
        {"name": "transfer", "type": "function", "stateMutability": "nonpayable",
         "inputs": [{"name": "to", "type": "address"},
                    {"name": "amount", "type": "uint256"}],
         "outputs": [{"name": "", "type": "bool"}]},
        {"name": "approve", "type": "function", "stateMutability": "nonpayable",
         "inputs": [{"name": "spender", "type": "address"},
                    {"name": "amount", "type": "uint256"}],
         "outputs": [{"name": "", "type": "bool"}]},
        {"name": "allowance", "type": "function", "stateMutability": "view",
         "inputs": [{"name": "owner", "type": "address"},
                    {"name": "spender", "type": "address"}],
         "outputs": [{"name": "", "type": "uint256"}]},
    ]
    erc1155_abi = [
        {"name": "setApprovalForAll", "type": "function",
         "stateMutability": "nonpayable",
         "inputs": [{"name": "operator", "type": "address"},
                    {"name": "approved", "type": "bool"}], "outputs": []},
        {"name": "isApprovedForAll", "type": "function",
         "stateMutability": "view",
         "inputs": [{"name": "owner", "type": "address"},
                    {"name": "operator", "type": "address"}],
         "outputs": [{"name": "", "type": "bool"}]},
    ]
    konto = w3.eth.account.from_key(pk)
    pusd = w3.eth.contract(Web3.to_checksum_address(PUSD), abi=erc20_abi)
    ctf = w3.eth.contract(Web3.to_checksum_address(CTF), abi=erc1155_abi)

    dep = Web3.to_checksum_address(deposit)
    bal_dep = pusd.functions.balanceOf(dep).call() / 1e6
    print(f"pUSD auf Deposit-Wallet: {bal_dep}")
    betrag = int(argv.usd * 1e6)
    if bal_dep * 1e6 < betrag:
        fehl = betrag - int(bal_dep * 1e6)
        print(f"Transferiere {fehl / 1e6} pUSD auf die Deposit-Wallet ...")
        gas_preis = w3.eth.gas_price
        prio = max(w3.to_wei(30, "gwei"), int(gas_preis * 0.2))
        tx = pusd.functions.transfer(dep, fehl).build_transaction({
            "from": konto.address,
            "nonce": w3.eth.get_transaction_count(konto.address, "pending"),
            "gas": 120_000,
            "maxFeePerGas": int(gas_preis * 2) + prio,
            "maxPriorityFeePerGas": prio,
        })
        signiert = konto.sign_transaction(tx)
        h = w3.eth.send_raw_transaction(signiert.raw_transaction)
        r = w3.eth.wait_for_transaction_receipt(h, timeout=300)
        if r.status != 1:
            raise SystemExit(f"pUSD-Transfer fehlgeschlagen: {h.hex()}")
        print(f"Transfer ok: {h.hex()}")

    # Approvals aus der Deposit-Wallet (ein Relayer-Batch, gasless).
    noetig = []
    for spender in (EXCHANGE_V2, NEG_RISK_EXCHANGE_V2):
        sp = Web3.to_checksum_address(spender)
        if pusd.functions.allowance(dep, sp).call() == 0:
            noetig.append((PUSD, pusd.encode_abi("approve", args=[sp, MAX_UINT])))
        if not ctf.functions.isApprovedForAll(dep, sp).call():
            noetig.append((CTF, ctf.encode_abi("setApprovalForAll", args=[sp, True])))

    if noetig:
        from py_builder_relayer_client.models import DepositWalletCall, TransactionType

        print(f"Sende Approval-Batch mit {len(noetig)} Calls via Relayer ...")
        nonce_payload = relayer.get_nonce(
            relayer.signer.address(), TransactionType.WALLET.value
        )
        calls = [DepositWalletCall(target=ziel, value="0", data=daten)
                 for ziel, daten in noetig]
        antwort = relayer.execute_deposit_wallet_batch(
            calls=calls,
            wallet_address=deposit,
            nonce=str(nonce_payload["nonce"]),
            deadline=str(int(time.time()) + 600),
        )
        antwort.wait()
        print("Approvals gesetzt.")
    else:
        print("Approvals bereits vollstaendig.")

    WALLET_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(WALLET_JSON, "w", encoding="utf-8") as f:
        json.dump({
            "deposit_wallet": deposit,
            "owner_eoa": konto.address,
            "erstellt_am_utc": datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"),
        }, f, indent=1)
    print(f"Geschrieben: {WALLET_JSON}")

    print("\nStatus:")
    print(f"  pUSD Deposit-Wallet: {pusd.functions.balanceOf(dep).call() / 1e6}")
    for spender in (EXCHANGE_V2, NEG_RISK_EXCHANGE_V2):
        sp = Web3.to_checksum_address(spender)
        print(f"  {spender[:10]}...: pUSD-Allowance="
              f"{'ok' if pusd.functions.allowance(dep, sp).call() > 0 else 'FEHLT'}"
              f", CTF={'ok' if ctf.functions.isApprovedForAll(dep, sp).call() else 'FEHLT'}")


if __name__ == "__main__":
    main()
