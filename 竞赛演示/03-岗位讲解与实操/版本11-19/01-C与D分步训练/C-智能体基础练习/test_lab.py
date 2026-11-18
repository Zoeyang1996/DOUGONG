import unittest
from server import cards,retrieve,answer
class LabTests(unittest.TestCase):
 def test_cards(self):self.assertTrue(cards())
 def test_known(self):self.assertTrue(retrieve('大殿建于哪一年'))
 def test_unknown(self):self.assertEqual(retrieve('火星人口多少'),[])
 def test_boundary(self):self.assertEqual(answer('火星人口多少')['refs'],[])
if __name__=='__main__':unittest.main()
