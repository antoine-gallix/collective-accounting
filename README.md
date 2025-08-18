# collective-accounting

CLI tool for group accounting. Maintain a ledger that tracks balances between accounts. This is intended to be used in a collective where members advance money to buy things for the group. The ledger keeps track of who owes and who is owed money so counts can be setteled later.

## Installation

## Concepts

### Accounts

Members of the collective are represented by *accounts*. An account represents the amount that the person owes or is owned by the group in general. A positive balance means the member is owed money by the group; a negative that they owe money. The sum of account balances is always zero. When all accounts are zero, the accounts are settled.

### Operations

The ledger is modified by operations. An operation bring changes on multiple accounts at once, and the sum of changes brought by each operation is also zero.

### Recording an expense

When a person pays an amount of money X for a group of size N, their account balance is increased by X and every account including the one who paid is decreased by X/N.

For the payer, the change to their account is `+X(N-1)/N`. For the other, the change is `-X/N`

### Settling the debts

To settle the debts, users with a negative account transfer money to the ones with a positive account. A negative account is called a debitor; a positive account is a creditor. When a debitor sends an amount of money X to a creditor, the debitor account is changed by `+X`, and the creditor `-X`. By such operations, the balances can be all brought to zero, settling the accounts and bringing back the peace in the community.

## Usage

### Visualize
