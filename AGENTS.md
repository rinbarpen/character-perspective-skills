# Roles 项目管理规范

> 本文件定义了 roles 目录下角色 Skill 的管理规则

---

## 目录结构

```
roles/
├── assets/
│   └── portraits/
├── characters/
│   └── [作品英文名]/
│       └── [角色名]-perspective/
│           ├── SKILL.md
│           └── references/
│               └── research/
│                   ├── 01-writings.md      # 官方设定
│                   ├── 02-conversations.md  # 台词对话
│                   ├── 03-expression-dna.md  # 说话风格
│                   ├── 04-external-views.md  # 他者评价
│                   ├── 05-decisions.md  # 关键行为
│                   └── 06-timeline.md  # 时间线
├── skills/
│   └── [工具名]/
│       └── SKILL.md                        # 工具型 Skill
```

---

## 命名规范

### 作品目录名

使用作品的英文标识符（与动画/游戏标题统一）：

| 作品 | 目录名 |
|------|--------|
| 名侦探光之美少女 | star-detective-precure |
| 偶像梦幻乐团 | ave-mujica |
| MyGO!!!!! | mygo |
| 宿命回响 | senren-banka |
| 东方Project | touhou-project |
| 转生史莱姆 / 关于我转生变成史莱姆这档事 | tensei-shitara-slime-datta-ken |
| 无职转生 | majono-yoru-en |
| ... | ... |

### 角色目录名

使用角色的罗马音/英文名 + `-perspective` 后缀：

```
hatsune-miku-perspective/    # 初音未来
takamatsu-tomori-perspective/  # 高松智水
luluka-perspective/         # 露露卡
```

---

## 使用女娲蒸馏时的流程

1. **确认角色和作品**
   - 确认要蒸馏的角色名
   - 确认角色所属的作品
   - 确认聚焦方向（全面画像 vs 某个维度）

2. **创建目录结构**
   ```bash
   mkdir -p characters/[作品名]/[角色名]-perspective/references/research
   ```

3. **运行6个并行Agent调研**
   - 1 著作（角色设定、技能、背景）
   - 2 对话（台词、语气）
   - 3 表达（说话风格、标志性特征）
   - 4 他者（粉丝评价、CP讨论）
   - 5 决策（关键剧情、行为模式）
   - 6 时间线（角色弧光、成长）

4. **构建 SKILL.md**
   - 基于6份调研报告提炼心智模型
   - 构建角色扮演规则
   - 验证质量（已知测试、边缘测试、风格测试）

5. **验证后交付**
   - 放入对应的作品目录
   - 更新 AGENTS.md（如有新作品）

---

## 角色 Skill 结构说明

### SKILL.md 核心字段

| 字段 | 说明 |
|------|------|
| name | Skill 标识（`[角色名]-perspective`） |
| description | 描述，包含来源、心智模型数、触发词 |
| 角色扮演规则 | 绝对禁止的行为边界 |
| 回答工作流 | Agentic Protocol |
| 身份卡 | 角色基础信息 |
| 心智模型 | 3-7个核心思维模式 |
| 决策启发式 | 快速判断规则 |
| 表达DNA | 说话风格特征 |
| 时间线 | 关键事件节点 |
| 价值观与反模式 | 核心价值、绝对不做的事 |
| 智识谱系 | 角色原型、与其他角色的关系 |
| 诚实边界 | 信息不完整时的免责声明 |
| 调研来源 | 各 Agent 的信息来源 |

### references/research/ 文件说明

| 文件 | 内容 | 来源 |
|------|------|------|
| 01-writings.md | 官方设定（百科、官网） | 6个Agent并行调研 |
| 02-conversations.md | 经典台词、对话 | 6个Agent并行调研 |
| 03-expression-dna.md | 说话风格、口癖 | 6个Agent并行调研 |
| 04-external-views.md | 粉丝评价、二创 | 6个Agent并行调研 |
| 05-decisions.md | 关键行为、决策 | 6个Agent并行调研 |
| 06-timeline.md | 时间线、角色弧光 | 6个Agent并行调研 |

---

## 迁移历史

