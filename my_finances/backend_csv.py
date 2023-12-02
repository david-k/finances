import csv
from datetime import datetime
from pprint import pprint
from decimal import Decimal
import shutil

from schwifty import IBAN


#===================================================================================================
def csv_fetch_transactions(account, from_date, to_date, temp_dir, config, options):
    transactions = []

    # TODO Must make sure that there are no pending transactions in the CSV, or that these
    # transactions can be identified somehow
    #
    # Some banks (e.g. Fyrst) add a UTF-8 BOM at the beginning of the file. Using utf-8-sig ensures
    # that the BOM is not treated as text.
    with open(options["csv_filename"], newline='', encoding="utf-8-sig") as csvfile:
        if config["has_header"]:
            csv_reader = csv.DictReader(csvfile, delimiter=config["delimiter"])
        else:
            csv_reader = csv.reader(csvfile, delimiter=config["delimiter"])

        for t in csv_reader:
            entry = entry_from_csv_row(t, account["account_number"], config)
            if (from_date and entry["entry_date"] < from_date) or (to_date and entry["entry_date"] > to_date):
                print("Warning: Ignoring entry that is outside the specified date range.")
                pprint(entry)
            else:
                transactions.append(entry)

    shutil.copy2(options["csv_filename"], temp_dir)

    # If the transactions are not sorted by entry_date in ascending order, reverse the list.
    # Why not simply do a sort? Because we (currently) need to preserve the order of transactions
    # that occurred on the same day. This is because when validating new transactions against the
    # already existing transactions, we simple compare them in order, and if they don't match, we
    # throw an error. (I should improve the validation procedure so that it does not have this
    # resitriction.)
    if not is_ascending(transactions):
        transactions.reverse()

    return transactions


# Utils
#===================================================================================================
def entry_from_csv_row(csv, local_account, config):
    fields = config["fields"]

    entry = {
        "local_account": local_account,
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
    for column, info in fields.items():
        csv_value = csv[info["column"]]
        if column == "remote_account":
            try:
                entry["remote_account"] = "iban:" + IBAN(csv_value).compact
            except ValueError:
                entry["remote_account"] = "?:" + ";" + csv_value
        elif column == "value":
            if config["thousands_separator"]:
                csv_value = csv_value.replace(config["thousands_separator"], "")
            if config["decimal_separator"]:
                csv_value = csv_value.replace(config["decimal_separator"], ".")
            entry[column] = int(str(Decimal(csv_value)*100).split(".")[0])
        elif column in ["entry_date", "valuta_date"]:
            if "format" in info:
                entry[column] = str(datetime.strptime(csv_value, info["format"]).date())
            else:
                entry[column] = str(datetime.date.fromisoformat(csv_value))
        else:
            entry[column] = csv_value

    return entry


def is_ascending(ts):
    if not ts:
        return True

    prev_date = ts[0]["entry_date"]
    for i in range(1, len(ts)):
        t = ts[i]
        if prev_date < t["entry_date"]:
            return True
        if prev_date > t["entry_date"]:
            return False

    return True
