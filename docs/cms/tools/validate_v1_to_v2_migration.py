#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse, filecmp, hashlib, json, subprocess, sys, tempfile

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description='Validate deterministic and idempotent AH v1-to-v2 migration.')
    p.add_argument('--v1-root',required=True); p.add_argument('--v2-root',required=True)
    p.add_argument('--classification',required=True); p.add_argument('--migrator',required=True); p.add_argument('--report-json')
    a=p.parse_args(); v1=Path(a.v1_root).resolve(); v2=Path(a.v2_root).resolve(); migrator=Path(a.migrator).resolve()
    with tempfile.TemporaryDirectory() as td:
        first=Path(td)/'first'; second=Path(td)/'second'
        cmd=[sys.executable,str(migrator),'--source-root',str(v1),'--output-root',str(first),'--classification',a.classification]
        r1=subprocess.run(cmd,capture_output=True,text=True)
        cmd2=[sys.executable,str(migrator),'--source-root',str(first),'--output-root',str(second),'--classification',a.classification]
        r2=subprocess.run(cmd2,capture_output=True,text=True)
        errors=[]; rows=[]
        for folder in ('_projects','_articles'):
            for expected in sorted((v2/folder).glob('*.md')):
                rel=expected.relative_to(v2); generated=first/rel; generated2=second/rel
                equal=generated.is_file() and sha(generated)==sha(expected)
                idem=generated2.is_file() and sha(generated2)==sha(generated)
                rows.append({'path':str(rel),'matches_v2':equal,'second_pass_identical':idem})
                if not equal: errors.append(f'{rel}: first migration does not match approved v2')
                if not idem: errors.append(f'{rel}: second migration pass is not idempotent')
        report={'first_returncode':r1.returncode,'second_returncode':r2.returncode,'records':rows,'errors':errors}
        if a.report_json: Path(a.report_json).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        if r1.returncode or r2.returncode or errors:
            print('\n'.join(errors or [r1.stderr,r2.stderr])); return 1
        print(f'PASS: {len(rows)} deterministic mappings and {len(rows)} idempotence checks')
        return 0
if __name__=='__main__': sys.exit(main())
