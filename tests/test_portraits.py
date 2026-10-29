import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import tarfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import portraits as p
import research_portraits as research
import rollback_portraits as rollback


def webp(color='red'):
    b=io.BytesIO();p.Image.new('RGB',(240,320),color).save(b,'WEBP');return b.getvalue()


class PortraitTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.m={'version':1,'works':{'work-a':'Work A','work-b':'Work B'},'characters':{},'duplicate_exceptions':[]}
        for i,work in enumerate(self.m['works']):
            key=work+'/alex-perspective';d=self.root/'characters'/key;d.mkdir(parents=True)
            if i==0:(d/'SKILL.md').write_text('# Alex')
            data=webp(['red','blue'][i]);path=self.root/p.image_path(key);path.parent.mkdir(parents=True);path.write_bytes(data)
            self.m['characters'][key]={'display_name':'Alex','path':p.image_path(key),'identity_verified':True,
              'visual_reviewed':True,'source_page':'https://example.org/'+work+'/alex','image_url':'https://example.org/'+work+'/alex.png',
              'source_name':'Alex','evidence':work+' official Alex character profile','source_sha256':'a'*64,'sha256':p.digest(data),
              'review_note':'Fixture visual review'}
        p.write_json(self.root/p.MANIFEST,self.m);p.render(self.root,self.m)

    def tearDown(self):self.tmp.cleanup()

    def test_all_directories_including_research_only(self):
        self.assertEqual(len(p.inventory(self.root)),2)
        self.assertTrue(p.audit(self.root,self.m)['passed'])

    def test_same_name_different_works_remain_distinct(self):
        mapping=p.read_json(self.root/'assets/portrait_mapping.json')
        self.assertEqual(mapping,{'work-a':['alex-perspective'],'work-b':['alex-perspective']})
        self.assertIn('仅 research',(self.root/'README.md').read_text())

    def test_render_is_deterministic(self):
        before=(self.root/'README.md').read_bytes();p.render(self.root,self.m)
        self.assertEqual(before,(self.root/'README.md').read_bytes())

    def test_path_rejects_free_form_aliases_and_traversal(self):
        for key in ['../alex-perspective','work/alex','work-a/../alex-perspective','alex-perspective']:
            with self.assertRaises(ValueError):p.image_path(key)

    def test_mapping_omission_fails(self):
        p.write_json(self.root/'assets/portrait_mapping.json',{})
        self.assertIn('Mapping is not the complete directory inventory',p.audit(self.root,self.m)['errors'])

    def test_missing_corrupt_and_modified_images_fail(self):
        key='work-a/alex-perspective';path=self.root/p.image_path(key)
        path.write_bytes(b'not an image')
        errors=p.audit(self.root,self.m)['errors']
        self.assertTrue(any(x.startswith('Corrupt image:') for x in errors))
        self.assertTrue(any(x.startswith('Hash mismatch:') for x in errors))
        path.unlink();self.assertTrue(any(x.startswith('Missing image:') for x in p.audit(self.root,self.m)['errors']))

    def test_cross_role_duplicate_requires_exact_documented_exception(self):
        keys=list(self.m['characters']);data=(self.root/p.image_path(keys[0])).read_bytes()
        (self.root/p.image_path(keys[1])).write_bytes(data);self.m['characters'][keys[1]]['sha256']=p.digest(data)
        self.assertFalse(p.audit(self.root,self.m)['passed'])
        self.m['duplicate_exceptions']=[{'keys':keys,'reason':'Explicit fixture: same identity under two archived work directories'}]
        self.assertTrue(p.audit(self.root,self.m)['passed'])
        self.m['duplicate_exceptions'][0]['keys']=keys[:1]
        self.assertFalse(p.audit(self.root,self.m)['passed'])

    def test_unreviewed_sources_do_not_pass(self):
        self.m['characters']['work-a/alex-perspective']['visual_reviewed']=False
        self.assertFalse(p.audit(self.root,self.m)['passed'])

    def test_unverified_source_never_downloads(self):
        with self.assertRaises(ValueError):p.download({'image_url':'https://example.org/test'})

    def test_network_failure_has_three_attempts(self):
        calls=[]
        def bad(*a,**kw):calls.append(1);raise OSError('fixture offline')
        with patch('portraits.time.sleep'):
            with self.assertRaisesRegex(RuntimeError,'3 attempts'):
                p.download(self.m['characters']['work-a/alex-perspective'],request=bad)
        self.assertEqual(len(calls),3)

    def test_unicode_page_url_is_encoded_for_http_headers(self):
        e=self.m['characters']['work-a/alex-perspective'];e['source_page']='https://example.org/博丽灵梦'
        e.pop('source_sha256')
        observed=[]
        def response(req,**kw):
            observed.append(req.get_header('Referer'));return io.BytesIO(webp())
        p.download(e,request=response)
        self.assertTrue(observed[0].isascii())
        self.assertIn('%E5%8D%9A',observed[0])

    def test_source_byte_change_requires_reverification(self):
        def response(*a,**kw):return io.BytesIO(webp())
        with patch('portraits.time.sleep'):
            with self.assertRaisesRegex(RuntimeError,'Source bytes changed'):
                p.download(self.m['characters']['work-a/alex-perspective'],request=response)

    def test_swapped_images_fail_even_when_link_and_image_sets_match(self):
        f=self.root/'README.md';s=f.read_text().replace('assets/portraits/work-a/','SWAP').replace('assets/portraits/work-b/','assets/portraits/work-a/').replace('SWAP','assets/portraits/work-b/');f.write_text(s)
        self.assertIn('Index image/character pairing mismatch: README.md',p.audit(self.root,self.m)['errors'])

    def test_bad_download_is_not_published(self):
        e=self.m['characters']['work-a/alex-perspective'];e.pop('sha256')
        path=self.root/p.image_path('work-a/alex-perspective');original=path.read_bytes()
        with patch('portraits.download',side_effect=RuntimeError('invalid response')):
            p.fetch(self.root,self.m,'work-a')
        self.assertEqual(path.read_bytes(),original)
        self.assertIn('invalid response',self.m['characters']['work-a/alex-perspective']['download_error'])

    def test_aliases_are_exact_not_substring_or_concatenation(self):
        self.assertEqual(research.norm('Kaname, Raana'),research.norm('Raana Kaname'))
        self.assertNotEqual(research.norm('Kaname Rana'),research.norm('Madoka Kaname'))
        self.assertNotEqual(research.norm('Yuuki'),research.norm('Asuna Yuuki'))
        self.assertNotEqual(research.norm('ab c'),research.norm('a bc'))
        self.assertNotEqual(research.norm('双海亚美'),research.norm('双海真美'))

    def test_wrong_anime_id_is_rejected(self):
        with patch('research_portraits.get',return_value='<meta property="og:title" content="Unrelated show">'):
            with self.assertRaisesRegex(ValueError,'identity mismatch'):research.mal_roster(1,'Target Show')

    def test_character_content_baseline_is_checked(self):
        path=self.root/'characters/work-a/alex-perspective/SKILL.md'
        p.write_json(self.root/p.REPORTS/'baseline/character-sha256.json',{'characters/work-a/alex-perspective/SKILL.md':p.digest(path.read_bytes())})
        self.assertTrue(p.audit(self.root,self.m)['passed']);path.write_text('changed')
        self.assertIn('Character documents differ from baseline',p.audit(self.root,self.m)['errors'])

    def test_index_must_link_exact_character_not_just_an_existing_directory(self):
        path=self.root/'README.md';path.write_text(path.read_text().replace('characters/work-a/alex-perspective/','characters/work-b/alex-perspective/'))
        self.assertTrue(any(x.startswith('Index role-link coverage mismatch:') for x in p.audit(self.root,self.m)['errors']))

    def make_rollback(self):
        folder=self.root/p.REPORTS;folder.mkdir(parents=True,exist_ok=True)
        baseline=folder/'baseline';baseline.mkdir()
        path='assets/original.txt';new='assets/new.txt'
        (self.root/path).write_text('modified');(self.root/new).write_text('new')
        raw=b'original'
        with tarfile.open(baseline/'originals.tar.gz','w:gz') as archive:
            info=tarfile.TarInfo(path);info.size=len(raw);archive.addfile(info,io.BytesIO(raw))
        p.write_json(folder/'changes.json',{path:{'before':p.digest(raw),'after':p.digest(b'modified')},
                                           new:{'before':None,'after':p.digest(b'new')}})
        return path,new

    def test_real_rollback_restores_original_removes_new_preserves_unrelated(self):
        path,new=self.make_rollback();unrelated=self.root/'unrelated.txt';unrelated.write_text('user work')
        rollback.rollback(self.root)
        self.assertEqual((self.root/path).read_text(),'original');self.assertFalse((self.root/new).exists())
        self.assertEqual(unrelated.read_text(),'user work')

    def test_rollback_preserves_later_edits_before_writing_anything(self):
        path,new=self.make_rollback();(self.root/new).write_text('later user edit')
        with self.assertRaisesRegex(ValueError,'changed after repair'):rollback.rollback(self.root)
        self.assertEqual((self.root/path).read_text(),'modified')

    def test_rollback_validates_archive_before_writing_anything(self):
        path,new=self.make_rollback();j=self.root/p.REPORTS/'changes.json';d=p.read_json(j)
        d[path]['before']='0'*64;p.write_json(j,d)
        with self.assertRaisesRegex(ValueError,'Original hash mismatch'):rollback.rollback(self.root)
        self.assertEqual((self.root/path).read_text(),'modified');self.assertTrue((self.root/new).exists())


if __name__=='__main__':unittest.main()
