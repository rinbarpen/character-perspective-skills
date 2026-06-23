# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

Character perspective skills repository for the Claude Code ecosystem. Contains prompt-based Skills that enable role-play as specific anime/game characters, plus tool-type skills for character fusion/transformation. These skills are consumed by Claude Code's Skill system (not a standalone application).

## Directory Structure

```
roles/
├── characters/    [work]/[character]-perspective/     # Character role-play skills (167 characters, 33 works)
│   ├── SKILL.md                                        # Core: identity, mental models, expression DNA, behavior rules
│   └── references/research/
│       ├── 01-writings.md           # Official source material
│       ├── 02-conversations.md      # Key dialogues
│       ├── 03-expression-dna.md     # Speech patterns & mannerisms
│       ├── 04-external-views.md     # Fan & critical reception
│       ├── 05-decisions.md          # Key character decisions
│       └── 06-timeline.md           # Character arc timeline
├── skills/        [tool-name]/SKILL.md                 # Tool-type skills (character fusion, transformation)
├── assets/
│   ├── portraits/ [work]/[character].webp              # Character portrait images
│   └── portrait_mapping.json                           # Programmatic work→character mapping
├── AGENTS.md      # Management conventions and directory rules
├── 角色清单.md    # Auto-generated full character inventory
└── README.md      # Character index with portrait links
```

## Character Skill Anatomy

Each character `SKILL.md` contains:
- **Mental Models** — 3-7 core thinking patterns, each with evidence and limitations
- **Expression DNA** — Speech patterns, tone, catchphrases
- **Decision Heuristics** — Fast judgment rules for common situations
- **Role-playing Rules** — Behavioral boundaries and forbidden actions
- **Identity Card** — Name, appearance, attributes
- **Timeline** — Key story events
- **Research Sources** — Tied to the 6 `references/research/` files

## Adding a New Character

Follow the workflow in `AGENTS.md`:

1. Create directory: `characters/[work]/[character]-perspective/references/research/`
2. Run 6 parallel research agents to build the research files
3. Distill mental models from research into `SKILL.md`
4. Add portrait to `assets/portraits/[work]/[character]-perspective.webp`
5. Update `assets/portrait_mapping.json` if it's a new work

## Key Conventions

- **Directory naming**: `kebab-case` for works, `[character-name]-perspective` for characters
- **Character name format**: Romanized/English name, lowercase kebab-case (e.g., `hatsune-miku-perspective`, `homura-akemi-perspective`)
- **Research files**: Always 6 files numbered 01-06, written in Chinese
- **SKILL.md**: May contain both Chinese and English content depending on the character's source material
- **Research depth**: Each research file comes from a dedicated agent run; mental models are extracted from these findings, not fabricated
- **Quality gates**: Known-tests, edge-case tests, and style consistency tests should pass before marking a character complete

## Common Tasks

- **List all characters**: `ls -d characters/*/*-perspective/`
- **Find characters by work**: `ls characters/[work-name]/`
- **Check portrait coverage**: Compare `ls assets/portraits/[work]/` against directory listing in `characters/[work]/`
- **Generate inventory**: Update `角色清单.md` to reflect current character count
- **Validate a SKILL.md**: Ensure all 6 research files exist and SKILL.md references all required fields listed in AGENTS.md