| 日期 | 操作 |
|------|------|
| 2026-04-22 | 创建 AGENTS.md，迁移 skills/ 到按作品分类结构 |
| 2026-04-22 | 添加 luluka-perspective |
| 2026-04-22 | 迁移所有角色到新结构（21个作品，~80个角色） |
| 2026-06-11 | 全量整理：创建 characters/ 目录，所有角色数据移入 characters/；assets/ 保留根目录；清理嵌套 roles/ 遗留目录；更新 AGENTS.md 映射表 |
| 2026-06-19 | 新增 toaru-project（魔法禁书目录系列）：14个角色，含6路Agent调研+SKILL.md |
| 2026-06-20 | 新增 engage-kiss（契约之吻）：4个角色（木更/绪方修/夕桐绫乃/莎朗），含24路Agent调研+4份SKILL.md |
| 2026-06-20 | 新增 toaru-project（魔法禁书目录系列）：追加15个角色（Item团队+暗部+神之右席+其他），累计29角色 |
| 2026-06-20 | 新增 idolmaster（偶像大师系列）：765Pro 13角色（春香/千早/美希/律子/梓/伊织/真/亚美/真美/响/贵音/小鸟/制作人）+ CG本家3角色（卯月/凛/未央），含96路Agent调研+16份SKILL.md |
| 2026-06-20 | 新增 idolmaster（偶像大师系列）：追加18角色——ML 7人（未来/静香/翼/星梨花/紬/歌織/琴葉）、SC 5人（巡/恋鐘/円香/果穂/千雪）、CG 3人（文香/加蓮/楓）、DS 3人（涼/絵理/愛），含108路Agent调研+18份SKILL.md，累计34角色 |
| 2026-06-20 | 新增 idolmaster（偶像大师系列）：追加16角色——ML 7人（杏奈/可奈/志保/百合子/育/恵美/エミリー）、SC 4人（甘奈/甜花/小糸/凛世）、CG 5人（蘭子/美波/菜々/きらり/幸子），含96路Agent调研+16份SKILL.md，累计50角色 |
| 2026-06-21 | 新增 idolmaster（偶像大师系列）：追加40角色——ML 24人（エレナ/美奈子/まつり/茜/紗代子/亜利沙/海美/朋花/歩/ひなた/奈緒/千鶴/このみ/環/風花/美也/のり子/瑞希/可憐/莉緒/昴/麗花/桃子/ジュリア）、SC 14人（咲耶/智代子/樹里/霧子/透/にちか/あさひ/冬優子/愛依/結華/ほたる/美琴/はづき/篠澤広）、CG 2人（志希/佐藤心），含240路Agent调研+40份SKILL.md，累计90角色 |
| 2026-06-21 | 新增 touhou-project（东方Project）：24角色。第一批8个（红美铃/小恶魔/古明地觉/火焰猫燐/灵乌路空/洩矢诹访子/因幡帝/姬海棠果），第二批6个（圣白莲/村纱水蜜/寅丸星/云居一轮/娜兹玲/幽谷响子），第三批10个（丰聪耳神子/物部布都/苏我屠自古/霍青娥/宫古芳香/鬼人正邪/少名针妙丸/宇佐见堇子/哆来咪·苏伊特/摩多罗隐岐奈），含144路Agent调研+24份SKILL.md，累计45角色 |
| 2026-06-20 | 新增 mushoku-tensei（无职转生 / Mushoku Tensei）：3角色——洛琪希/艾莉丝/希露菲，含18路Agent调研+3份SKILL.md，累计177角色 |
| 2026-06-20 | 新增 toradora（龙与虎 / Toradora!）：1角色——逢坂大河，含6路Agent调研+1份SKILL.md，累计178角色 |
| 2026-06-20 | 新增 kage-no-jitsuryokusha（我想成为影之实力者！/ The Eminence in Shadow）：13角色——阿尔法/贝塔/伽玛/德尔塔/艾普西隆/洁塔/希妲/阿蕾克希亚/克莱尔/罗兹/纽/安妮萝洁/玛丽，含78路Agent调研+13份SKILL.md，累计191角色 |
| 2026-06-20 | 新增 rokudenashi-majutsu-koushi（不正经的魔术讲师与禁忌教典 / Akashic Records of Bastard Magic Instructor）：5角色——希丝缇娜·菲伊贝尔/露米娅·汀洁尔/莉艾尔·雷福德/塞莉卡·阿尔佛诺亚/伊芙·伊格尼特，含30路Agent调研+5份SKILL.md，累计196角色 |
| 2026-06-21 | 新增 sanoba-witch（魔女的夜宴 / サノバウィッチ）：追加4角色——因幡めぐる/椎葉紬/戸隠憧子/仮屋和奏，含24路Agent调研+4份SKILL.md |
| 2026-06-21 | 新增 dracu-riot（德古拉之怒）：追加1角色——ニコラ・ケフェウス，含6路Agent调研+1份SKILL.md |
| 2026-06-21 | 新增 amairo-islenauts（青色魔法少女 / 天色＊アイルノーツ）：追加2角色——ティア・ホーエンヴェルフェン/火宮木乃香，含12路Agent调研+2份SKILL.md |
| 2026-06-21 | 新增 cafe-stella（星光咖啡馆与死神之蝶 / 喫茶ステラと死神の蝶）：5角色——明月栞那/四季ナツメ/墨染希/火打谷愛衣/汐山涼音，含30路Agent调研+5份SKILL.md |
| 2026-06-21 | 新增 parquet（PARQUET / パルフェ）：2角色——茨木リノ/城門ツバサ，含12路Agent调研+2份SKILL.md |
| 2026-06-21 | 新增 tenshi-souzou-re-boot（天使☆騒々 RE-BOOT! / 天使☆嚣嚣 RE-BOOT!）：6角色——白雪乃愛/谷風天音/小雲雀来海/星河かぐ耶/高楯オリエ/百里風実花，含36路Agent调研+6份SKILL.md |
| 2026-06-23 | 新增 touhou-project（东方Project）：追加16角色——犬走椛/八云蓝/橙/河城荷取/键山雏/永江衣玖/茨木华扇/四季映姬/小野塚小町/秋静叶/秋穰子/稀神探女/纯狐/赫卡提亚/克劳恩皮丝/本居小铃，含96路Agent调研+16份SKILL.md，累计61角色 |

