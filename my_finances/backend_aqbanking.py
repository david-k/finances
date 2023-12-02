import os
import subprocess
import csv
from schwifty import IBAN


#===================================================================================================
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))


# Main functions
#===================================================================================================
# Depends on external script `chiptan_qr.sh`
def aqbanking_fetch_transactions(account, from_date, to_date, temp_dir, config, options):
    # Execute the `aqbanking-cli` command-line utility to fetch the transactions
    ctx_filename = os.path.join(temp_dir, "transactions.ctx")
    aqbanking_command = [
        "aqbanking-cli",
        "--opticaltan=chiptan_qr.sh",
        "request",
        "--account=" + parse_iban(account["account_number"]).account_code.lstrip("0"),
        "--transactions",
        "-c", ctx_filename
    ]
    if from_date != None:
        aqbanking_command.append("--fromdate=" + from_date.replace("-", ""))
    if to_date != None:
        aqbanking_command.append("--todate=" + to_date.replace("-", ""))

    subprocess.run(aqbanking_command)

    # Convert aqbanking's context file to CSV
    csv_filename = os.path.join(temp_dir, "transactions.csv")
    subprocess.run([
        "aqbanking-cli",
        "export",
        "--profile-file=" + os.path.join(SCRIPT_DIR, "../actually_full.conf") , # export all fields
        "-c", ctx_filename,
        "-o", csv_filename
    ])

    transactions = []
    with open(csv_filename, newline='') as csvfile:
        for t in csv.DictReader(csvfile, delimiter=";"):
            # Transactions with type=notedStatement behave a bit inconsistently. For example, they
            # behave inconsistently with respect to --fromdate and --todate filters, and their data
            # is still subject to change. See notes from 28.06.2023.
            if t["type"] == "notedStatement":
                continue

            transactions.append(entry_from_csv_row(t, account["account_number"]))

    return transactions


# Utils
#===================================================================================================
def entry_from_csv_row(csv, local_account):
    local_account_csv = "iban:" + IBAN.generate("DE",
        bank_code = csv["localBankCode"],
        account_code = csv["localAccountNumber"]
    ).compact

    # Sanity check
    if local_account_csv != local_account:
        raise RuntimeError("Local account of transaction does not match user account")

    # Data from Sparkasse directly contains the IBAN in remoteAccountNumber, but I'm not sure if
    # this is also the case for other banks
    remote_account = ""
    if csv["remoteAccountNumber"]:
        try:
            remote_account = "iban:" + IBAN(csv["remoteAccountNumber"]).compact
        except ValueError:
            if csv["remoteBankCode"]:
                try:
                    # Because remoteCountry always seems to be empty I'm just using DE here even
                    # though this could (?) be wrong in some cases. However, it seems to be
                    # reasonbly safe for now because we only reach this case if remoteAccountNumber
                    # is not set, which in turn only seems to happen if the transaction was
                    # triggered by your own bank (at least this is what I observed with Sparkasse).
                    # So as long as we only use aqbanking to import transactions from German banks I
                    # hope we're okay.
                    # Also, python-fints seems to somehow know the IBAN in this case, and I would
                    # like the backends to create the same entries to make cross-validation easier.
                    remote_account = "iban:" + IBAN.generate("DE",
                        bank_code = csv["remoteBankCode"],
                        account_code = csv["remoteAccountNumber"]
                    ).compact

                except ValueError:
                    remote_account = "?:" + csv["remoteBankCode"] + ";" + csv["remoteAccountNumber"]
            else:
                remote_account = "?:" + ";" + csv["remoteAccountNumber"]
    elif csv["remoteBankCode"]:
        remote_account = "?:" + csv["remoteBankCode"] + ";"

    return {
        "local_account": local_account,
        "remote_account": remote_account,
        "remote_name": csv["remoteName"],
        "entry_date": csv["date"].replace("/", "-"),
        "valuta_date": csv["valutaDate"].replace("/", "-"),
        "value": to_fixedpoint(csv["value_value"]),
        "currency": csv["value_currency"],
        "purpose": extract_purpose(csv),
        "ultimate_debtor": csv["ultimateDebtor"],
        "ultimate_creditor": csv["ultimateCreditor"],
        "primanota": csv["primanota"],

        "transaction_key": csv["transactionKey"],
        "transaction_code": csv["transactionCode"],
        "transaction_text": csv["transactionText"],

        # SEPA
        "creditor_scheme_id": csv["creditorSchemeId"],
        "mandate_id": csv["mandateId"],
        "end_to_end_ref": csv["endToEndReference"],
    }


def to_fixedpoint(v):
    # `v` should be of the form "x/100"
    [dec, frac] = v.split("/")
    if frac != "100":
        raise RuntimeError("Expected fraction to be 100")

    return int(dec)


def extract_purpose(csv_row):
    purpose = csv_row["purpose"]
    for i in range(1, 8):
        purpose += "\n" + csv_row["purpose" + str(i)]

    return purpose.strip()


def parse_iban(account_number):
    [kind, code] = account_number.split(":")
    if kind != "iban":
        raise RuntimeError("Only IBAN accounts supported")

    return IBAN(code)
