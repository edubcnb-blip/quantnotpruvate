import sqlite3, unittest
from core import connect, add, settle, rows, summary, expected_value, profit, import_csv
class TestLedger(unittest.TestCase):
 def setUp(self): self.db=connect(':memory:')
 def tearDown(self): self.db.close()
 def record(self,odds=100,p=.6): return add(self.db,'2026-11-21','NBA','A vs B','Moneyline','A',odds,10,p)
 def test_ev(self): self.assertAlmostEqual(expected_value(100,.6),.2)
 def test_win(self):
  id=self.record();settle(self.db,id,'WIN');s=summary(rows(self.db));self.assertEqual(s['pnl'],10);self.assertEqual(s['roi'],1)
 def test_loss(self):
  id=self.record(-110);settle(self.db,id,'LOSS');self.assertEqual(summary(rows(self.db))['pnl'],-10)
 def test_no_resettle(self):
  id=self.record();settle(self.db,id,'PUSH')
  with self.assertRaises(ValueError): settle(self.db,id,'WIN')
 def test_duplicates(self):
  self.record()
  with self.assertRaises(sqlite3.IntegrityError): self.record()
 def test_import(self):
  csv='event_date,domain,event,market,selection,american_odds,stake\n2026-11-21,NHL,A vs B,Moneyline,A,+120,5\n'
  self.assertEqual(import_csv(self.db,csv),(1,0,0))
 def test_invalid_odds(self):
  with self.assertRaises(ValueError): self.record(50)
 def test_brier(self):
  id=self.record();settle(self.db,id,'WIN');self.assertAlmostEqual(summary(rows(self.db))['brier'],.16)
if __name__=='__main__': unittest.main()