## 作品目录映射

| 目录名 | 作品 |
|--------|------|
| amairo-islenauts | 青色魔法少女 |
| angel-beats | Angel Beats! |
| cafe-stella | 星光咖啡馆与死神之蝶 / 喫茶ステラと死神の蝶 / Café Stella and the Reaper's Butterflies |
| ave-mujica | 偶像梦幻乐团 |
| bocchi-the-rock | 孤独摇滚！ |
| charlotte | Charlotte |
| dracu-riot | 德古拉之怒 |
| engage-kiss | 契约之吻 / Engage Kiss |
| fate | FATE |
| fate-grand-order | FGO |
| fate-stay-night | FS/N |
| idolmaster | 偶像大师（含765Pro、灰姑娘女孩/U149、Million Live!、Shiny Colors、Dearly Stars、学園アイドルマスター） |
| kage-no-jitsuryokusha | 我想成为影之实力者！ / The Eminence in Shadow / 陰の実力者になりたくて！ |
| kyokou-suiri | 虚构推理 / In/Spectre |
| konosuba | 为美好的世界献上祝福 |
| madoka | 魔法少女小圆 |
| majo-no-tabitabi | 魔女之旅 |
| majono-yoru-en | 魔女的夜宴 / サノバウィッチ (Sanoba Witch) |
| mushoku-tensei | 无职转生 / Mushoku Tensei |
| mygo | MyGO!!!!! |
| neon-genesis-evangelion | 新世纪福音战士 / EVA |
| noble-works | NOBLE WORKS |
| otonari-no-tenshi-sama | 关于邻家的天使大人不知不觉把我惯成了废人这档子事 |
| overlord | Overlord |
| otome-riron | 乙女理論とその周辺 / 月に寄りそう乙女の作法 |
| parquet | PARQUET / パルフェ |
| riddle-joker | 谜之屋 |
| rokudenashi-majutsu-koushi | 不正经的魔术讲师与禁忌教典 / ロクでなし魔術講師と禁忌教典 / Akashic Records of Bastard Magic Instructor |
| sakura-no-toki | 樱之刻 |
| sakura-no-uta | 樱之诗 |
| sanoba-witch | 魔女的夜宴 / サノバウィッチ (Sanoba Witch) |
| senren-banka | 宿命回响 |
| seraph-of-the-end | 终结的炽天使 |
| sword-art-online | Sword Art Online / 刀剑神域 |
| star-detective-precure | 名侦探光之美少女 |
| tenshi-souzou-re-boot | 天使☆騒々 RE-BOOT! / 天使☆嚣嚣 RE-BOOT!（天使骚骚/天使纷扰） |
| steins-gate | 命运石之门 |
| toradora | 龙与虎 / Toradora! |
| tensei-shitara-slime-datta-ken | 转生史莱姆 / 关于我转生变成史莱姆这档事 |
| touhou-project | 东方Project |
| tsuki-ni-yorisou-otome-no-sahou | 月依 |
| toaru-project | 魔法禁书目录（含超电磁炮、科学一方通行） |
| vocaloid | 初音未来 |

---

## 注意事项

- **虚拟角色 vs 真实人物**：虚拟角色没有真实思维可提炼，只能做角色扮演Skill
- **信息不完整**：动画新番播出中时，在诚实边界中标注信息截止日期
- **触发词**：在 SKILL.md 的 description 中添加触发词，便于激活

---

> 本规范由 [女娲 · Skill造人术](https://github.com/alchaincyf/nuwa-skill) 生成
