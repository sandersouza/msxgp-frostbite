"""Audit actual credit pixels/ownership without weakening parent guards."""
import argparse
from pathlib import Path
import presentation_viewport_edges_check as parent
import presentation_open_view_check as credit_parent
from presentation_credit import expected_frame, shadow_credit, audit_credit

def check(build, out, mode, steps=2252):
    old = parent.expected_frame, credit_parent.shadow_credit, credit_parent.audit_credit
    parent.expected_frame = expected_frame
    credit_parent.shadow_credit, credit_parent.audit_credit = shadow_credit, audit_credit
    try:
        return parent.check(build, out, mode, steps)
    finally:
        parent.expected_frame, credit_parent.shadow_credit, credit_parent.audit_credit = old

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('build', type=Path)
    p.add_argument('out', type=Path)
    p.add_argument('mode')
    p.add_argument('steps', type=int, nargs='?', default=2252)
    a = p.parse_args()
    check(a.build, a.out, a.mode, a.steps)
