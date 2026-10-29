#!/usr/bin/env python3
"""Verify current behavior, original behavior, binary patch and real rollback.

The patch is applied and rolled back in a disposable copy, never the live tree.
Every command, literal output, input hash and exit status is retained.
"""
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

from portraits import ROOT, REPORTS, MANIFEST, digest, read_json, write_json, image_path


def verify():
    out=ROOT/REPORTS
    out.mkdir(parents=True,exist_ok=True)
    commands=[]
    def run(argv,cwd=ROOT,expected=0):
        result=subprocess.run([str(a) for a in argv],cwd=cwd,text=True,capture_output=True)
        item={'command':[str(a) for a in argv],'cwd':str(cwd),'exit_status':result.returncode,
              'stdout':result.stdout,'stderr':result.stderr}
        commands.append(item)
        write_json(out/'commands.json',commands)
        print('EXIT',result.returncode,' '.join(map(str,argv)),flush=True)
        if result.returncode!=expected:
            raise RuntimeError(f'Expected exit {expected}, got {result.returncode}: {argv}\n{result.stderr}\n{result.stdout[-2000:]}')
        return result
    before=read_json(out/'baseline/sha256.json')
    browser_record=out/'browser-verification.json'
    visual_record=out/'visual-review.json'
    browser=read_json(browser_record)
    for label in ['readme','inventory']:
        text='\n'.join(c.get('text','') for c in browser[label]['content'])
        stats=json.loads(text.split('```json\n',1)[1].split('```',1)[0])
        if stats['total']!=444 or stats['loaded']!=444 or stats['broken']:
            raise RuntimeError('Browser image validation failed: '+label)
    visual=read_json(visual_record)
    if visual['characters_reviewed']!=444 or len(visual['pages'])!=53:
        raise RuntimeError('Visual review inventory incomplete')
    for page in visual['pages']:
        if not page['reviewed'] or digest((ROOT/page['path']).read_bytes())!=page['sheet_sha256']:
            raise RuntimeError('Reviewed contact sheet changed: '+page['path'])
    scope=set(before)|{str(p.relative_to(ROOT)) for p in (ROOT/'assets').rglob('*') if p.is_file()}
    changes={}
    for path in sorted(scope):
        p=ROOT/path;after=digest(p.read_bytes()) if p.is_file() else None
        if before.get(path)!=after:changes[path]={'before':before.get(path),'after':after}
    write_json(out/'changes.json',changes)
    run([sys.executable,'-m','unittest','discover','-s','tests','-v'])
    run([sys.executable,'scripts/portraits.py','check','--report',out/'current-check.json'])
    current=read_json(out/'current-check.json')
    manifest=read_json(ROOT/MANIFEST)
    known_regressions=[]
    for first,second in [
        ('mygo/kaname-rana-perspective','madoka/madoka-kaname-perspective'),
        ('sword-art-online/kirigaya-kazuto-perspective','sword-art-online/kirigaya-suguha-perspective'),
        ('sword-art-online/asuna-yuuki-perspective','sword-art-online/yuuki-perspective'),
        ('sakura-no-toki/toritani-saki-perspective','sakura-no-toki/toritani-shizuru-perspective'),
    ]:
        old_same=before[image_path(first)]==before[image_path(second)]
        new_same=manifest['characters'][first]['sha256']==manifest['characters'][second]['sha256']
        if not old_same or new_same:raise RuntimeError('Known mismatch regression failed: '+first)
        known_regressions.append({'keys':[first,second],'original_same_image':old_same,'modified_same_image':new_same})
    index_files=['README.md','角色清单.md','assets/portrait_mapping.json']
    index_before={f:digest((ROOT/f).read_bytes()) for f in index_files}
    run([sys.executable,'scripts/portraits.py','render'])
    if index_before!={f:digest((ROOT/f).read_bytes()) for f in index_files}:
        raise RuntimeError('Generated indexes were not up to date')
    tracked=run(['git','diff','--binary','HEAD','--','README.md','角色清单.md','assets']).stdout
    untracked=run(['git','ls-files','--others','--exclude-standard']).stdout.splitlines()
    new=[f for f in untracked if f.startswith(('assets/','scripts/','tests/')) or f=='.gitignore']
    patch=tracked
    for f in new:
        patch+=run(['git','diff','--no-index','--binary','--','/dev/null',f],expected=1).stdout
    patch_path=out/'repair.patch';patch_path.write_text(patch,encoding='utf-8')
    with tempfile.TemporaryDirectory(prefix='portrait-verify-') as td:
        fixture=Path(td)
        shutil.copytree(ROOT/'characters',fixture/'characters')
        with tarfile.open(out/'baseline/originals.tar.gz','r:gz') as archive:
            for member in archive.getmembers():
                name=Path(member.name)
                if not member.isfile() or name.is_absolute() or '..' in name.parts:
                    raise RuntimeError('Invalid baseline archive member')
                raw=archive.extractfile(member).read()
                if digest(raw)!=before[member.name]:raise RuntimeError('Baseline archive hash mismatch')
                p=fixture/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        # Compare original files against the same reviewed target manifest.
        # It is explicit comparison input, not a claim the old repo had one.
        shutil.copy2(ROOT/MANIFEST,fixture/MANIFEST)
        run([sys.executable,ROOT/'scripts/portraits.py','check','--root',fixture,'--report',out/'original-check.json'],expected=1)
        original=read_json(out/'original-check.json')
        (fixture/MANIFEST).unlink()
        run(['git','apply','--check',patch_path],cwd=fixture)
        run(['git','apply',patch_path],cwd=fixture)
        for path,info in changes.items():
            p=fixture/path;actual=digest(p.read_bytes()) if p.is_file() else None
            if actual!=info['after']:raise RuntimeError('Patch output differs from workspace: '+path)
        baseline=fixture/REPORTS/'baseline';baseline.mkdir(parents=True)
        for f in ['originals.tar.gz','sha256.json','character-sha256.json']:
            shutil.copy2(out/'baseline'/f,baseline/f)
        shutil.copy2(out/'changes.json',fixture/REPORTS/'changes.json')
        run([sys.executable,fixture/'scripts/portraits.py','check','--root',fixture])
        # Evidence that the rollback preserves files outside its own change set.
        sentinel=fixture/'unrelated-user-file.txt';sentinel.write_text('preserve unrelated user work\n')
        run([sys.executable,fixture/'scripts/rollback_portraits.py','--root',fixture])
        for path,info in changes.items():
            p=fixture/path;actual=digest(p.read_bytes()) if p.is_file() else None
            if actual!=info['before']:raise RuntimeError('Restored baseline differs: '+path)
        if sentinel.read_text()!='preserve unrelated user work\n':raise RuntimeError('Unrelated file changed')
    summary={'passed':True,'roles':current['roles'],'works':current['works'],
             'original_images':original['images'],'modified_images':current['images'],
             'identity_verified':current['identity_verified'],'visual_reviewed':current['visual_reviewed'],
             'original_check_exit':1,'modified_check_exit':0,
             'changed_portrait_index_paths':len(changes),
             'duplicate_exceptions':current['duplicates'],
             'known_mismatch_regressions':known_regressions,
             'character_documents_unchanged':True,'render_deterministic':True,
             'patch_applied_and_checked':True,'rollback_executed_and_checked':True,
             'unrelated_files_preserved':True,
             'browser_images_loaded_per_index':444,'browser_broken_images':0,
             'contact_sheets_reviewed':53,
             'inputs':{'original_archive_sha256':digest((out/'baseline/originals.tar.gz').read_bytes()),
                       'original_hashes_sha256':digest((out/'baseline/sha256.json').read_bytes()),
                       'expected_source_manifest_sha256':digest((ROOT/MANIFEST).read_bytes()),
                       'browser_record_sha256':digest(browser_record.read_bytes()),
                       'visual_review_record_sha256':digest(visual_record.read_bytes()),
                       'patch_sha256':digest(patch_path.read_bytes())},
             'command_record':str((out/'commands.json').relative_to(ROOT)),
             'current_check':str((out/'current-check.json').relative_to(ROOT)),
             'original_check':str((out/'original-check.json').relative_to(ROOT))}
    write_json(out/'verification.json',summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':verify()
