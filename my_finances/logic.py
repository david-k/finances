import sys
import os
import sqlite3
import datetime
import pathlib
import shutil
import json
from pprint import pprint
from decimal import Decimal

from . import db


# GLOBALS
#===================================================================================================
LENIENT_VALIDATION_FIELDS = [
    "local_account",
    "remote_account",
    "remote_name",
    "entry_date",
    "valuta_date",
    "value",
    "currency",
    "purpose",
]


# Validating new transactions
#===================================================================================================
# If the new transactions valid for the interval [new_start_date, new_end_date), returns a list of
# ranges into new_transactions denoting the which transactions should be inserted (skipping over any
# transactions that already exist in the database).
# Otherwise, an exception is raised.
def validate_new_transactions(
    cursor, account,
    new_transactions, new_start_date, new_end_date,
    lenient = False
):
    # Some basic sanity checks
    prev_date = new_start_date
    for t in new_transactions:
        if t["local_account"] != account["account_number"]:
            raise RuntimeError("Local account of new transaction is wrong")

        if t["entry_date"] < prev_date:
            raise RuntimeError("Date of new transaction too small")
        if t["entry_date"] > new_end_date:
            raise RuntimeError("Date of new transaction too large")

        prev_date = t["entry_date"]


    # Check that new_transactions does not contradict existing information. For this we need to
    # ensure that the new transactions match the existing transactions for each known interval.
    intervals = cursor.execute(
        """select start_date, end_date from intervals
        where
            -- Select intervals that intersect with the start date and end date of the new transactions
            start_date <= :new_end_date and end_date >= :new_start_date
            and account_number = :account
        order by start_date""",
        {"new_start_date": new_start_date, "new_end_date": new_end_date, "account": account["account_number"]}
    ).fetchall()
    new_idx = 0 # Index into new_transactions
    new_trans_ranges = []
    for i in intervals:
        start_date = max(i["start_date"], new_start_date)
        end_date = min(i["end_date"], new_end_date)
        # Get all existing transactions for this interval
        existing_transactions = cursor.execute(
            """select * from transactions
            where
                entry_date >= :start_date and entry_date <= :end_date and
                local_account = :account
            order by total_order""",
            {"start_date": start_date, "end_date": end_date, "account": account["account_number"]}
        ).fetchall()

        # Get the index of the first transaction with the same date as start_date (or larger)
        known_start_idx = first_idx_with_date_at_least(new_transactions, new_idx, start_date)
        # If no such transaction exists, then existing_transactions must also be empty (because we
        # are in a known interval, both new and existing transactions must match)
        if known_start_idx == None:
            if len(existing_transactions) == 0:
                continue
            else:
                raise RuntimeError(f"Missing new transactions in interval {i['start_date']} -- {i['end_date']}")

        # If there exist new transactions before start_date then they are outside any known
        # interval. Hence, we need to remember to add them to the database.
        if known_start_idx > new_idx:
            new_trans_ranges.append(range(new_idx, known_start_idx))

        new_idx = known_start_idx

        # Ensure that the new transactions conincide with the existing transactions in the interval
        # TODO The ways this is currently implemented requires that transaction that occured on the
        #      same day are sorted the same way in both existing_transactions and new_transactions.
        #      This seems unnecessarily restrictive.
        for existing_trans in existing_transactions:
            if new_idx == len(new_transactions):
                # If new_transactions prematurely ends on the last day of the provided interval
                # [new_start_date, new_end_date) then that's fine since the last day is allowed to
                # be incomplete (the last day is basically best-effort). However, in all other cases
                # this is an error.
                if existing_trans["entry_date"] == new_end_date:
                    break
                else:
                    raise RuntimeError(f"Missing new transactions in interval {i['start_date']} -- {i['end_date']}")

            new_trans = new_transactions[new_idx]
            if not compare_rows(existing_trans, new_trans, lenient):
                print_diff(existing_trans, new_trans)
                raise RuntimeError("Retrieved transactions are inconsistent with existing transactions")
            new_idx += 1


    if new_idx < len(new_transactions):
        new_trans_ranges.append(range(new_idx, len(new_transactions)))

    return new_trans_ranges


def compare_rows(db_row, csv_row, lenient = False):
    fields = LENIENT_VALIDATION_FIELDS if lenient else db.DB_TRANSACTION_DATA_COLUMNS

    for key in fields:
        db_val = db_row[key]
        csv_val = csv_row.get(key)
        if not csv_val and db_val:
            return False

        if key == "purpose":
            db_val = db_val.replace("\n", "").replace(" ", "")
            csv_val = csv_val.replace("\n", "").replace(" ", "")

            if lenient:
                if db_val and csv_val:
                    if db_val.find(csv_val) == -1 and csv_val.find(db_val) == -1:
                        return False
                elif db_val != csv_val:
                    return False
            elif db_val != csv_val:
                return False

        elif db_val != csv_val:
            return False

    return True


