import unittest
from tron import Arena,Rider,run

def rider(id,p,h): return Rider(id,id,'#ffffff','defensive',p,h)
class Rules(unittest.TestCase):
    def test_head_on(self):
        a=Arena(5,5,[rider('a',(1,2),1),rider('b',(3,2),3)])
        self.assertEqual(a.step({'a':1,'b':3}),{'a':'head-on','b':'head-on'})
        self.assertFalse(a.alive)
    def test_swap_hits_trails(self):
        a=Arena(5,5,[rider('a',(1,2),1),rider('b',(2,2),3)])
        self.assertEqual(a.step({'a':1,'b':3}),{'a':'trail','b':'trail'})
    def test_wall_and_survivor(self):
        a=Arena(5,5,[rider('a',(0,0),0),rider('b',(3,3),3)])
        self.assertEqual(a.step({'a':0,'b':3}),{'a':'wall'})
        self.assertEqual(a.alive,{'b'})
    def test_reproducible_and_color_independent(self):
        c={'width':8,'height':8,'riders':[rider('a',(1,1),1).__dict__.copy(),rider('b',(6,6),3).__dict__.copy()]}
        first=run(c,42)
        self.assertEqual(first,run(c,42))
        c['riders'][0]['color']='#ff0000'
        self.assertEqual(first['frames'],run(c,42)['frames'])
if __name__=='__main__': unittest.main()
