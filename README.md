# Character Perspective Skills

Archive repository for character-oriented prompt skills gathered from local agent skill trees.

## Overview

- Current archive size: `58` character skills
- Grouping rule: one top-level directory per work slug
- Copy policy: whole skill directories are preserved, including bundled `references/` and `scripts/`
- Registry status: this repository is an archive layout, not yet an auto-discovered skill registry

## Source Priority

The current archive pass was built from the following local sources, in priority order:

1. `.claude/skills`
2. `.opencode/skills`
3. pre-existing copied content from other local skill trees

When the same skill existed in multiple sources, the higher-priority source won.

## Layout

Each skill lives at:

```text
<work-slug>/<skill-name>/
```

Example:

```text
overlord/ainz-ooal-gown-perspective/
touhou-project/flandre-scarlet-perspective/
fate-stay-night/rin-tohsaka-perspective/
```

## Works

| Slug | Work | Skill Count |
| --- | --- | ---: |
| `amairo-islenauts` | `《天色＊アイルノーツ》` | 4 |
| `charlotte` | `《Charlotte》` | 1 |
| `dracu-riot` | `《DRACU-RIOT!》` | 4 |
| `fate` | `《Fate》` | 1 |
| `fate-grand-order` | `《Fate/Grand Order》` | 1 |
| `fate-stay-night` | `《Fate/stay night》` | 5 |
| `konosuba` | `《为美好的世界献上祝福！》` | 1 |
| `majono-yoru-en` | `《魔女的夜宴》` | 4 |
| `noble-works` | `《のーぶる☆わーくす》` | 5 |
| `overlord` | `《Overlord》` | 13 |
| `riddle-joker` | `《RIDDLE JOKER》` | 5 |
| `sanoba-witch` | `《魔女的夜宴 / サノバウィッチ》` | 1 |
| `senren-banka` | `《千恋＊万花》` | 6 |
| `seraph-of-the-end` | `《终结的炽天使》` | 1 |
| `steins-gate` | `《命运石之门》` | 1 |
| `touhou-project` | `《东方Project》` | 4 |
| `tsuki-ni-yorisou-otome-no-sahou` | `《近月少女的礼仪》` | 1 |

## Notes

- Original source directories were intentionally left unchanged.
- This repository currently focuses on preservation and organization, not runtime integration.