def print_diff(db_row, csv_row):
    print("\n=== EXISTING ===")
    for key in csv_row.keys():
        if csv_row[key] != db_row[key]:
            print("!!! ", end="")
        print(f'{key} = "{db_row[key]}"')

    print("\n=== NEW ===")
    for key in csv_row.keys():
        if csv_row[key] != db_row[key]:
            print("!!! ", end="")
        print(f'{key} = "{csv_row[key]}"')

    print()


def first_idx_with_date_at_least(transactions, start_idx, date):
    for i in range(start_idx, len(transactions)):
        if transactions[i]["entry_date"] >= date:
            return i

    return None


def max_safe(a, b):
    if a == None:
        return b
    if b == None:
        return a

    return max(a, b)


def min_safe(a, b):
    if a == None:
        return b
    if b == None:
        return a

    return min(a, b)


# Inserting new transactions into the database
#===================================================================================================
# Note that `new_transactions` is modified
def insert_transactions(
    cursor, account,
    new_transactions, new_start_date, new_end_date,
    fetched_by, fetched,
    lenient = False
):
    idx_ranges = validate_new_transactions(cursor, account, new_transactions, new_start_date, new_end_date, lenient)

    min_start_date = cursor.execute(
        "select min(start_date) from intervals where account_number = ?",
        (account["account_number"],)
    ).fetchone()
    if min_start_date:
        min_start_date = min_start_date["min(start_date)"]

    # Get the current value for total_order
    # TODO This is wrong for all cases where we not only add transactions at the end!
    total_order_start = cursor.execute(
        "select max(total_order) as mto from transactions where local_account = :account",
        {"account": account["account_number"]}
    ).fetchone()
    total_order_start = 0 if total_order_start["mto"] == None else total_order_start["mto"] + 1

    # Insert new transactions into the database
    initial_balance_delta = 0
    counter = 0
    for idx_range in idx_ranges:
        for i in idx_range:
            entry = new_transactions[i]
            entry["total_order"] = total_order_start
            entry["inserted_by"] = fetched_by
            entry["inserted_at"] = fetched
            total_order_start += 1

            columns = entry.keys()
            placeholders = [":" + c for c in columns]
            cursor.execute(
                "insert into transactions({}) values({})".format(
                    ', '.join(columns),
                    ', '.join(placeholders)
                ),
                entry
            )
            counter += 1

            if entry["entry_date"] < min_start_date:
                initial_balance_delta += int(entry["value"])


    match_transactions(cursor)
    update_known_intervals(cursor, account, new_start_date, new_end_date)

    if initial_balance_delta != 0:
        cursor.execute(
            """update accounts set initial_balance = initial_balance - :delta
            where account_number = :account""",
            {"account": account["account_number"], "delta": initial_balance_delta}
        )

    return counter


def update_known_intervals(cursor, account, new_start_date, new_end_date):
    res = cursor.execute(
        """select
            min(start_date) as min_start,
            max(end_date) as max_end
        from intervals
        where account_number = :account and
            -- Select intervals that intersect with the start date and end date of the new transactions
            start_date <= :new_end_date and end_date >= :new_start_date""",
        {"account": account["account_number"], "new_start_date": new_start_date, "new_end_date": new_end_date}
    ).fetchone()

    min_start = min_safe(res["min_start"], new_start_date)
    max_end = max_safe(res["max_end"], new_end_date)

    # Delete all intervals that we selected above and create a new, combined interval that contains
    # them all and also [new_start_date, new_end_date]
    cursor.execute(
        """delete from intervals
        where account_number = :account and
            -- Select intervals that intersect with the start date and end date of the new transactions
            start_date <= :new_end_date and end_date >= :new_start_date""",
        {"account": account["account_number"], "new_start_date": new_start_date, "new_end_date": new_end_date}
    )
    cursor.execute(
        "insert into intervals(account_number, start_date, end_date) values(?, ?, ?)",
        (account["account_number"], min_start, max_end)
    )


