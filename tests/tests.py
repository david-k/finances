import sqlite3
import unittest
from pprint import pprint

from my_finances import db, logic


class Test(unittest.TestCase):
    # Initialization and shutdown
    #---------------------------------------------------------------------------
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

        self.conn.execute(db.DB_TRANSACTIONS_TABLE)
        self.conn.execute(db.DB_ACCOUNTS_TABLE)
        self.conn.execute(db.DB_INTERVALS_TABLE)


    def tearDown(self):
        self.conn.close()


    # Tests: Transaction consistency
    #---------------------------------------------------------------------------
    def test_transactions_belong_to_interval(self):
        # TODO
        pass


    def test_transactions_have_consistent_total_order(self):
        # TODO
        pass


    # Tests: Interval consistency
    #---------------------------------------------------------------------------
    def test_single_interval_consisteny(self):
        logic.check_consistency(self.conn)

        self.insert_account("A")

        self.insert_interval("A", "2023-09-12", "2023-09-23")
        logic.check_consistency(self.conn)

        self.insert_interval("A", "2023-09-24", "2023-09-25")
        logic.check_consistency(self.conn)

        self.conn.commit()

        self.assert_invalid_interval("A", "2023-10-12", "2023-10-11")
        self.assert_invalid_interval("A", "2023-11-12", "2023-11-12")
        self.assert_invalid_interval("A", "2023-08-12", "2023-07-23")


    def test_cross_interval_consistency(self):
        logic.check_consistency(self.conn)

        self.insert_account("A")
        self.insert_account("B")
        self.insert_interval("A", "2023-09-12", "2023-09-23")
        logic.check_consistency(self.conn)

        self.insert_interval("B", "2023-09-20", "2023-09-25")
        logic.check_consistency(self.conn)

        self.insert_interval("A", "2023-09-24", "2023-09-25")
        logic.check_consistency(self.conn)

        self.insert_interval("A", "2023-09-06", "2023-09-11")
        logic.check_consistency(self.conn)

        self.conn.commit()

        self.assert_invalid_interval("A", "2023-09-20", "2023-09-25")
        self.assert_invalid_interval("A", "2023-09-03", "2023-09-06")
        self.assert_invalid_interval("A", "2023-09-25", "2023-09-27")



    # Utils
    #---------------------------------------------------------------------------
    def assert_invalid_interval(self, acc, start_date, end_date):
        self.insert_interval(acc, start_date, end_date)
        with self.assertRaises(logic.InconsistentIntervalsError):
            logic.check_consistency(self.conn)
        self.conn.rollback()


    def insert_account(self, acc):
        self.conn.execute(
            "insert into accounts(account_number, bank_code) values(?, ?)",
            (acc, "12345678")
        )


    def insert_interval(self, acc, start_date, end_date):
        self.conn.execute(
            "insert into intervals(account_number, start_date, end_date) values(?, ?, ?)",
            (acc, start_date, end_date)
        )
