rm ledger.pkl
uv run accountant init
uv run accountant add-user antoine
uv run accountant add-user renan
uv run accountant add-user baptiste
uv run accountant record-shared-expense 25 antoine
uv run accountant record-shared-expense 8 renan
uv run accountant record-shared-expense 47 baptiste
uv run accountant record-transfer 12 antoine baptiste