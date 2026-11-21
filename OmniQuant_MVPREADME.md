# OmniQuant MVP v0.1

A functioning **local-first research dashboard**, not a deployed cloud service. Stores real predictions in SQLite and never silently generates fake results.

## Quick start

Requires Python 3.10+.

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

Open the local URL shown by Streamlit (typically http://localhost:8501). To use on your iPhone, deploy behind authenticated HTTPS; do not expose the unauthenticated local app directly to the internet.

## Test

```bash
python -m unittest discover -v
```

## Features
- Dashboard with actual recorded win rate, ROI, cumulative profit/loss, and Brier score when probability forecasts are present.
- Manual prediction entry, unique-key duplicate protection, immutable first settlement, CSV export/import.
- Risk and break-even probability calculator.
- Separate domains for sports and markets. Trade entries are recorded as research outcomes using American-odds-style payoffs for now; **this is not a true trade execution/P&L accounting engine**.
- Database persists in `omniquant.db` in the launch directory. Back it up regularly.

## Data contract
Required import CSV columns: `event_date,domain,event,market,selection,american_odds,stake`. Optional: `model_probability,source,model_version,notes`. Probability is a fraction between 0 and 1. Imports create **pending** entries only; settlement must be verified manually. Unique key: date/domain/event/market/selection/odds/model version. Exports include all rows.

## Important limitations
- No automatic sportsbook odds, scores, brokerage orders, SEC ingestion, AI agents, model fitting, multi-user security, audit revisions, or backtesting pipeline yet.
- A settled prediction cannot be corrected through the UI. A production version must add authorized, audited corrections.
- Dashboard ROI is realized P/L divided by all settled stake including pushes; voids excluded. It is not a portfolio time-weighted return.
- The model probability is user-entered, not validated or calibrated by this application.
- No demo data is inserted into real records. Unit tests use isolated in-memory databases.
- SQLite is for one local user; migrate to PostgreSQL with auth before public deployment.

## Development milestones
1. **v0.2:** sports score and odds ingestion, provider contracts, timestamp integrity, result audit log.
2. **v0.3:** point-in-time historical store, walk-forward model evaluation, benchmarks, bootstrap confidence intervals, and activation gates.
3. **v0.4:** SEC Form 4 collector + security master + market data; connect separate Insider Intelligence prototype after validation.
4. **v0.5:** stock/forex technical analysis and simulated order ledger with fees, slippage, and market sessions.
5. **v1.0:** FastAPI service, PostgreSQL, authentication, background jobs, agents, responsive PWA; native mobile only if needed.

## Suggested hosting
Streamlit Community Cloud can host a prototype, but its filesystem may be ephemeral: use a persistent managed database and authentication before entering sensitive or important data. GitHub for version control; GitHub Actions for tests. Keep API keys in secrets, never in the repository.