def match_transactions(cursor):
    # Find all transactions that can have a counterpoart but for which we haven't found it yet.
    unmatched = cursor.execute(
        """select * from transactions
        where
            matching_txn is null and
            local_account in (select account_number from accounts) and
            remote_account in (select account_number from accounts)"""
    ).fetchall()

    for tx in unmatched:
        match = find_matching_transaction(cursor, tx)
        if not match:
            # TODO Emit warning if...
            continue

        cursor.execute(
            "update transactions set matching_txn = :match_id where id = :id",
            {"id": tx["id"], "match_id": match["id"]}
        )
        cursor.execute(
            "update transactions set matching_txn = :match_id where id = :id",
            {"id": match["id"], "match_id": tx["id"]}
        )


def find_matching_transaction(cursor, tx):
    time_delta = datetime.timedelta(days=20) # Is that enough?
    entry_date = datetime.date.fromisoformat(tx["entry_date"])
    matches = cursor.execute(
        """select * from transactions
        where
            local_account = :local and remote_account = :remote and
            value = :value and matching_txn is null and
            :lower_bound <= entry_date and entry_date <= :upper_bound""",
            {
                "local": tx["remote_account"],
                "remote": tx["local_account"],
                "value": -int(tx["value"]),
                "lower_bound": entry_date - time_delta,
                "upper_bound": entry_date + time_delta,
            }
    ).fetchall()

    if not matches:
        return None

    best_match = matches[0]
    for idx in range(1, len(matches)):
        match = matches[idx]
        if entry_date_diff(match, tx) < entry_date_diff(best_match, tx):
            best_match = match

    return best_match


def entry_date_diff(tx1, tx2):
    entry_date1 = datetime.date.fromisoformat(tx1["entry_date"])
    entry_date2 = datetime.date.fromisoformat(tx2["entry_date"])
    return abs((entry_date1 - entry_date2).days)


# Checking database for consistency
#===================================================================================================
class InconsistentTransactionsError(RuntimeError):
    def __init__(self, msg, inconsistent_transactions):
        super().__init__(msg)
        self.inconsistent_transactions = inconsistent_transactions

class InconsistentIntervalsError(RuntimeError):
    def __init__(self, msg, inconsistent_intervals):
        super().__init__(msg)
        self.inconsistent_intervals = inconsistent_intervals


def check_consistency(cursor):
    check_transaction_consistency(cursor)
    check_interval_consistency(cursor)


def check_transaction_consistency(cursor):
    # All transactions must be part of an interval
    outside_txs = cursor.execute(
        """select * from transactions tx
        where not exists (
            select * from intervals i
            where i.account_number = tx.local_account and i.start_date <= tx.entry_date and tx.entry_date <= i.end_date
        )"""
    ).fetchall()
    if outside_txs:
        raise InconsistentTransactionsError(
            "The following transactions are outside any known interval",
            [dict(tx) for tx in outside_txs]
        )


    # A transaction's entry_date must be consistent with its total_order
    invalid_total_order_txs = cursor.execute(
        """select * from transactions s
        where exists (
            select * from transactions t
            where t.local_account = s.local_account and t.total_order < s.total_order and t.entry_date > s.entry_date
        )"""
    ).fetchall()
    if invalid_total_order_txs:
        raise InconsistentTransactionsError(
            "The following transactions have an invalid total order",
            [dict(tx) for tx in invalid_total_order_txs]
        )


    # TODO Check that all transactions that can be matched *have* been matched


def check_interval_consistency(cursor):
    # Check that start_date <  end_date
    result = cursor.execute("select * from intervals where start_date >= end_date").fetchall()
    if result:
        raise InconsistentIntervalsError(
            "The following intervals have a start_date >= end_date",
            [dict(i) for i in result]
        )


    # Check that intervals do not intersect
    result = cursor.execute(
        """select * from intervals a
        where exists (
            select * from intervals b
            where
                b.account_number = a.account_number and b.rowid != a.rowid and
                -- a.end_date == b.start_date is not allowed because then a transaction could belong
                -- to two intervals
                b.start_date <= a.end_date and b.end_date >= a.start_date
        )"""
    ).fetchall()
    if result:
        raise InconsistentIntervalsError(
            "The following intervals intersect with another interval",
            [dict(i) for i in result]
        )


    # Check that two intervals don't share the same start_date or end_date.
    # This is not strictly needed for consistency but ensures that we don't have redundant intervals.
    # (This scenario is only possible if one of the intervals has the same start and end date.)
    result = cursor.execute(
        """select * from intervals a
        where exists (
            select * from intervals b
            where
                b.account_number = a.account_number and b.rowid != a.rowid and
                (b.start_date = a.start_date or b.end_date = a.end_date)
        )"""
    ).fetchall()
    if result:
        raise InconsistentIntervalsError(
            "The following intervals are redundant",
            [dict(i) for i in result]
        )
