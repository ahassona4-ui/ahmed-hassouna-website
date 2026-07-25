#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from copy import deepcopy
import argparse, json, shutil, sys, yaml

def split_frontmatter(path: Path):
    text=path.read_text(encoding='utf-8'); end=text.find('\n---',4)
    if not text.startswith('---\n') or end<0: raise ValueError(f'{path}: invalid frontmatter')
    return yaml.safe_load(text[4:end]) or {}, text[end+4:].lstrip('\n')

def write_frontmatter(path: Path,data,body):
    text='---\n'+yaml.safe_dump(data,allow_unicode=True,sort_keys=False,width=100000)+'---\n'+body
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text,encoding='utf-8')

def omit_empty(value):
    if isinstance(value,dict):
        out={}
        for k,v in value.items():
            x=omit_empty(v)
            if x is None or x=='' or x==[] or x=={}: continue
            out[k]=x
        return out
    if isinstance(value,list):
        out=[]
        for v in value:
            x=omit_empty(v)
            if x is None or x=='' or x==[] or x=={}: continue
            out.append(x)
        return out
    return value

def migrate(data,classification):
    version=str(data.get('schema_version',''))
    if version=='2.0': return deepcopy(data)
    if version not in {'1.0','1.1'}: raise ValueError(f'Unsupported schema_version {version!r}')
    content_id=data.get('article_id') or data.get('project_id')
    state=classification['records'].get(content_id)
    if not state: raise ValueError(f'Missing classification for {content_id}')
    out=deepcopy(data); out['schema_version']='2.0'; out.pop('legacy_date_pending',None)
    rebuilt={}
    for key,value in out.items():
        rebuilt[key]=value
        if key=='order' and out.get('content_type')=='article':
            rebuilt['publication_date_state']=state['publication_date_state']
            rebuilt['media_state']=state['media_state']; rebuilt['claims_state']=state['claims_state']
        if key=='featured' and out.get('content_type')=='project':
            rebuilt['media_state']=state['media_state']; rebuilt['claims_state']=state['claims_state']
    out=rebuilt
    if out.get('content_type')=='article':
        if state['publication_date_state']!='recorded': out.pop('published_at',None)
        if state['media_state']!='ready': out.pop('media',None)
        if state['claims_state']!='structured': out.pop('claims',None)
    else:
        media=out.get('media') or {}
        if media.get('decorative') is True: media.pop('alt',None)
        out['media']=media
        if state['claims_state']!='structured': out.pop('claims',None)
    seo=out.get('seo') or {}; seo.pop('og_image',None) if seo.get('og_image') in (None,'',[],{}) else None; out['seo']=seo
    review=out.get('review') or {}; review['timestamp_state']=state['review_timestamp_state']
    if state['review_timestamp_state']!='recorded': review.pop('reviewed_at',None)
    out['review']=review
    return omit_empty(out)

def main():
    p=argparse.ArgumentParser(description='Deterministically migrate AH Website content records from v1.x to v2.0.')
    p.add_argument('--source-root',required=True); p.add_argument('--output-root',required=True)
    p.add_argument('--classification',required=True); p.add_argument('--report-json')
    args=p.parse_args(); src=Path(args.source_root).resolve(); dst=Path(args.output_root).resolve()
    classification=json.loads(Path(args.classification).read_text(encoding='utf-8'))
    if src==dst: raise SystemExit('Source and output roots must differ for controlled migration.')
    if dst.exists(): shutil.rmtree(dst)
    dst.mkdir(parents=True)
    results=[]
    for folder in ('_projects','_articles'):
        for path in sorted((src/folder).glob('*.md')):
            data,body=split_frontmatter(path); migrated=migrate(data,classification)
            target=dst/path.relative_to(src); write_frontmatter(target,migrated,body)
            results.append({'path':str(path.relative_to(src)),'source_version':str(data.get('schema_version')),'target_version':'2.0'})
    report={'records':results,'count':len(results),'dates_inferred':False}
    if args.report_json: Path(args.report_json).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f'PASS: migrated {len(results)} records to schema 2.0 without date inference')
if __name__=='__main__': main()
