#!/usr/bin/env python3
"""Reproducible source collection. Exact identities only; ambiguous results stay pending.

These adapters establish source identity, never visual approval. See portraits.py
for downloading and the explicit contact-sheet review step.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import time
import unicodedata
from urllib.parse import urlencode, unquote
from urllib.parse import urljoin
import requests

from portraits import ROOT, MANIFEST, digest, inventory, image_path, read_json, write_json

CACHE = ROOT / 'artifacts/portrait-repair/sources'


def get(url, payload=None):
    CACHE.mkdir(parents=True, exist_ok=True)
    key = digest((url + json.dumps(payload, sort_keys=True)).encode())
    cache = CACHE / (key + '.txt')
    if cache.exists():
        return cache.read_text(encoding='utf-8')
    for attempt in range(3):
        try:
            kwargs = dict(timeout=30, headers={'User-Agent': 'CharacterPortraitMaintenance/1.0'})
            r = requests.get(url, **kwargs) if payload is None else requests.post(url, json=payload, **kwargs)
            r.raise_for_status()
            r.encoding = 'utf-8'
            cache.write_text(r.text, encoding='utf-8')
            return r.text
        except Exception:
            if attempt == 2:
                raise
            time.sleep(attempt+1)


def api(base, **params):
    return json.loads(get(base + '?' + urlencode(params)))


class Tags(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


def norm(text):
    text = unicodedata.normalize('NFKD', html.unescape(text)).casefold()
    if re.search(r'[\u3040-\u30ff\u3400-\u9fff]', text):
        return re.sub(r'\s+', '', text)
    return '|'.join(sorted(re.findall(r'[a-z0-9]+', text)))


def plain(text):
    return html.unescape(re.sub('<[^>]+>', '', text)).strip()


def record(e, *, page, image, name, evidence, kind, identity, title=None):
    e.update(source_page=page, image_url=image, source_name=name,
             evidence=evidence, source_kind=kind, source_identity=identity,
             identity_verified=True, visual_reviewed=False)
    if title:
        e['display_name'] = title
    e.pop('research_error', None)


def bootstrap():
    works = {}
    for line in (ROOT/'AGENTS.md').read_text().splitlines():
        m = re.match(r'\| ([a-z][a-z0-9-]+) \| (.+?) \|', line)
        if m:
            works[m[1]] = m[2]
    works.update({'amairo-islenauts':'天色＊アイルノーツ / Amairo Islenauts',
                  'ave-mujica':'BanG Dream! Ave Mujica',
                  'majono-yoru-en':'魔女的夜宴 / Sanoba Witch',
                  'sanoba-witch':'魔女的夜宴 / Sanoba Witch',
                  'senren-banka':'千恋＊万花 / Senren＊Banka',
                  'parquet':'PARQUET', 'zero-no-tsukaima':'零之使魔 / The Familiar of Zero'})
    entries = {}
    for key, directory in inventory(ROOT).items():
        work, slug = key.split('/')
        name = slug.removesuffix('-perspective').replace('-', ' ').title()
        p = directory/'SKILL.md'
        if p.exists():
            s = p.read_text()
            h = re.search(r'^# (.+)$', s, re.M)
            if h and not h[1].startswith(('SKILL', '「')) and '-perspective' not in h[1]:
                name = re.split(r'\s+[·—]|操作系统|角色扮演|角色操作| パースペクティブ| - ', h[1])[0].strip()
                name = re.sub(r'[（(].*', '', name).strip()
        entries[key] = {'display_name':name, 'path':image_path(key),
                        'identity_verified':False, 'visual_reviewed':False}
    manifest = {'version':1, 'works':{w:works.get(w,w) for w in sorted({k.split('/')[0] for k in entries})},
                'characters':entries, 'duplicate_exceptions':[]}
    write_json(ROOT/MANIFEST, manifest)


def touhou(manifest):
    overrides = {'ebisu-eika':'戎璎花','himemushi-momoyo':'姬虫百百世','tenkajin-chiyari':'天火人血枪',
                 'mitsugashira-enoko':'三头慧之子','kumoi-ichirin':'云居一轮','onozuka-komachi':'小野塚小町',
                 'shikieiki-yamaxanadu':'四季映姬','ringoo':'铃瑚','saigyouji-yuyuko':'西行寺幽幽子',
                 'ushizaki-urumi':'牛崎润美','kurokoma-saki':'骊驹早鬼','joutouguu-mayumi':'杖刀偶磨弓',
                 'haniyasushin-keiki':'埴安神袿姬','kicchou-yachie':'吉吊八千慧'}
    def one(item):
        key, entry = item
        slug = key.split('/')[1].removesuffix('-perspective')
        name = overrides.get(slug, entry['display_name'])
        data = api('https://thwiki.cc/api.php', action='parse', page=name, prop='text', format='json', redirects=1)
        if 'error' in data:
            raise ValueError(str(data['error']))
        parsed = data['parse']; title = parsed['title']; text = parsed['text']['*']
        # The character page's leading named official-art thumbnail, not a logo
        # or a random image returned by a search API.
        candidates = [a for t,a in Tags(text).tags if t=='img'
                      and unquote(a.get('src','')).rsplit('/',1)[-1].split('px-',1)[-1].startswith(title+'（')
                      and a.get('src','').startswith('https://upload.thbwiki.cc/')]
        if not candidates:
            raise ValueError('No named character illustration thumbnail')
        img = candidates[0]
        # Resolve the named file, not a tiny character-table thumbnail.
        image = re.sub(r'/\d+px-[^/]+$', '', img['src']).replace('/thumb/', '/')
        record(entry, page='https://thwiki.cc/'+title, image=img['src'], name=title,
               evidence=f"THBWiki character article {title}; named official illustration: {unquote(image).rsplit('/',1)[-1]}",
               kind='reference-site-official-art', identity='thbwiki:'+str(parsed['pageid']))
        entry['image_url']=image
        return entry
    collect(manifest, 'touhou-project', one)


def wuwa(manifest):
    def one(item):
        key, entry = item
        slug=key.split('/')[1].removesuffix('-perspective')
        name={'jinshi':'Jinhsi','shorekeeper':'Shorekeeper'}.get(slug,slug.title())
        data=api('https://wutheringwaves.fandom.com/api.php',action='parse',page=name,prop='text',format='json',redirects=1)
        p=data.get('parse',{})
        if norm(p.get('title',''))!=norm(name):
            raise ValueError('Resonator page not found or different identity: '+str(data.get('error',p.get('title'))))
        tags=Tags(p['text']['*']).tags
        imgs=[a for t,a in tags if t=='img' and 'pi-image-thumbnail' in a.get('class','')]
        imgs=[a for a in imgs if a.get('data-image-name','').casefold().startswith(name.casefold().removeprefix('the '))]
        if not imgs:
            raise ValueError('No named resonator infobox portrait')
        img=next((a for a in imgs if a.get('alt')=='Card'),imgs[0])
        record(entry,page='https://wutheringwaves.fandom.com/wiki/'+name.replace(' ','_'),
               image=img['src'],name=name,evidence=f"Resonator page title {p['title']}; infobox image {img.get('data-image-name')}",
               kind='reference-site-official-art',identity='wuwa:'+str(p['pageid']))
        return entry
    collect(manifest,'wuthering-waves',one)


def collect(manifest, work, fn):
    items=[(k,e.copy()) for k,e in manifest['characters'].items() if k.split('/')[0]==work and not e.get('identity_verified')]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures={pool.submit(fn,item):item[0] for item in items}
        for future in as_completed(futures):
            key=futures[future]
            try:
                manifest['characters'][key]=future.result();print('SOURCE',key,'OK',flush=True)
            except Exception as exc:
                manifest['characters'][key]['research_error']=str(exc);print('PENDING',key,str(exc)[:180],flush=True)
            write_json(ROOT/MANIFEST,manifest)


MAL_WORKS = {
    'angel-beats':[(6547,'Angel Beats')], 'ave-mujica':[(54959,'MyGO')],
    'bocchi-the-rock':[(47917,'Bocchi')], 'charlotte':[(28999,'Charlotte')],
    'danganronpa':[(16592,'Danganronpa')], 'engage-kiss':[(51417,'Engage Kiss')],
    'fate':[(356,'Fate/stay night')], 'fate-grand-order':[(38084,'Fate/Grand Order')],
    'fate-stay-night':[(356,'Fate/stay night')], 'konosuba':[(30831,'Kono Subarashii')],
    'kyokou-suiri':[(39017,'Kyokou Suiri')], 'madoka':[(9756,'Mahou Shoujo Madoka')],
    'majo-no-tabitabi':[(40571,'Majo no Tabitabi')], 'mushoku-tensei':[(39535,'Mushoku Tensei')],
    'mygo':[(54959,'MyGO')], 'neon-genesis-evangelion':[(30,'Evangelion')],
    'otonari-no-tenshi-sama':[(50739,'Otonari no Tenshi')],
    'overlord':[(29803,'Overlord'),(35073,'Overlord II'),(37675,'Overlord III'),(48895,'Overlord IV')],
    'rokudenashi-majutsu-koushi':[(32951,'Rokudenashi')], 'seraph-of-the-end':[(26243,'Owari no Seraph')],
    'steins-gate':[(9253,'Steins;Gate')],
    'sword-art-online':[(11757,'Sword Art Online'),(21881,'Sword Art Online II'),
                        (36474,'Sword Art Online'),(39597,'Sword Art Online'),(31765,'Sword Art Online')],
    'tensei-shitara-slime-datta-ken':[(37430,'Tensei shitara Slime')],
    'toaru-project':[(4654,'Toaru Majutsu'),(8937,'Toaru Majutsu'),(16049,'Toaru Kagaku'),(36432,'Toaru Majutsu')],
    'toradora':[(4224,'Toradora')], 'zero-no-tsukaima':[(1195,'Zero no Tsukaima')],
    'kage-no-jitsuryokusha':[(48316,'Kage no Jitsuryokusha'),(54595,'Kage no Jitsuryokusha')],
    'idolmaster':[(10278,'iDOLM@STER')],
}
ALIASES={
 'kaname-rana':['Raana Kaname','Rana Kaname'], 'kisaragi':['Kisara'],
 'artoria-pendragon':['Saber','Artoria Pendragon'], 'mash-kyrielight':['Mash Kyrielight','Mashu Kyrielight'],
 'hitori-gotoh':['Hitori Gotou'], 'pa-san':['PA-san'], 'misumi-uika':['Uika Misumi'],
 'sharon-holygrail':['Sharon Holy Grail','Sharon Holygrail'],
 'hatsune-miku':['Miku Hatsune'], 'mami':['Mami Tomoe'], 'kyubey':['Kyuubey'],
 'asuka-langley-soryu':['Asuka Langley Souryuu','Asuka Langley Soryu'],
 'ainz-ooal-gown':['Momonga','Ainz Ooal Gown'], 'zesshi-zetsumei':['Zesshi Zetsumei','Antilene Heran Fouche'],
 'renner-theiere-chardelon-ryle-vaiself':['Renner Theiere Chardelon Ryle Vaiself'],
 'riel-rayford':['Riel Rayford','Re=L Rayford'], 'celica-arfonia':['Celica Arfonia'],
 'rumia-tingel':['Rumia Tingel'], 'sistine-fibel':['Sistine Fibel'],
 'andrew-gilbert-mills':['Andrew Gilbert Mills','Agil'], 'argo':['Argo'],
 'asada-shino':['Shino Asada','Sinon'], 'alice-synthesis-thirty':['Alice Zuberg','Alice Synthesis Thirty'],
 'bercouli-synthesis-one':['Bercouli Synthesis One'], 'eiji-nogata':['Eiji Nochizawa','Eiji'],
 'kirigaya-kazuto':['Kazuto Kirigaya','Kirito'], 'kirigaya-suguha':['Suguha Kirigaya','Leafa'],
 'lizbeth-rika-shinozaki':['Rika Shinozaki','Lisbeth'], 'renly-synthesis-twenty-seven':['Renly Synthesis Twenty-seven'],
 'sheyta-synthesis-twelve':['Sheyta Synthesis Twelve'], 'silica-keiko-ayano':['Keiko Ayano','Silica'],
 'tsuboi-ryoutarou':['Ryoutarou Tsuboi','Klein'], 'yuuki':['Yuuki Konno'],
 'heaven-canceller':['Heaven Canceler','Heaven Canceller'], 'frenda':['Frenda Seivelun'],
 'awaki-musujime':['Awaki Musujime'], 'acqua-of-the-back':['Acqua of the Back'],
 'fiamma-of-the-right':['Fiamma of the Right'], 'terra-of-the-left':['Terra of the Left'],
 'vento-of-the-front':['Vento of the Front'], 'index':['Index Librorum Prohibitorum','Index'],
 'kamijou-touma':['Touma Kamijou'], 'komoe-tsukuyomi':['Komoe Tsukuyomi'],
 'mary':['Mary'], 'annerose-notoire':['Annerose Nichtsehen','Annerose Notoire'],
 'louise':['Louise Françoise Le Blanc de La Vallière','Louise de La Vallière'],
 'takagi-producer':['Producer'], 'otonashi-kotori':['Kotori Otonashi'],
 'yutenji-nyamu':['Nyamu Yuutenji'], 'ryo-yamada':['Ryou Yamada'],
 'kyoko-kirigiri':['Kyouko Kirigiri'],'ogata-shu':['Shuu Ogata'],'yugiri-ayano':['Ayano Yuugiri'],
 'rin-tohsaka':['Rin Toosaka'],'kyoko-sakura':['Kyouko Sakura'],'gendo-ikari':['Gendou Ikari'],
 'sheyta-synthesis-twelve':['Scheta Synthesis Twelve'],
 'acqua-of-the-back':['William Orwell'],'fiamma-of-the-right':['Uho no Fiamma'],
 'terra-of-the-left':['Sahou no Terra'],'vento-of-the-front':['Zenpou no Vento'],
}


def mal_roster(anime_id, expected):
    url=f'https://myanimelist.net/anime/{anime_id}/_/characters'
    text=get(url)
    titles=[a.get('content','') for t,a in Tags(text).tags if t=='meta' and a.get('property')=='og:title']
    title=' '.join(titles)
    if expected.casefold() not in title.casefold():
        raise ValueError(f'Anime identity mismatch: {anime_id}: {title!r}, expected {expected!r}')
    rows={}
    for link,body in re.findall(r'<a\b[^>]*href="(https://myanimelist.net/character/[^"?#]+)"[^>]*>(.*?)</a>',text,re.S):
        row=rows.setdefault(link,{'url':link,'work_page':url,'work_title':title})
        imgs=[a for t,a in Tags(body).tags if t=='img']
        if imgs:
            img=imgs[0];src=img.get('data-src',img.get('src',''))
            if '/images/characters/' in src:
                row['image']=re.sub(r'/r/\d+x\d+','',src).split('?')[0]
                row['name']=img.get('alt','')
        elif plain(body):
            row['name']=plain(body)
    return [v for v in rows.values() if v.get('name') and v.get('image')]


def mal(manifest):
    for work, sources in MAL_WORKS.items():
        if not any(k.startswith(work+'/') and not e.get('identity_verified') for k,e in manifest['characters'].items()):
            continue
        rows={}
        for anime_id,expected in sources:
            try:
                for row in mal_roster(anime_id,expected):rows[row['url']]=row
            except Exception as exc:
                print('ROSTER ERROR',work,anime_id,str(exc),flush=True)
        for key,e in manifest['characters'].items():
            if not key.startswith(work+'/') or e.get('identity_verified'):continue
            slug=key.split('/')[1].removesuffix('-perspective')
            aliases=ALIASES.get(slug,[])+[slug.replace('-',' ')]
            wanted={norm(n) for n in aliases}
            matches=[r for r in rows.values() if norm(r['name']) in wanted or norm(r['url'].rsplit('/',1)[1].replace('_',' ')) in wanted]
            if len(matches)==1:
                r=matches[0]
                record(e,page=r['url'],image=r['image'],name=r['name'],
                       evidence=f"Exact alias {aliases}; character {r['name']} listed in {r['work_title']} at {r['work_page']}",
                       kind='character-database',identity='mal:'+r['url'].split('/')[4])
                print('SOURCE',key,r['name'],flush=True)
            else:
                e['research_error']=f'Exact work-qualified aliases found {len(matches)} matches'
                print('PENDING',key,e['research_error'],flush=True)
        write_json(ROOT/MANIFEST,manifest)


VN_WORKS = {
 'amairo-islenauts':['v12167'], 'dracu-riot':['v8213'], 'noble-works':['v4806'],
 'otome-riron':['v12246','v10680'], 'tsuki-ni-yorisou-otome-no-sahou':['v10680'],
 'riddle-joker':['v22230'], 'sakura-no-uta':['v562'], 'sakura-no-toki':['v20431'],
 'sanoba-witch':['v16044'], 'majono-yoru-en':['v16044'], 'senren-banka':['v19073'],
 'cafe-stella':['v26414'], 'parquet':['v31807'], 'tenshi-souzou-re-boot':['v40520'],
}
VN_NAMES = {
 'airi':'Shiraga Airi','masaki':'Masaki Gaillard','shirley':'Shirley Warwick',
 'yune':'Amagiri Yuune','hinomiya-konoka':'Hinomiya Konoka','tia-hohenwerfen':'Tia Hohenwerfen',
 'azusa':'Mera Azusa','elina':'Elina Olegovna Oven','miu':'Yarai Miu','rio':'Inamura Rio',
 'nicola-cepheus':'Nicola Kephalos', 'akari':'Kanemoto Akari','hinata':'Kunihiro Hinata',
 'maya':'Nagamitsu Maya','sena':'Tsukiyama Sena','shizuru':'Masamune Shizuru',
 'meguru':'Inaba Meguru','touko':'Togakushi Touko','tsumugi':'Shiiba Tsumugi','wakana':'Kariya Wakana',
 'sakurai-nene':'Ayachi Nene','koharu':'Kurama Koharu','lena':'Lena Liechtenauer',
 'mako':'Hitachi Mako','murasame':'Murasame','roka':'Maniwa Roka','yoshino':'Tomotake Yoshino',
 'ayase':'Mitsukasa Ayase','chisaki':'Mibu Chisaki','hazuki':'Nijouin Hazuki',
 'mayu':'Shikibe Mayu','nanami':'Arihara Nanami',
 'kokura-asahi':'Kokura Asahi','ookura-aeon':'Ookura Ion','ookura-resona':'Ookura Risona','ookura-yusei':'Ookura Yuusei',
 'sakurakouji-runa':'Sakurakouji Luna','hibikawa-ruriwo':'Hikawa Ruriwo',
 'ozato-fumika':'Oozato Fumika','takatate-orie':'Takatate Orie','hoshikawa-kaguya':'Hoshikawa Kaguya',
}


def vndb(manifest):
    for work, ids in VN_WORKS.items():
        rows={}
        for vid in ids:
            payload={'filters':['vn','=', ['id','=',vid]],'fields':'name,original,aliases,image.url,vns.title,vns.id','results':100}
            data=json.loads(get('https://api.vndb.org/kana/character',payload))
            if data.get('more'):
                raise ValueError('VNDB roster requires pagination')
            for r in data['results']:rows[r['id']]=r
        for key,e in manifest['characters'].items():
            if not key.startswith(work+'/') or e.get('identity_verified'):continue
            slug=key.split('/')[1].removesuffix('-perspective')
            aliases=[slug.replace('-',' '), e['display_name']]+([VN_NAMES[slug]] if slug in VN_NAMES else [])
            wanted={norm(a) for a in aliases}
            matches=[r for r in rows.values() if any(norm(x or '') in wanted for x in [r['name'],r.get('original')]+r.get('aliases',[]))]
            if len(matches)==1 and matches[0].get('image'):
                r=matches[0]
                record(e,page='https://vndb.org/'+r['id'],image=r['image']['url'],name=r['name'],
                       evidence=f"VNDB exact name/alias {r['name']} ({r.get('original')}); visual novel membership {r['vns']}",
                       kind='character-database',identity='vndb:'+r['id'])
                print('SOURCE',key,r['name'],flush=True)
            else:
                e['research_error']=f'VNDB exact role/novel match count {len(matches)}'
                print('PENDING',key,e['research_error'],flush=True)
        write_json(ROOT/MANIFEST,manifest)


IDOL_NAMES={
 'arima-rinse':'杜野凛世','higuchi-enoka':'樋口円香','izumi-mei':'和泉愛依','osaki-anna':'大崎甘奈',
 'sakamori-kaori':'桜守歌織','satou-shizuku':'佐藤心','shinozaki-hiro':'篠澤広','shirose-sakuya':'白瀬咲耶',
 'tokoro-emi':'所恵美','tsukioka-kanade':'月岡恋鐘','yatsumiya-meguru':'八宮めぐる',
 'akagi-miria':'赤城みりあ','ichihara-nina':'市原仁奈','koga-koharu':'古賀小春',
 'ryuzaki-kaoru':'龍崎薫','sakurai-momoka':'櫻井桃華','sasaki-chie':'佐々木千枝',
 'tachibana-arisu':'橘ありす','yuki-haru':'結城晴','yusa-kozue':'遊佐こずえ',
 'ookami-tamaki':'大神環',
}


def idol(manifest):
    data=api('https://idollist.idolmaster-official.jp/api/search',keyword='',order_type=1,order_direction=1)
    rows=data['character_list']
    for key,e in manifest['characters'].items():
        if not key.startswith('idolmaster/') or e.get('identity_verified'):continue
        slug=key.split('/')[1].removesuffix('-perspective')
        aliases=[slug.replace('-',' '),e['display_name']]+([IDOL_NAMES[slug]] if slug in IDOL_NAMES else [])
        wanted={norm(a) for a in aliases}
        matches=[r for r in rows if norm(r['name']) in wanted or norm(r['identification_label'].replace('_',' ')) in wanted]
        if len(matches)==1:
            r=matches[0];label=r['identification_label']
            record(e,page=f"https://idollist.idolmaster-official.jp/search/detail/{r['character_id']}",
                   image=f'https://idollist.idolmaster-official.jp/images/character_thumbnail/{label}_thumb.jpg',
                   name=r['name'],evidence=f"Official idol directory exact name {r['name']}, label {label}, brand {r['brand_id']}",
                   kind='official',identity='idolmaster:'+str(r['character_id']),title=r['name'].replace(' ',''))
            print('SOURCE',key,r['name'],flush=True)
        else:
            print('PENDING',key,'official idol-directory matches',len(matches),flush=True)
    write_json(ROOT/MANIFEST,manifest)


def special(manifest):
    """Individually resolved aliases / official pages, not generic fallbacks."""
    def bind(key,page,image,name,evidence,kind='official',identity=None):
        e=manifest['characters'][key]
        record(e,page=page,image=image,name=name,evidence=evidence,kind=kind,
               identity=identity or page)
        print('SOURCE',key,name,flush=True)
        write_json(ROOT/MANIFEST,manifest)
    key='vocaloid/hatsune-miku-perspective'
    if not manifest['characters'][key]['identity_verified']:
        page='https://piapro.net/intl/en_character.html';text=get(page)
        section=text.split('<section id="ch_miku"',1)[1].split('</section>',1)[0]
        imgs=[a for t,a in Tags(section).tags if t=='img' and a.get('src')=='images/ch_img_miku.png']
        if len(imgs)!=1 or 'HATSUNE MIKU' not in section:raise ValueError('Official Miku section mismatch')
        bind(key,page,urljoin(page,imgs[0]['src']),'Hatsune Miku',
             'Crypton Piapro official character page, ch_miku section, ch_img_miku.png')
    key='idolmaster/nanakusa-hazuki-perspective'
    if not manifest['characters'][key]['identity_verified']:
        page='https://shinycolors-anime.idolmaster-official.jp/character/';text=get(page)
        blocks=re.findall(r'<li\b[^>]*class="chara__list-item"[^>]*>(.*?)</li>',text,re.S)
        blocks=[b for b in blocks if '七草 はづき' in b]
        if len(blocks)!=1:raise ValueError('Hazuki official named card mismatch')
        img=next(a for t,a in Tags(blocks[0]).tags if t=='img' and '/hazuki/' in a.get('src',''))
        bind(key,page,urljoin(page,img['src']),'七草はづき','Official Shiny Colors anime character roster: named 七草 はづき card and hazuki thumbnail')
    key='star-detective-precure/luluka-perspective'
    if not manifest['characters'][key]['identity_verified']:
        page='https://www.toei-anim.co.jp/tv/precure/character/arcana_shadow.php';text=get(page)
        tags=Tags(text).tags;meta={a.get('property'):a.get('content') for t,a in tags if t=='meta'}
        if '森亜るるか' not in meta.get('og:title',''):raise ValueError('Official Precure page is a different character')
        bind(key,page,meta['og:image'],'森亜るるか / Cure Arcana Shadow',
             'Toei official character page og:title names 森亜るるか; og:image is her character illustration')
        manifest['characters'][key]['display_name']='露露卡'
    key='the-noexistencen-of-you-and-me/lilith-perspective'
    if not manifest['characters'][key]['identity_verified']:
        payload={'filters':['vn','=', ['id','=','v49859']],'fields':'name,original,aliases,image.url,vns.title,vns.id','results':100}
        rs=json.loads(get('https://api.vndb.org/kana/character',payload))['results']
        r=next(r for r in rs if r['id']=='c148903' and r['name']=='Lilith')
        bind(key,'https://vndb.org/c148903',r['image']['url'],'Lilith',
             'VNDB Lilith c148903 explicitly appears in original visual novel v49859 (Bu/cunzai de Ni, he Wo); not a similarly named character',
             'character-database','vndb:c148903')
    for key,domain,page_title,expected_title,image_key in [
      ('touhou-project/koakuma-perspective','touhou','Koakuma','Koakuma','SCoOW6Koakuma.jpg'),
      ('sword-art-online/argo-perspective','swordartonline','Argo','Hosaka Carina Tomo','Argo.png'),
      ('rokudenashi-majutsu-koushi/eve-ignite-perspective','rokuaka','Eve Ignite','Eve Ignite','Character Manga-Eve.png'),
    ]:
        if manifest['characters'][key]['identity_verified']:continue
        base=f'https://{domain}.fandom.com'
        p=api(base+'/api.php',action='parse',page=page_title,prop='text',format='json',redirects=1)['parse']
        if p['title']!=expected_title:raise ValueError('Unexpected wiki identity: '+p['title'])
        imgs=[a for t,a in Tags(p['text']['*']).tags if t=='img' and a.get('data-image-name')==image_key]
        if not imgs:raise ValueError('Named infobox image not found: '+image_key)
        bind(key,base+'/wiki/'+expected_title.replace(' ','_'),imgs[0]['src'],expected_title,
             f"Named character article {expected_title}, exact infobox image {image_key}; requested name {page_title}",
             'reference-site-official-art',domain+':'+str(p['pageid']))
    write_json(ROOT/MANIFEST,manifest)


def refine(manifest):
    # Visual inspection rejected landscape idol event cards: their identity is
    # documented, but the subject is too small or shares the image with others.
    # Prefer the explicit character portrait, keeping the official record as
    # corroboration instead of treating a busy official card as an avatar.
    ids=[(10278,'iDOLM@STER'),(42385,'Million Live'),(23587,'Cinderella Girls'),
         (51536,'U149'),(54758,'Shiny Colors'),(58302,'Shiny Colors'),(60045,'Shiny Colors'),
         (34257,'Cinderella Girls'),(37422,'Cinderella Girls'),(41299,'Cinderella Girls')]
    rows={}
    for pair in ids:
        try:
            for r in mal_roster(*pair):rows[r['url']]=r
        except Exception as exc:print('ROSTER ERROR',pair,str(exc),flush=True)
    for key,e in manifest['characters'].items():
        if not key.startswith('idolmaster/') or '/character_thumbnail/' not in e.get('image_url',''):continue
        slug=key.split('/')[1].removesuffix('-perspective')
        label=e['image_url'].rsplit('/',1)[1].removesuffix('_thumb.jpg').replace('_',' ')
        aliases=[label,slug.replace('-',' ')]
        extra={'akizuki-ryo':['Ryou Akizuki'],'emily-stewart':['Emily'],
               'mizutani-eri':['Eri Mizutani'],'satou-shizuku':['Shin Satou'],
               'shijou-takane':['Takane Shijou'],'hojo-karen':['Karen Houjou'],
               'asakura-toru':['Tooru Asakura'],'nikaido-chizuru':['Chizuru Nikaidou'],
               'ookami-tamaki':['Tamaki Oogami'],'ryuzaki-kaoru':['Kaoru Ryuuzaki'],
               'tenkubashi-tomoka':['Tomoka Tenkuubashi'],'toyokawa-fuka':['Fuuka Toyokawa']}
        aliases+=extra.get(slug,[])
        wanted={norm(n) for n in aliases}
        matches=[r for r in rows.values() if norm(r['name']) in wanted or norm(r['url'].rsplit('/',1)[1].replace('_',' ')) in wanted]
        if len(matches)!=1:
            print('IDOL PORTRAIT PENDING',key,aliases,len(matches),flush=True);continue
        r=matches[0]
        e['official_identity_reference']={'page':e['source_page'],'name':e['source_name'],
                                         'reason':'Official directory confirms identity; landscape event card rejected in visual review as an avatar'}
        record(e,page=r['url'],image=r['image'],name=r['name'],kind='character-database',
               identity='mal:'+r['url'].split('/')[4],
               evidence=f"Exact official/local aliases {aliases}; {r['name']} appears in {r['work_title']} at {r['work_page']}; dedicated character portrait")
        e.pop('sha256',None);e.pop('source_sha256',None)
        print('REFINED',key,r['name'],flush=True)
    for slug,name,filename in [('alice-margatroid','爱丽丝·玛格特罗伊德','爱丽丝（人妖名鉴）.jpg'),
                                ('kumoi-ichirin','云居一轮','云居一轮（心绮楼立绘）.png')]:
        key='touhou-project/'+slug+'-perspective';e=manifest['characters'][key]
        p=api('https://thwiki.cc/api.php',action='parse',page=name,prop='text',format='json',redirects=1)['parse']
        imgs=[a for t,a in Tags(p['text']['*']).tags if t=='img' and unquote(a.get('src','')).rsplit('/',1)[-1].split('px-',1)[-1]==filename]
        if not imgs:raise ValueError('Specified official illustration missing: '+filename)
        url=re.sub(r'/\d+px-[^/]+$','',imgs[0]['src']).replace('/thumb/','/')
        if e.get('image_url') != url:
            record(e,page='https://thwiki.cc/'+name,image=url,name=name,
                   evidence=f'Character article {name}; explicitly selected official individual illustration {filename}; replaces tiny result-screen/group composition',
                   kind='reference-site-official-art',identity='thbwiki:'+str(p['pageid']))
            e.pop('sha256',None);e.pop('source_sha256',None)
    e=manifest['characters']['star-detective-precure/luluka-perspective']
    if not e.get('trim_transparent_padding'):
        e['trim_transparent_padding']=True;e.pop('sha256',None)
    e=manifest['characters']['touhou-project/kumoi-ichirin-perspective']
    e['trim_white_padding']=True
    key='idolmaster/shinozaki-hiro-perspective';e=manifest['characters'][key]
    page='https://gakuen.idolmaster-official.jp/idol/hiro/';text=get(page)
    meta={a.get('property'):a.get('content') for t,a in Tags(text).tags if t=='meta'}
    if '篠澤 広' not in meta.get('og:title',''):raise ValueError('Hiro official page identity mismatch')
    # Named individual standing illustration, not the landscape social card.
    imgs=[a for t,a in Tags(text).tags if t=='img' and '/hiro/' in a.get('src','')]
    selected=[a for a in imgs if a['src']=='../../assets/img/idol/hiro/default.png']
    if selected and e.get('image_url') != urljoin(page,selected[0]['src']):
        record(e,page=page,image=urljoin(page,selected[0]['src']),name='篠澤広',
               evidence='Official Gakuen Idolmaster 篠澤 広 profile; named individual illustration '+selected[0]['src'],
               kind='official',identity='gakuen:hiro')
        e.pop('sha256',None);e.pop('source_sha256',None)
        print('REFINED',key,selected[0]['src'],flush=True)
    elif not selected:
        print('HIRO IMAGE CANDIDATES',imgs,flush=True)
    key='idolmaster/shiragiku-hotaru-perspective';e=manifest['characters'][key]
    if '/character_thumbnail/' in e['image_url']:
        # This minor character has no roster entry in the selected anime pages.
        # The exact character URL was separately resolved and inspected.
        page='https://myanimelist.net/character/160914/Hotaru_Shiragiku';text=get(page)
        tags=Tags(text).tags;meta={a.get('property'):a.get('content') for t,a in tags if t=='meta'}
        portraits=[a for t,a in tags if t=='img' and a.get('alt')=='Hotaru Shiragiku'
                   and 'portrait-' in a.get('class','')]
        if meta.get('og:title')!='Hotaru Shiragiku' or 'Cinderella Girls' not in text or len(portraits)!=1:
            raise ValueError('Hotaru name/franchise/portrait association mismatch')
        e['official_identity_reference']={'page':e['source_page'],'name':e['source_name'],
                                         'reason':'Official landscape event card replaced with a dedicated named portrait'}
        record(e,page=page,image=portraits[0]['data-src'],name='Hotaru Shiragiku',
               evidence='Exact character profile Hotaru Shiragiku; Cinderella Girls association; named portrait-225x350 image',
               kind='character-database',identity='mal:160914')
        e.pop('sha256',None);e.pop('source_sha256',None)
    write_json(ROOT/MANIFEST,manifest)


if __name__=='__main__':
    if sys.argv[1]=='bootstrap':
        bootstrap()
    else:
        m=read_json(ROOT/MANIFEST)
        {'touhou':touhou,'wuwa':wuwa,'mal':mal,'vndb':vndb,'idol':idol,'special':special,'refine':refine}[sys.argv[1]](m)
