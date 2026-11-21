# Insider Intelligence Engine — research prototype

## Scope
Offline screening and **exploratory** event-study backtesting of normalized SEC Form 4 purchases. Does not place trades. No historical results are claimed until real data are supplied.

## Setup
`pip install pandas numpy`

## Run
`python engine.py --transactions transactions.csv --prices prices.csv --output results`
`python -m unittest test_engine.py -v`

## Input contracts
`transactions.csv`: ticker,accession,insider_id,insider_name,role,filing_timestamp,transaction_date,code,acquired_disposed,shares,price,shares_after,direct_indirect,is_derivative,is_10b5_1

`prices.csv`: ticker,date,open,high,low,close,volume

All times in filing_timestamp should be UTC ISO-8601; dates in YYYY-MM-DD. Prices must be consistent, corporate-action-adjusted OHLC data; split-adjusted prices alone do not represent total returns. Historical ticker-to-CIK mapping must be point-in-time. Treat unknown 10b5-1 flags as unknown rather than false.

## Data ingestion roadmap
1. Download SEC quarterly insider transaction ZIP files, 2023Q1–2026Q3, plus 2026Q4-to-date via EDGAR. SEC dataset: https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets
2. Join SUBMISSION, REPORTINGOWNER, and NONDERIV_TRANS by accession; preserve filing acceptance timestamps from original EDGAR records; map SEC transaction code P, acquisition A, and direct ownership D; verify footnotes and 10b5-1 status in the original filing.
3. Build a survivorship-bias-free historical security master with delisted symbols, share-class changes, corporate actions, and point-in-time market caps.
4. Obtain adjusted OHLCV including delisted securities, and market/sector benchmark data. Respect vendor licensing.
5. Normalize to input CSVs and run. No historical performance can be reported until this is done.

## Critical limitations of this prototype
- The current engine does **not** download/parse SEC quarterly ZIP files or provide automated scheduled monitoring.
- It does not implement 4H/1H/5M BOS/CHOCH, independent technical-only strategy, portfolio accounting, benchmark returns, walk-forward validation, bootstrap confidence intervals, or actual liquidity/slippage modeling.
- Simple 20-day moving-average trend confirmation is a placeholder.
- 20-day price confirmation uses the filing date's daily close and is therefore not valid for an intraday trade entered on that same date; next-session entry avoids this.
- Filing timestamp is reduced to New York calendar date and signals enter the following trading session even when an earlier execution could be possible. This is intentionally conservative.
- The 20 bps round-trip cost is illustrative, not an execution estimate.
- Overlapping trade horizons and repeated events are not independent; do not interpret win rates as validated strategy performance.
- Data preparation must resolve amendments, joint filers, duplicated transactions, insider IDs, trading plans, filing footnotes and ownership attribution.
- A robust model requires time-split 2023–2025 development, 2026 holdout, walk-forward evaluation, sector/size benchmark, delisting returns, calibrated probabilities, portfolio constraints and tests across multiple transaction cost assumptions.

## Activation gate
TRACK-only. No live trading, automated order placement, or publication of high-confidence signals until the model beats transparent baselines out of sample, costs included, and passes the user's 30/60/100/150+ signal evaluation milestones.
