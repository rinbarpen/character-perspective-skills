# Roles 项目管理规范

> 本文件定义了 roles 目录下角色 Skill 的管理规则

---

## 目录结构

```
roles/
├── [作品英文名]/
│   └── [角色名]-perspective/
│       ├── SKILL.md
│       └── references/
│           └── research/
│               ├── 01-writings.md      # 官方设定
│               ├── 02-conversations.md  # 台词对话
│               ├── 03-expression-dna.md  # 说话风格
│               ├── 04-external-views.md  # 他者评价
│               ├── 05-decisions.md  # 关键行为
│               └── 06-timeline.md  # 时间线
```

---

## 命名规范

### 作品目录名

使用作品的英文标识符（与动画/游戏标题统一）：

| 作品 | 目录名 |
|------|--------|
| 名侦探光之美少女 | star-detective-precure |
| 偶像梦幻乐团 | ave-mujica |
| MyGO!!!!! | my-go |
| 宿命回响 | senren-banka |
| 东方Project | touhou-project |
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
   mkdir -p roles/[作品名]/[角色名]-perspective/references/research
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

## 作品目录映射

| 目录名 | 作品 |
|--------|------|
| amairo-islenauts | 青色魔法少女 |
| ave-mujica | 偶像梦幻乐团 |
| charlotte | Charlotte |
| dracu-riot | 德古拉之怒 |
| fate | FATE |
| fate-grand-order | FGO |
| fate-stay-night | FS/N |
| konosuba | 为美好的世界献上祝福 |
| madoka | 魔法少女小圆 |
| majono-yoru-en | 无职转生 |
| my-go | MyGO!!!!! |
| noble-works | NOBLE WORKS |
| overlord | Overlord |
| riddle-joker | 谜之屋 |
| sanoba-witch | 圣痕炼金术师 |
| senren-banka | 宿命回响 |
| seraph-of-the-end | 终结的炽天使 |
| star-detective-precure | 名侦探光之美少女 |
| steins-gate | 命运石之门 |
| touhou-project | 东方Project |
| tsuki-ni-yorisou | 月依 |
| vocaloid | 初音未来 |

---

## 注意事项

- **虚拟角色 vs 真实人物**：虚拟角色没有真实思维可提炼，只能做角色扮演Skill
- **信息不完整**：动画新番播出中时，在诚实边界中标注信息截止日期
- **触发词**：在 SKILL.md 的 description 中添加触发词，便于激活

---

> 本规范由 [女娲 · Skill造人术](https://github.com/alchaincyf/nuwa-skill) 生成