import os
from datetime import date
import pandas as pd
import streamlit as st
from core import connect, add, settle, rows, summary, expected_value, breakeven, profit, export_csv, import_csv, DOMAINS

st.set_page_config(page_title='OmniQuant',page_icon='📊',layout='wide')
st.title('OmniQuant | Research Command Center')
st.caption('Local-first MVP • Manual research ledger • No live odds or automated execution • TRACK-only signals')
db=connect(os.environ.get('OMNIQUANT_DB','omniquant.db'))
page=st.sidebar.radio('Workspace',['Dashboard','Add prediction','Settle results','Import / Export','Risk calculator','Roadmap'])
allrows=rows(db)

def fmt_pct(v): return '—' if v is None else f'{v:.1%}'
if page=='Dashboard':
    domain=st.selectbox('Filter', ['ALL',*DOMAINS]); data=rows(db,domain); s=summary(data)
    c=st.columns(5)
    for col,(label,val) in zip(c,[('Predictions',s['records']),('Pending',s['pending']),('Win rate',fmt_pct(s['win_rate'])),('Realized P/L',f"${s['pnl']:,.2f}"),('ROI',fmt_pct(s['roi']))]): col.metric(label,val)
    st.caption(f"Brier score: {s['brier']:.4f} ({s['brier_n']} graded probability predictions)" if s['brier'] is not None else 'Brier score: not enough probability predictions settled')
    if data:
        df=pd.DataFrame(data)
        st.dataframe(df[['id','event_date','domain','event','market','selection','american_odds','stake','model_probability','status','model_version']],hide_index=True,use_container_width=True)
        settled=df[df.status.isin(['WIN','LOSS','PUSH'])].sort_values('id')
        if not settled.empty:
            settled=settled.copy();settled['pnl']=[profit(r.american_odds,r.stake,r.status) for r in settled.itertuples()]
            settled['cumulative_pnl']=settled.pnl.cumsum();st.line_chart(settled.set_index('id')['cumulative_pnl'])
    else: st.info('No predictions recorded. Add one or import a CSV. Metrics do not include example data.')
elif page=='Add prediction':
    with st.form('add'):
        a,b=st.columns(2)
        with a:
            dt=st.date_input('Event date',date.today());domain=st.selectbox('Domain',DOMAINS);event=st.text_input('Event / ticker');market=st.text_input('Market (e.g., Moneyline, Long)')
        with b:
            selection=st.text_input('Selection');odds=st.number_input('American odds',value=-110,step=5);stake=st.number_input('Stake ($)',min_value=0.01,value=10.0);prob=st.number_input('Model probability (%) — 0 if unknown',min_value=0.0,max_value=99.9,value=0.0,step=0.5)
        source=st.text_input('Source / sportsbook');version=st.text_input('Model version',value='manual-v1');notes=st.text_area('Research notes');submitted=st.form_submit_button('Save prediction')
    if submitted:
        try:
            add(db,dt.isoformat(),domain,event,market,selection,int(odds),stake,prob/100 if prob else None,source,version,notes)
            st.success('Prediction saved as PENDING.');st.rerun()
        except Exception as exc: st.error(str(exc))
    if prob:
        try: st.write(f'Estimated EV: {expected_value(int(odds),prob/100):+.2%} | Break-even probability: {breakeven(int(odds)):.2%}')
        except ValueError: pass
elif page=='Settle results':
    pending=[r for r in allrows if r['status']=='PENDING']
    if not pending: st.info('No pending predictions.')
    else:
        options={f"#{r['id']} | {r['event_date']} | {r['event']} | {r['selection']}":r['id'] for r in pending}
        pick=st.selectbox('Prediction',list(options));result=st.selectbox('Final result',['WIN','LOSS','PUSH','VOID'])
        st.warning('Settlement is final in this MVP. Verify the result before saving.')
        if st.button('Confirm result'):
            try: settle(db,options[pick],result);st.success('Result saved.');st.rerun()
            except ValueError as exc: st.error(str(exc))
elif page=='Import / Export':
    st.download_button('Export all predictions CSV',export_csv(allrows),'omniquant_predictions.csv','text/csv')
    st.write('Import new pending predictions. Required columns: event_date, domain, event, market, selection, american_odds, stake. Optional: model_probability (0–1), source, model_version, notes. Existing settled results cannot be overwritten.')
    upload=st.file_uploader('Choose CSV',type='csv')
    if upload and st.button('Import CSV'):
        try:
            result=import_csv(db,upload.getvalue().decode('utf-8-sig'))
            st.success(f'Imported: {result[0]} | Duplicates: {result[1]} | Invalid rows: {result[2]}')
        except Exception as exc: st.error(str(exc))
elif page=='Risk calculator':
    bankroll=st.number_input('Current bankroll ($)',min_value=1.0,value=500.0)
    max_day=st.slider('Maximum daily exposure (%)',1,20,10)
    pct=st.slider('Proposed stake (% of bankroll)',1.0,10.0,2.0,0.5)
    odds=st.number_input('American odds',value=-110,step=5,key='riskodds')
    p=st.number_input('Estimated probability (%)',min_value=0.0,max_value=99.9,value=55.0,step=0.5)
    try:
        ev=expected_value(odds,p/100);stake=bankroll*pct/100
        st.metric('Proposed stake',f'${stake:,.2f}');st.metric('Daily exposure ceiling',f'${bankroll*max_day/100:,.2f}');st.metric('Estimated EV',f'{ev:+.2%}')
        st.metric('Break-even probability',f'{breakeven(odds):.2%}')
        if ev<=0: st.warning('Non-positive estimated EV: TRACK-only, not a recommendation.')
    except ValueError as exc: st.error(str(exc))
else:
    st.markdown('''### Release plan
- **v0.1 (this package):** Local prediction ledger, settlement, CSV import/export, metrics, bankroll calculator.
- **v0.2:** Automated score ingestion with verified providers, timestamped odds snapshots, corrections/audit log.
- **v0.3:** Reproducible walk-forward backtests, baselines, uncertainty, per-market activation gates.
- **v0.4:** SEC Form 4 collector and insider research signals (separate prototype included).
- **v0.5:** Forex technical scanner, 4H/1H/5M signals, historical execution simulation.
- **v1.0:** Multi-user authentication, hosted PostgreSQL, agent coordinator, secure API, mobile-friendly PWA.

**Data policy:** Never mix sample predictions with real results. No automated wagering or live order execution in this release.''')
