# Bundled benchmark rates

Published benchmark rates used by the engine, the Python reference and the spreadsheet (A-05, B-03, B-07). Every figure is copied from the publisher's own website without rounding or gap-filling. Each folder holds the source CSV files and a `sources.json` with the source page, retrieval date and caveats.

| Folder | Contents | Used for |
|---|---|---|
| `mclr/` | SBI and Bank of Baroda MCLR history from April 2016 | A reference shown beside an MCLR-linked loan. MCLR resets are not modelled; the customer enters each past rate (B-07). |
| `repo/` | Every RBI policy repo rate change since the rate in force on 1 Oct 2019, each with its RBI release | Repo-linked loans (B-03). How a repo change reaches the loan's rate is pending (B-09). |

HDFC Bank, ICICI Bank and Axis Bank publish no official MCLR history, so none is bundled for them.

After editing a CSV or `sources.json`, run `python3 -I data/benchmarks/build.py` to rebuild `benchmarks.json`. CI runs it with `--check`. To update a table, add the new rows from the publisher's page, update `covers`, `retrieved` and `table_version`, and rebuild.
