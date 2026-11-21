"""Insider Intelligence Engine: offline, reproducible Form 4 research pipeline.
Input: normalized transactions CSV and daily adjusted OHLCV CSV.
No live orders, no claims of historical returns without real inputs.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd

TX_COLS=['ticker','accession','insider_id','insider_name','role','filing_timestamp','transaction_date','code','acquired_disposed','shares','price','shares_after','direct_indirect','is_derivative','is_10b5_1']
PRICE_COLS=['ticker','date','open','high','low','close','volume']

def validate(tx, px):
    for name, frame, cols in [('transactions',tx,TX_COLS),('prices',px,PRICE_COLS)]:
        missing=set(cols)-set(frame.columns)
        if missing: raise ValueError(f'{name} missing columns: {sorted(missing)}')
    tx=tx.copy();px=px.copy()
    tx['filing_timestamp']=pd.to_datetime(tx.filing_timestamp,utc=True,errors='coerce')
    tx['transaction_date']=pd.to_datetime(tx.transaction_date,errors='coerce')
    px['date']=pd.to_datetime(px.date,errors='coerce').dt.normalize()
    for c in ['shares','price','shares_after']: tx[c]=pd.to_numeric(tx[c],errors='coerce')
    for c in ['open','high','low','close','volume']:px[c]=pd.to_numeric(px[c],errors='coerce')
    if tx.filing_timestamp.isna().any() or px.date.isna().any():raise ValueError('Invalid dates')
    if px.duplicated(['ticker','date']).any():raise ValueError('Duplicate price dates')
    return tx,px.sort_values(['ticker','date'])

def candidates(tx):
    # Exclude options, gifts, grants, sells, indirect ownership and preplanned trades.
    x=tx[(tx.code.astype(str).str.upper()=='P') & (tx.acquired_disposed.astype(str).str.upper()=='A') &
         (tx.direct_indirect.astype(str).str.upper()=='D') &
         (tx.is_derivative.astype(str).str.lower().isin(['false','0','no'])) &
         (tx.is_10b5_1.astype(str).str.lower().isin(['false','0','no']))].copy()
    x=x[(x.shares>0)&(x.price>0)]
    x['notional']=x.shares*x.price
    x=x.drop_duplicates(['accession','insider_id','transaction_date','shares','price'])
    return x

def signals(tx):
    x=candidates(tx)
    if x.empty:return pd.DataFrame(columns=['ticker','filing_day','buyers_10d','purchase_usd','score','insider_signal'])
    x['filing_day']=pd.to_datetime(x.filing_timestamp,utc=True).dt.tz_convert('America/New_York').dt.date.astype(str)
    out=[]
    for (ticker,day),grp in x.groupby(['ticker','filing_day']):
        cutoff=pd.Timestamp(day)-pd.Timedelta(days=10)
        history=x[(x.ticker==ticker)&(pd.to_datetime(x.filing_day)>=cutoff)&(x.filing_day<=day)]
        buyers=history.insider_id.nunique()
        amount=grp.notional.sum()
        # Explicitly heuristic, not a probability or calibrated signal.
        cluster=min(buyers/3,1)*25
        size=min(amount/500000,1)*20
        executive=15 if grp.role.astype(str).str.contains('CEO|CFO',case=False,regex=True).any() else 0
        repeat=15 if history.groupby('insider_id').size().max()>=2 else 0
        score=round(cluster+size+executive+repeat,2)
        out.append(dict(ticker=ticker,filing_day=day,buyers_10d=int(buyers),purchase_usd=round(amount,2),score=score,insider_signal=score>=40))
    return pd.DataFrame(out).sort_values(['filing_day','score'],ascending=[True,False])

def evaluate(sig,px,horizons=(5,10,20,60)):
    """Entry next daily OPEN after filing day; exit CLOSE at horizon sessions.
    All returns price-only; adjusted price series recommended for split/dividend effects.
    """
    rows=[]
    for s in sig.itertuples(index=False):
        p=px[(px.ticker==s.ticker)&(px.date>pd.Timestamp(s.filing_day))].sort_values('date').reset_index(drop=True)
        if p.empty:continue
        entry=p.iloc[0]
        if not np.isfinite(entry.open) or entry.open<=0:continue
        # Trend confirmation uses only information available before the entry day.
        prior=px[(px.ticker==s.ticker)&(px.date<=pd.Timestamp(s.filing_day))].sort_values('date')
        tech=bool(len(prior)>=20 and prior.iloc[-1].close>prior.tail(20).close.mean())
        for h in horizons:
            if len(p)<h:continue
            exitrow=p.iloc[h-1]
            gross=exitrow.close/entry.open-1
            for strategy,selected in [('insider_only',bool(s.insider_signal)),('combined',bool(s.insider_signal and tech))]:
                if selected:
                    rows.append(dict(strategy=strategy,ticker=s.ticker,signal_day=s.filing_day,entry_day=str(entry.date.date()),exit_day=str(exitrow.date.date()),horizon=h,score=s.score,return_gross=gross,return_net=gross-0.002,technical_confirmed=tech))
    return pd.DataFrame(rows)

def summarize(trades):
    if trades.empty:return pd.DataFrame(columns=['strategy','horizon','n','win_rate','mean_net_return','median_net_return'])
    return trades.groupby(['strategy','horizon']).return_net.agg(n='count',win_rate=lambda x:(x>0).mean(),mean_net_return='mean',median_net_return='median').reset_index()

def run(txfile,pricefile,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    tx,px=validate(pd.read_csv(txfile),pd.read_csv(pricefile))
    sig=signals(tx);trades=evaluate(sig,px);summary=summarize(trades)
    sig.to_csv(out/'signals.csv',index=False)
    trades.to_csv(out/'trades.csv',index=False)
    summary.to_csv(out/'summary.csv',index=False)
    (out/'run_metadata.json').write_text(json.dumps({'transactions':len(tx),'qualified_transactions':len(candidates(tx)),'signals':len(sig),'trades':len(trades),'cost_round_trip':0.002,'data_source':'user-supplied CSV','validation':'research only; no causal or out-of-sample claims'},indent=2))
    return summary

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--transactions',required=True);parser.add_argument('--prices',required=True);parser.add_argument('--output',default='results');a=parser.parse_args()
    print(run(a.transactions,a.prices,a.output).to_string(index=False))
