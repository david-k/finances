import sys
import os
import tempfile
import sqlite3
import datetime
import shutil
import ntplib
from zoneinfo import ZoneInfo
import json
from pprint import pprint

from . import logic
from .backend_aqbanking import aqbanking_fetch_transactions
from .backend_fints import fints_fetch_transactions
from .backend_csv import csv_fetch_transactions


# Globals
#===================================================================================================
OVERLAP_DAYS = 4

BACKENDS = [
    "aqbanking",
    "fints",
    "csv",
]


# Utils
#===================================================================================================
def fatal(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
    sys.exit(1)


def get_date_via_ntp():
    c = ntplib.NTPClient()

    # Alternative: response = c.request('ntp.hetzner.de', version=3)
    response = c.request('europe.pool.ntp.org', version=3)

    # Create a `datetime` object instead of a `date` object because the latter does not accept a
    # timezone argument. Isn't the timezone required to reconstruct the correct date from
    # `response.tx_time`, which is UTC?
    # This assumes that all the banks we are interested in use the same timezone as Europe/Berlin.
    d = datetime.datetime.fromtimestamp(response.tx_time, ZoneInfo("Europe/Berlin"))

    return str(d.date())


def backend_for_account(account, options):
    if account["preferred_backend"]:
        return account["preferred_backend"]

    return options["backend"]


def backend_fetch_transactions(cursor, account, from_date, to_date, temp_dir, options):
    backend = backend_for_account(account, options)
    backend_config = account["backend_config"]

    if backend not in backend_config:
        backend_config[backend] = {}

    if backend == "aqbanking":
        transactions = aqbanking_fetch_transactions(account, from_date, to_date, temp_dir, backend_config[backend], options)
    elif backend == "fints":
        transactions = fints_fetch_transactions(account, from_date, to_date, temp_dir, backend_config[backend], options)
    elif backend == "csv":
        transactions = csv_fetch_transactions(account, from_date, to_date, temp_dir, backend_config[backend], options)

    cursor.execute(
        "update accounts set backend_config = :config where account_number = :account",
        {"account": account["account_number"], "config": json.dumps(backend_config)}
    ).fetchall()

    return transactions, backend


def validate_import_start_date(cursor, account, start_date):
    intervals = cursor.execute(
        """select end_date from intervals
        where
            account_number = :account and
            start_date <= :date and :date <= end_date""",
        {"account": account["account_number"], "date": start_date}
    ).fetchall()

    start_date_obj = datetime.date.fromisoformat(start_date)
    for i in intervals:
        delta = datetime.date.fromisoformat(i["end_date"]) - start_date_obj
        if delta.days < OVERLAP_DAYS:
            raise RuntimeError("start date does not satisfy overlap window")


def validate_import_end_date(cursor, account, end_date):
    intervals = cursor.execute(
        """select start_date from intervals
        where
            account_number = :account and
            start_date <= :date and :date <= end_date""",
        {"account": account["account_number"], "date": end_date}
    ).fetchall()

    end_date_obj = datetime.date.fromisoformat(end_date)
    for i in intervals:
        delta = end_date_obj - datetime.date.fromisoformat(i["start_date"])
        if delta.days < OVERLAP_DAYS:
            raise RuntimeError("end date does not satisfy overlap window")


# Commands
#===================================================================================================
def import_transactions(conn, account, options):
    cursor = conn.cursor()
    check_consistency(cursor)

    if options["derive_dates"]:
        fetch_start_date = None
        fetch_end_date = None
    else:
        fetch_start_date = options["start_date"]
        if fetch_start_date:
            validate_import_start_date(cursor, account, fetch_start_date)
        else:
            fetch_start_date = cursor.execute(
                "select max(end_date) as max_date from intervals where account_number = :account",
                {"account": account["account_number"]}
            ).fetchone()["max_date"]

            # Fetch transactions starting from OVERLAP_DAYS days before the most recent known transaction.
            # Why not just use most_recent_date directly?
            # - Beacuse I've read that sometimes, transactions may be inserted
            #   after the fact, and I want to detect that.
            # - Also, this ensures that we can detect when a bank refuses to
            #   return transactions that are too old. For example:
            #   - Postbank does not return transactions older than 3 months, but also does not throw
            #     and error if you try to do that. So if you requests transactions for the last 4
            #     months, Postbank will silently skip any transactions that are too old.
            #   - Since we require the list of new transactions to overlap with the existing
            #     transactions, we can detect this case.
            #   - The only thing we can do in this case is to create two disjoint `intervals` with a
            #     whole inbetween. TODO I'm not doing this yet
            if fetch_start_date != None:
                fetch_start_date = str(datetime.date.fromisoformat(fetch_start_date) - datetime.timedelta(days=OVERLAP_DAYS))

        fetch_end_date = str(datetime.date.today())
        server_date = get_date_via_ntp()
        if fetch_end_date != server_date:
            # This shouldn't be a hard error. Let the user decide whether they want to continue.
            raise RuntimeError(f"Local date {fetch_end_date} does not match date from server {server_date}")


    print("== Account " + account["account_number"])
    if fetch_start_date and fetch_end_date:
        print(f"Importing transactions between {fetch_start_date} and {fetch_end_date}") 
    elif fetch_end_date:
        # Actually, the message below does not seem to be entirely accurate. For example, if no date
        # is given, then Sparkasse only returns credit card transactions for the current month, even
        # though you can get transactions up to one year in the past when explicitly provinding a
        # date.
        print(f"Importing all available transactions until {fetch_end_date}")


    with tempfile.TemporaryDirectory() as temp_dir:
        transactions, backend = backend_fetch_transactions(cursor, account, fetch_start_date, fetch_end_date, temp_dir, options)

        # In order to insert the transactions we need a concrete start date. If fetch_start_date is
        # None, then the start date depends on how the bank handles the case when no start date is
        # provided (e.g., Sparkasse will return all transactions from the last two years, while
        # Postbank only considers the last three months).
        # As a conversative approximation we try to use the date of the first transaction.
        if fetch_start_date == None and len(transactions):
            fetch_start_date = transactions[0]["entry_date"]
            validate_import_start_date(cursor, account, fetch_start_date)

        if fetch_end_date == None and len(transactions):
            fetch_end_date = transactions[-1]["entry_date"]
            validate_import_end_date(cursor, account, fetch_end_date)

        # TODO If fetch_start_date != None and there do not exist any transactions in the DB then we
        #      have no way of knowing if the list of transactions returned from the bank has been
        #      truncated (see comment above on why we use OVERLAP_DAYS). In this case, the only safe
        #      thing seems to be to set fetch_start_date = transactions[0]["entry_date"]

        # If fetch_start_date is still None it means that there are no transactions in the database
        # and no new transactions have been fetched. Since we don't have a start date in this case
        # we simply to nothing.
        if fetch_start_date != None:
            fetched = datetime.datetime.utcnow().isoformat(" ")
            num_new_trans = insert_transactions(
                cursor, account, transactions, fetch_start_date, fetch_end_date, backend, fetched,
                options["lenient_validation"]
            )
            print(f"Fetched {num_new_trans} new transactions")

            # In we have inserted at least one transaction, copy the raw transaction data to
            # options["raw_import_dir"]
            if num_new_trans > 0:
                with open(os.path.join(temp_dir, "info.ini"), "w") as info_file:
                    info_file.write(f"imported = {fetched}\n")
                    info_file.write(f"backend = {backend}\n")
                    info_file.write(f"start_date = {fetch_start_date}\n")
                    info_file.write(f"end_date = {fetch_end_date}\n") # End date is assumed to be incomplete

                dest_dir = os.path.join(options["raw_import_dir"],
                                        account["account_number"] + "__" + fetched)
                shutil.copytree(temp_dir, dest_dir)

    check_consistency(cursor)
    cursor.close()
    conn.commit()


def validate_transactions(conn, account, options):
    cursor = conn.cursor()
    check_consistency(cursor)

    fetch_start_date = options["start_date"]
    fetch_end_date = options["end_date"]
    with tempfile.TemporaryDirectory() as temp_dir:
        transactions, _ = backend_fetch_transactions(cursor, account, fetch_start_date, fetch_end_date, temp_dir, options)

    if not fetch_start_date and transactions:
        fetch_start_date = transactions[0]["entry_date"]
    if not fetch_end_date and transactions:
        fetch_end_date = transactions[-1]["entry_date"]

    if fetch_start_date:
        print(f"Validating transactions from {fetch_start_date} to {fetch_end_date} using backend {options['backend']}")
        validate_new_transactions(cursor, account, transactions, fetch_start_date, fetch_end_date, options["lenient_validation"])
    else:
        print("Error: Could not determine start date and/or end date")

    cursor.close()
    conn.commit()


def fetch_transactions(conn, account, options):
    cursor = conn.cursor()
    check_consistency(cursor)

    fetch_start_date = options.get("start_date")
    fetch_end_date = options["end_date"]

    with tempfile.TemporaryDirectory() as temp_dir:
        transactions, _ = backend_fetch_transactions(
            cursor, account, options.get("start_date"), options.get("end_date"), temp_dir, options
        )

    pprint(transactions)

    cursor.close()
    conn.commit()


def process_transactions(conn, account, options):
    cursor = conn.cursor()
    check_consistency(cursor)
    match_transactions(cursor)
    cursor.close()
    conn.commit()


# Parsing command-line arguments
#===================================================================================================
def parse_arguments():
    if len(sys.argv) < 2:
        fatal("You need to provide a command")

    command = sys.argv[1]
    if command == "import":
        return parse_import_arguments()
    elif command == "validate":
        return parse_validate_fetch_arguments("validate")
    elif command == "fetch":
        return parse_validate_fetch_arguments("fetch")
    elif command == "process":
        return parse_process_arguments()
    else:
        fatal("Invalid command: " + command)


def parse_import_arguments():
    options = {
        "command": "import",
        "db_file": None,
        "backend": "aqbanking",
        "accounts": set(), # Empty means all accounts
        "start_date": None,
        "csv_filename": None,
        # Whether to derive start_date and end_date from the retrieved transactions. By default,
        # start_date is 4 days before the last import date, and end_date is today.
        "derive_dates": False,
        "lenient_validation": False,
        # Where to store the raw transaction data that is fetched from the bank. The directory is relative
        # to the directory this script is executed in.
        # It's useful to keep this data around because we don't import all the transaction fields
        # into the database (not sure what all of them mean and not all of them seem required for my
        # needs). If I later decide I need these additional fields, then the original data still
        # available.
        "raw_import_dir": "./raw_import_data",
    }

    idx = 2
    while idx < len(sys.argv):
        arg = sys.argv[idx]
        idx += 1
        if arg == "--backend":
            backend = sys.argv[idx]
            if backend not in BACKENDS:
                fatal("Invalid backend: " + backend)
            options["backend"] = backend
            idx += 1
        elif arg == "--account":
            options["accounts"].add(sys.argv[idx])
            idx += 1
        elif arg == "--start-date":
            options["start_date"] = str(datetime.date.fromisoformat(sys.argv[idx]))
            idx += 1
        elif arg == "--derive-dates":
            options["derive_dates"] = True
        elif arg == "--csv":
            options["csv_filename"] = sys.argv[idx]
            options["backend"] = "csv"
            options["derive_dates"] = True
            idx += 1
        elif arg == "--lenient-validation":
            options["lenient_validation"] = True
        else:
            if options["db_file"] != None:
                raise RuntimeError("Error: invalid option: " + arg)
            options["db_file"] = arg

    if options["db_file"] == None:
        fatal("Error: db_file is not set")

    return options


def parse_validate_fetch_arguments(command):
    options = {
        "command": command,
        "db_file": None,
        "backend": "aqbanking",
        "accounts": set(), # Empty means all accounts
        "start_date": None,
        "end_date": None,
        "csv_filename": None,
        "lenient_validation": False,
    }

    idx = 2
    while idx < len(sys.argv):
        arg = sys.argv[idx]
        idx += 1
        if arg == "--backend":
            backend = sys.argv[idx]
            if backend not in BACKENDS:
                fatal("Invalid backend: " + backend)
            options["backend"] = backend
            idx += 1
        elif arg == "--account":
            options["accounts"].add(sys.argv[idx])
            idx += 1
        elif arg == "--start-date":
            options["start_date"] = str(datetime.date.fromisoformat(sys.argv[idx]))
            idx += 1
        elif arg == "--end-date":
            options["end_date"] = str(datetime.date.fromisoformat(sys.argv[idx]))
            idx += 1
        elif arg == "--csv":
            options["csv_filename"] = sys.argv[idx]
            options["backend"] = "csv"
            idx += 1
        elif arg == "--lenient-validation":
            options["lenient_validation"] = True
        else:
            if options["db_file"] != None:
                raise RuntimeError("Error: invalid option: " + arg)
            options["db_file"] = arg

    if options["db_file"] == None:
        fatal("Error: db_file is not set")

    return options


def parse_process_arguments():
    options = {
        "command": "process",
        "db_file": None,
    }

    idx = 2
    while idx < len(sys.argv):
        arg = sys.argv[idx]
        idx += 1
        if options["db_file"] != None:
            raise RuntimeError("Error: invalid option: " + arg)
        options["db_file"] = arg

    if options["db_file"] == None:
        fatal("Error: db_file is not set")

    return options


# MAIN
#===================================================================================================
options = parse_arguments()

conn = sqlite3.connect(options["db_file"])
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA foreign_keys = ON")

cursor = conn.cursor()
cursor.execute(db.DB_TAGS_TABLE)
cursor.execute(db.DB_TRANSACTIONS_TABLE)
cursor.execute(db.DB_ACCOUNTS_TABLE)
cursor.execute(db.DB_INTERVALS_TABLE)


accounts_res = cursor.execute(
    "select * from accounts where login_name is not null"
).fetchall()
def process_account_row(row):
    acc = dict(row)
    acc["backend_config"] = json.loads(acc["backend_config"])
    return acc
accounts = [process_account_row(acc) for acc in accounts_res]


for acc in accounts:
    if options.get("accounts") and not acc["account_number"] in options["accounts"]:
        continue

    if options["command"] == "import":
        import_transactions(conn, acc, options)
    elif options["command"] == "validate":
        validate_transactions(conn, acc, options)
    elif options["command"] == "fetch":
        fetch_transactions(conn, acc, options)
    elif options["command"] == "process":
        process_transactions(conn, acc, options)
