#!/usr/bin/env python3
"""Restore just the recorded portrait/index changes; preserve unrelated edits.

Use --root with a disposable copy to verify rollback without changing the live
workspace. The tar archive and hashes are retained as evidence after rollback.
"""
import argparse
import io
import json
from pathlib import Path
import sys
import tarfile
from portraits import ROOT, REPORTS, digest, read_json


def rollback(root):
    folder=root/REPORTS
    changes=read_json(folder/'changes.json')
    # Validate everything before restoring any file. A later user edit is never
    # overwritten just because its path belonged to this repair.
    for path, info in changes.items():
        relative=Path(path)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Invalid rollback path: '+path)
        p=root/relative
        actual=digest(p.read_bytes()) if p.is_file() else None
        if actual!=info['after']:
            raise ValueError('File changed after repair; preserve it: '+path)
    with tarfile.open(folder/'baseline/originals.tar.gz','r:gz') as archive:
        originals={m.name:m for m in archive.getmembers() if m.isfile()}
        restored={}
        for path, info in changes.items():
            if info['before'] is not None:
                if path not in originals:raise ValueError('Missing original: '+path)
                raw=archive.extractfile(originals[path]).read()
                if digest(raw)!=info['before']:raise ValueError('Original hash mismatch: '+path)
                restored[path]=raw
        for path, info in changes.items():
            p=root/path
            if info['before'] is None:
                p.unlink()
            else:
                p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(restored[path])
    for path,info in changes.items():
        p=root/path;actual=digest(p.read_bytes()) if p.is_file() else None
        if actual!=info['before']:raise ValueError('Rollback verification failed: '+path)
    print(f'Restored and verified {len(changes)} portrait/index paths; unrelated files preserved.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    args=parser.parse_args();rollback(args.root.resolve())
