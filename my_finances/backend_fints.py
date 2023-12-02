import os
import json
import logging
from datetime import date
import getpass
from pprint import pprint
from fints.client import FinTS3PinTanClient, SEPAAccount
from fints.utils import minimal_interactive_cli_bootstrap
import fints.segments.statement
from schwifty import IBAN
import mt940.models
import decimal


# Main functions
#===================================================================================================
# TODO Consider using https://github.com/jhermsmeier/fints-institute-db
FINTS_ENDPOINTS = {
    # Sparkasse
    "10050000": "https://banking-be3.s-fints-pt-be.de/fints30",
    # Postbank
    "10010010": "https://hbci.postbank.de/banking/hbci.do",
}


def fints_fetch_transactions(account, from_date, to_date, temp_dir, config, options):
    # This probably belongs somewhere else
    logging.basicConfig(level=logging.WARNING)

    client = FinTS3PinTanClient(
        account["bank_code"],
        account["login_name"],
        getpass.getpass('PIN:'),
        FINTS_ENDPOINTS[account["bank_code"]],
        product_id='32F8A67FE34B57AB8D7E4FE70' # I think the ID is stolen from aqbanking
    )

    if prev_state := config.get("state"):
        client.set_data(bytes.fromhex(prev_state))

    minimal_interactive_cli_bootstrap(client)

    with client:
        # Since PSD2, a TAN might be needed for dialog initialization. Let's check if there is one required
        if client.init_tan_response:
            print("A TAN is required", client.init_tan_response.challenge)
            tan = input('Please enter TAN:')
            client.send_tan(client.init_tan_response, tan)

        account_type = account["account_number"].split(":")[0]
        if account_type == "iban":
            return fetch_account_transactions(client, account, from_date, to_date, temp_dir, config)
        elif account_type == "cc":
            return fetch_card_transactions(client, account, from_date, to_date, temp_dir, config)
        else:
            raise RuntimeError("fints: unsupported account type: " + account_type)


# Fetching account transactions
#===================================================================================================
def fetch_account_transactions(client, account, from_date, to_date, temp_dir, config):
    # Find account
    account_number = account["account_number"].split(":")[1]
    bank_accounts = client.get_sepa_accounts()
    bank_account = None
    for acc in bank_accounts:
        if acc.iban == account_number:
            bank_account = acc
            break

    if bank_account == None:
        raise RuntimeError("fints: Account not found")

    # Fetch transactions
    from_date = date.fromisoformat(from_date) if from_date else None
    to_date = date.fromisoformat(to_date) if to_date else None
    # Returns only booked transactions (not pending ones)
    fints_transactions = client.get_transactions(bank_account, start_date=from_date, end_date=to_date)

    # including_private includes account numbers and names, but no PINs
    config["state"] = client.deconstruct(including_private=True).hex()

    # Save original transaction data
    with open(os.path.join(temp_dir, "transactions.json"), "w") as file:
        data_to_save = [t.data for t in fints_transactions]
        json.dump(data_to_save, file, indent=4, default=default_json_encoder)

    return [entry_from_account_transaction(t.data, account["account_number"]) for t in fints_transactions]


def entry_from_account_transaction(t, local_account):
    remote_account = ""
    if t["applicant_iban"]:
        remote_account = "iban:" + IBAN(t["applicant_iban"]).compact
    elif t["applicant_bin"]: # it seems this can be either BLZ or BIC
        remote_account = "?:" + t["applicant_bin"] + ";"

    return {
        "local_account": local_account,
        "remote_account": remote_account,
        "remote_name": t.get("applicant_name") or "",
        "entry_date": str(t["entry_date"]),
        "valuta_date": str(t["date"]),
        "value": int(str(t["amount"].amount * 100).split(".")[0]),
        "currency": t["currency"],
        "purpose": extract_purpose(t),

        "ultimate_debtor": t.get("deviate_applicant") or "",
        "ultimate_creditor": t.get("deviate_recipient") or "",
        "primanota": t.get("prima_nota") or "",

        "transaction_key": extract_transaction_key(t),
        "transaction_code": (t.get("transaction_code") or "").lstrip("0"), # lstripping 0 to make it the same as aqbanking
        "transaction_text": t.get("posting_text") or "",

        # SEPA
        "creditor_scheme_id": t.get("applicant_creditor_id") or "",
        "mandate_id": t.get("additional_position_reference") or "",
        "end_to_end_ref": t.get("end_to_end_reference") or "",
    }


