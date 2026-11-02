#!/usr/bin/env python3
"""Hash a completed UnityTextLabB build without exposing private answer labels."""
from pathlib import Path
import argparse
import hashlib
import json


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda:f.read(1<<20),b''):h.update(part)
    return h.hexdigest()


def seal(build_data,private,out):
    build_data=Path(build_data)
    private=Path(private)
    asm=build_data/'Managed/Assembly-CSharp.dll'
    fingerprint=private/'public_fingerprint_ONLY.json'
    if not asm.is_file() or not fingerprint.is_file():
        raise FileNotFoundError('Missing built Mono DLL or private public_fingerprint_ONLY.json')
    files=[]
    for f in sorted(build_data.rglob('*')):
        if f.is_file() and (f.suffix.lower() in ('.assets','.resource','.resS'.lower()) or f.name.lower().startswith('level') or f.name=='Assembly-CSharp.dll'):
            files.append({'relative_path':f.relative_to(build_data).as_posix(),
                          'size':f.stat().st_size,'sha256':digest(f)})
    meta=json.loads(fingerprint.read_text(encoding='utf-8'))
    if not files:raise ValueError('Build data was empty')
    result={'schema':'modstudio.m04.build_sha256_manifest.v0.1',
            'eval_id':meta['eval_id'], 'private_truth_sha256':meta['private_ground_truth_sha256'],
            'assembly_sha256':digest(asm),'build_files':files,
            'warning':'Only hashes and file names; this is not a reference answer key.'}
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--build-data',required=True)
    p.add_argument('--private-dir',required=True)
    p.add_argument('--out',required=True)
    a=p.parse_args()
    try:
        x=seal(a.build_data,a.private_dir,a.out)
        print(json.dumps({'status':'sealed','eval_id':x['eval_id'],'files':len(x['build_files'])},ensure_ascii=False))
    except (OSError,KeyError,ValueError) as ex:
        p.exit(2,f'ERROR: {ex}\n')
