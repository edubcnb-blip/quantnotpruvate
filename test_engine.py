import unittest
import pandas as pd
from engine import validate,candidates,signals,evaluate
class EngineTests(unittest.TestCase):
 def test_filter(self):
  d=dict(ticker='ABC',accession='1',insider_id='1',insider_name='A',role='CEO',filing_timestamp='2024-01-03T20:00:00Z',transaction_date='2024-01-02',code='P',acquired_disposed='A',shares=10000,price=100,shares_after=20000,direct_indirect='D',is_derivative=False,is_10b5_1=False)
  x=pd.DataFrame([d,{**d,'accession':'2','code':'S'},{**d,'accession':'3','is_10b5_1':True}]);self.assertEqual(len(candidates(x)),1)
  self.assertEqual(len(signals(x)),1)
 def test_no_lookahead(self):
  s=pd.DataFrame([dict(ticker='ABC',filing_day='2024-01-03',buyers_10d=1,purchase_usd=1000000,score=60,insider_signal=True)])
  dates=pd.bdate_range('2023-12-01',periods=90)
  p=pd.DataFrame(dict(ticker='ABC',date=dates,open=100.,high=100.,low=100.,close=100.,volume=10000))
  p.loc[p.date==pd.Timestamp('2024-01-03'),'close']=500
  r=evaluate(s,p)
  self.assertTrue(len(r)>0)
  self.assertTrue((pd.to_datetime(r.entry_day)>pd.Timestamp('2024-01-03')).all())
  self.assertTrue((r.return_gross==0).all())
if __name__=='__main__':unittest.main()
