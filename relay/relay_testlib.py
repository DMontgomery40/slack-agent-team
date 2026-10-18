"""Shared fixtures: the public example config (examples/instance.example.json), pointed at a throwaway instance dir."""
import json,os,tempfile,unittest
from pathlib import Path
from instance import Instance,RELAY_ROOT,load
EXAMPLE=RELAY_ROOT/'examples'/'instance.example.json'
_DATA=json.loads(EXAMPLE.read_text())
TEAM=_DATA['slack']['team'];CHANNEL=_DATA['slack']['channel']
HUMAN=next(iter(_DATA['trusted_humans']))
BOT={n:s['bot_user_id'] for n,s in _DATA['seats'].items()}
OTHER_CHANNEL='C99999999'
STRANGER='U9999999999'

def lab(directory,**seat_patches):
    data=json.loads(json.dumps(_DATA))
    # Most policy tests exercise the full routing matrix, so the fixture opts into following everything;
    # DefaultModeTests checks the shipped default (addressed-only) separately.
    data['default_mode']='follow_conversation'
    for seat,patch in seat_patches.items():data['seats'][seat].update(patch)
    return Instance(data,directory)

def load_example(directory):
    """Write the example as config.json into a private instance dir and load it the way service.py does."""
    d=Path(directory);d.mkdir(mode=0o700,parents=True,exist_ok=True);os.chmod(d,0o700)
    (d/'config.json').write_text(EXAMPLE.read_text())
    return load(d)

def event(ts='1.001',text='The review packet is blue.',user=HUMAN,**extra):
    return dict(dict(team=TEAM,channel=CHANNEL,user=user,ts=ts,text=text),**extra)

def bid_of(prompt):return prompt.split('Batch ID: ')[1].split('\n')[0]
def rev_of(prompt):return prompt.split('Shared team context revision: ')[1].split()[0]

class LabCase(unittest.TestCase):
    patches={}
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.dir=Path(self.tmp.name);self.cfg=lab(self.dir,**self.patches)
    def store(self,cfg=None):
        from notifications import Store
        return Store(self.dir/'deliveries.sqlite',cfg or self.cfg)
