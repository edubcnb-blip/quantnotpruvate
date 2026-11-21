"""OmniQuant local ledger and metrics. No external network required."""
import csv, io, sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = '''CREATE TABLE IF NOT EXISTS predictions (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 created_at TEXT NOT NULL, event_date TEXT NOT NULL,
 domain TEXT NOT NULL CHECK(domain IN ('NBA','NFL','NCAAF','NHL','NCAAB','FOREX','STOCKS','GOLD','NASDAQ','OTHER')),
 event TEXT NOT NULL, market TEXT NOT NULL, selection TEXT NOT NULL,
 american_odds INTEGER NOT NULL, stake REAL NOT NULL CHECK(stake > 0),
 model_probability REAL CHECK(model_probability IS NULL OR (model_probability > 0 AND model_probability < 1)),
 status TEXT NOT NULL DEFAULT 'PENDING' CHECK(status IN ('PENDING','WIN','LOSS','PUSH','VOID')),
 source TEXT NOT NULL DEFAULT '', model_version TEXT NOT NULL DEFAULT 'manual-v1',
 notes TEXT NOT NULL DEFAULT '', settled_at TEXT,
 UNIQUE(event_date, domain, event, market, selection, american_odds, model_version)
);'''
DOMAINS = ('NBA','NFL','NCAAF','NHL','NCAAB','FOREX','STOCKS','GOLD','NASDAQ','OTHER')
STATUSES = ('PENDING','WIN','LOSS','PUSH','VOID')

def connect(path='omniquant.db'):
    db = sqlite3.connect(str(path)); db.row_factory = sqlite3.Row
    db.execute('PRAGMA busy_timeout=5000'); db.execute('PRAGMA journal_mode=WAL')
    db.executescript(SCHEMA); return db

def decimal_odds(american):
    a=int(american)
    if -100 < a < 100: raise ValueError('American odds must be >= +100 or <= -100')
    return 1+a/100 if a>0 else 1+100/abs(a)

def breakeven(american): return 1/decimal_odds(american)
def expected_value(american, probability):
    if probability is None: return None
    p=float(probability)
    if not 0 < p < 1: raise ValueError('Probability must be between 0 and 1')
    return p*decimal_odds(american)-1

def profit(american, stake, status):
    if status=='WIN': return round(float(stake)*(decimal_odds(american)-1),2)
    if status=='LOSS': return -float(stake)
    return 0.0

def add(db, event_date, domain, event, market, selection, american_odds, stake, model_probability=None, source='', model_version='manual-v1', notes=''):
    if domain not in DOMAINS: raise ValueError('Unsupported domain')
    datetime.fromisoformat(event_date)
    if not event.strip() or not market.strip() or not selection.strip(): raise ValueError('Event, market and selection are required')
    decimal_odds(american_odds)
    if float(stake)<=0: raise ValueError('Stake must be positive')
    if model_probability is not None and not 0<float(model_probability)<1: raise ValueError('Probability must be 0–1')
    with db:
        cur=db.execute('''INSERT INTO predictions(created_at,event_date,domain,event,market,selection,american_odds,stake,model_probability,source,model_version,notes)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''', (datetime.now(timezone.utc).isoformat(),event_date,domain,event.strip(),market.strip(),selection.strip(),int(american_odds),float(stake),model_probability,source,model_version,notes))
    return cur.lastrowid

def settle(db, id, status):
    if status not in STATUSES or status=='PENDING': raise ValueError('Invalid settlement status')
    with db:
        cur=db.execute("UPDATE predictions SET status=?,settled_at=? WHERE id=? AND status='PENDING'",(status,datetime.now(timezone.utc).isoformat(),id))
    if cur.rowcount!=1: raise ValueError('Not found or already settled; no overwrite allowed')

def rows(db, domain=None):
    if domain and domain!='ALL': return [dict(r) for r in db.execute('SELECT * FROM predictions WHERE domain=? ORDER BY id DESC',(domain,))]
    return [dict(r) for r in db.execute('SELECT * FROM predictions ORDER BY id DESC')]

def summary(records):
    settled=[r for r in records if r['status'] in ('WIN','LOSS','PUSH')]
    resolved=[r for r in settled if r['status'] in ('WIN','LOSS')]
    risk=sum(r['stake'] for r in settled)
    pnl=sum(profit(r['american_odds'],r['stake'],r['status']) for r in settled)
    wins=sum(r['status']=='WIN' for r in resolved)
    brier=[(float(r['model_probability'])-(1 if r['status']=='WIN' else 0))**2 for r in resolved if r['model_probability'] is not None]
    return {'records':len(records),'pending':sum(r['status']=='PENDING' for r in records), 'settled':len(settled),'wins':wins,'losses':len(resolved)-wins,'win_rate':wins/len(resolved) if resolved else None,'risked':round(risk,2),'pnl':round(pnl,2),'roi':pnl/risk if risk else None,'brier':sum(brier)/len(brier) if brier else None,'brier_n':len(brier)}

def export_csv(records):
    output=io.StringIO(); fields=['id','created_at','event_date','domain','event','market','selection','american_odds','stake','model_probability','status','source','model_version','notes','settled_at']
    w=csv.DictWriter(output,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(records)
    return output.getvalue()

def import_csv(db, text):
    reader=csv.DictReader(io.StringIO(text)); needed={'event_date','domain','event','market','selection','american_odds','stake'}
    if not reader.fieldnames or not needed.issubset(reader.fieldnames): raise ValueError('Missing required CSV columns: '+', '.join(sorted(needed)))
    inserted=duplicates=errors=0
    for r in reader:
        try:
            p=r.get('model_probability','').strip()
            add(db,r['event_date'],r['domain'],r['event'],r['market'],r['selection'],int(r['american_odds']),float(r['stake']),float(p) if p else None,r.get('source',''),r.get('model_version') or 'manual-v1',r.get('notes',''))
            inserted+=1
        except sqlite3.IntegrityError: duplicates+=1
        except (ValueError,KeyError,TypeError): errors+=1
    return inserted,duplicates,errors
