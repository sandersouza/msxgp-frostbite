"""Keep v29 source/page/owner guards for the replacement letter shapes."""
import argparse
from pathlib import Path
import presentation_credit_check as parent
from presentation_credit_reference import expected_frame,shadow_credit,audit_credit

def check(build,out,mode,steps=2252):
    previous=parent.expected_frame,parent.shadow_credit,parent.audit_credit
    parent.expected_frame,parent.shadow_credit,parent.audit_credit=expected_frame,shadow_credit,audit_credit
    try:return parent.check(build,out,mode,steps)
    finally:parent.expected_frame,parent.shadow_credit,parent.audit_credit=previous

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('build',type=Path);p.add_argument('out',type=Path);p.add_argument('mode');p.add_argument('steps',type=int,nargs='?',default=2252)
    a=p.parse_args();check(a.build,a.out,a.mode,a.steps)