def extract_purpose(t):
    purpose = t["purpose"] or ""
    if t.get("additional_purpose"):
        purpose += "\n" + t["additional_purpose"]

    return purpose.strip()


def extract_transaction_key(t):
    if t.get("id"):
        # This shows my ignorance. I only know that if I remove the leading "N" then it matches the
        # transactionKey value from aqbanking.
        if t["id"][0] != "N":
            raise RuntimeError("Expected transaction_key to start with N")

        return t["id"][1:]

    return ""


# Fetching credit card transactions
#===================================================================================================
def fetch_card_transactions(client, account, from_date, to_date, temp_dir, config):
    from_date = date.fromisoformat(from_date) if from_date else None
    to_date = date.fromisoformat(to_date) if to_date else None
    card_number = account["account_number"].split(":")[1]

    # TODO Check if this also returns pending transactions
    result = client.get_credit_card_transactions(None, card_number, start_date=from_date, end_date=to_date)
    if len(result) != 1:
        raise RuntimeError("fints: expected exactly one result")
    result = result[0]

    # including_private includes account numbers and names, but no PINs
    config["state"] = client.deconstruct(including_private=True).hex()

    # Save original transaction data
    with open(os.path.join(temp_dir, "transactions.json"), "w") as file:
        json.dump(result, file, indent=4, default=default_json_encoder)

    data = result._additional_data
    if data[0] != card_number:
        raise RuntimeError("fints: Unexpected credit card number")

    transactions = []
    for i in range(5, len(data)):
        transactions.append(entry_from_card_transaction(data[i], card_number))

    return transactions


def entry_from_card_transaction(t, card_number):
    return {
        "local_account": "cc:" + card_number,
        "remote_account": "",
        "remote_name": "",
        "entry_date": cc_compact_date_to_iso(t[2]),
        "valuta_date": cc_compact_date_to_iso(t[1]),
        "value": cc_parse_amount(t[8], t[10]),
        "currency": t[9],
        "purpose": cc_extract_purpose(t),

        "original_value": cc_parse_amount(t[4], t[6]),
        "original_currency": t[5],
        "exchange_rate": str(decimal.Decimal(t[7].replace(",", "."))),

        "cc_entry_ref": t[21], # Is this actually a unique ID?
        "cc_billing_ref": t[23],

        "ultimate_debtor": "",
        "ultimate_creditor": "",
        "primanota": "",
        "transaction_key": "",
        "transaction_code": "",
        "transaction_text": "",
        "creditor_scheme_id": "",
        "mandate_id": "",
        "end_to_end_ref": "",
    }


def cc_compact_date_to_iso(date):
    return date[0:4] +"-"+ date[4:6] +"-"+ date[6:8]

def cc_parse_amount(amount, debit_or_credit):
    d = decimal.Decimal(amount.replace(",", "."))
    if debit_or_credit == "D":
        d *= -1
    elif debit_or_credit != "C":
        raise RuntimeError("fints: debit or credit: expected either 'D' or 'C'")

    return int(str(d*100).split(".")[0])

def cc_extract_purpose(t):
    purpose = t[11] or ""
    if t[12]:
        purpose += "\n" + t[12] # `t[12]` contains to additional purpose
    if len(t) > 25 and t[25]:
        purpose += "\n" + t[25] # `t[25]`: AEE+Buchungsreferenz

    return purpose


# Utils
#===================================================================================================
def default_json_encoder(x):
    if isinstance(x, mt940.models.Amount):
        return x.__dict__

    if isinstance(x, fints.segments.statement.DIKKU2):
        return {
            "header": str(x.header),
            "_additional_data": x._additional_data,
        }

    if isinstance(x, date) or isinstance(x, decimal.Decimal):
        return str(x)

    raise TypeError("json encoding: unsupported type " + str(type(x)))

