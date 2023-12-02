# Table: Accounts
#===================================================================================================
DB_ACCOUNTS_TABLE = """
create table if not exists accounts(
    account_number text not null,
    bank_code text not null,
    login_name text,
    backend_config text not null default "{}",
    preferred_backend text,
    initial_balance integer not null default 0,

    constraint UK_accounts__account_number unique(account_number)
)"""


# Table: Transactions
#===================================================================================================
DB_TRANSACTION_DATA_COLUMNS = [
    "local_account",
    "remote_account",
    "remote_name",
    "entry_date",
    "valuta_date",
    "value",
    "currency",
    "purpose",
    "ultimate_debtor",
    "ultimate_creditor",
    "primanota",
    "original_value",
    "original_currency",
    "exchange_rate",
    "transaction_key",
    "transaction_code",
    "transaction_text",
    "creditor_scheme_id",
    "mandate_id",
    "end_to_end_ref",
    "cc_entry_ref",
    "cc_billing_ref",
]

DB_TRANSACTIONS_TABLE = """
create table if not exists transactions(
    id integer,

    -- Data that comes from the bank
    local_account text not null,
    remote_account text not null,
    remote_name text not null,
    entry_date date not null,
    valuta_date date not null,
    value integer not null,
    currency text not null,
    purpose text not null,
    ultimate_debtor text not null,
    ultimate_creditor text not null,
    primanota text not null,

    original_value integer,
    original_currency text,
    exchange_rate text, -- TODO Should be fixed-point

    transaction_key text not null,
    transaction_code text not null,
    transaction_text text not null,

    -- SEPA Lastschrift
    creditor_scheme_id text not null,
    mandate_id text not null,
    end_to_end_ref text not null,

    -- Credit cards
    cc_entry_ref text, -- Buchungsreferenz (Sparkasse *.csv)
    cc_billing_ref text, -- Abrechnungskennzeichen (Sparkasse *.csv)

    -- For transfers between two known accounts A and B there will typically also be two
    -- transactions: one from A to B and one from B to A with a negated amount. We use matching_txn
    -- to keep track of these matching transactions.
    matching_txn integer,

    total_order integer not null,
    inserted_at datetime not null,
    inserted_by text not null,

    constraint PK_transactions__id primary key(id),
    constraint UK_transactions__total_order unique(local_account, total_order),
    constraint FK_transactions__matching_txn foreign key(matching_txn) references transactions(id),
    constraint FK_transactions__local_account foreign key(local_account) references accounts(account_number)
)"""


# Table: Intervals
#===================================================================================================
DB_INTERVALS_TABLE = """
-- Intervals describe time ranges for which the database contains all the transactions that have
-- been made (i.e., all the transactions that are part of the bank statements for that time range).
-- More precisely, for the interval [start_date + 1 day, end_date - 1 day], all transactions must be
-- present in the database, and in the correct order.
-- Special rules apply for transactions that occured on start_date and end_date. In particular, for
-- those days we don't expect the database to contain all transactions (though it may contain some).
-- However, those that do exist must be in the correct order relative to each other (where the
-- correct order is whatever order the bank uses).
-- For example, assume we have the interval [2023-09-02, 2023-09-15]. This means that for the time
-- from 2023-09-03 to 2023-09-15 (both inclusive) the database must contain all transactions that
-- occured in that time. Additionally, the database may contain some transactions that occured on
-- 2023-09-02 and 2023-09-15. Note that the information available for start_date and end_date is
-- incomplete. In the above example this means that if the database contains transactions A and B
-- that occured on 2023-09-02, then it's possible that we might later need to insert additional
-- transactions before A (but not after A).
-- If you want to communicate that all transactions have been imported for some specific day, simple
-- set start_date to a day before that day and end_date to a day after.
-- Note that start_date <= end_date is not allowed.
create table if not exists intervals(
    account_number text not null,
    start_date date not null,
    end_date date not null,

    constraint FK_intervals__account_number foreign key(account_number) references accounts(account_number)
)"""


# Table: Abstract transactions
#===================================================================================================
DB_ABSTRACT_TRANSACTIONS_TABLE = """
create table if not exists abstract_transactions (
    from_account text not null,
    to_account text not null,
    notes text not null default "",

    -- Always positive
    amount unsigned int not null,

    -- These dates may be null if they have not been processed yet by the corresponding account.
    -- Usually, only one of them may be null. This happens if a new transaction is fetched before
    -- it's been processed by the receiver one or two days later.
    -- One could imagine leaving them both null transactions that one knows will occur at some point
    -- in the future.
    from_entry_date date,
    to_entry_date date,

    -- The concrete transaction that this abstract transaction was derived from, or null if it is a
    -- purely abstract transaction
    origin_tx_id int,

    inserted_at datetime not null,
    inserted_by text not null,

    constraint FK_abstract_transactions__origin_tx_id foreign key(origin_tx_id) references transactions(id)
)"""
