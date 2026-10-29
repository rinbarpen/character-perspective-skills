# 角色头像维护

角色身份使用 `作品目录/角色目录` 完整键；同名、短名和罗马音近似不是自动匹配依据。

- 目录清单：`characters/<work>/<character>-perspective/`，包括仅有 research 的历史目录。
- 图片映射：`assets/portrait_mapping.json`，保持“作品 → 完整角色目录名列表”结构。
- 身份与来源：`assets/portrait_sources.json`，记录来源页、图片地址、原始/本地 SHA-256、身份依据、视觉复核状态。
- 官方图片优先；资料站图片须有明确的角色、作品关联。图片版权属于各自权利人；来源页不等于开放许可。
- 下载仅接受已确认身份的显式 URL；失败最多重试三次，不回退到搜索首图，不覆盖原有文件。
- 统一为 240 × 320 WebP 画布，等比例缩放、留白、不裁切或生成角色内容；个别原图按清单标记移除外围透明/纯白留白。

## 命令

```bash
python -m pip install -r scripts/requirements-portraits.txt
python scripts/portraits.py audit
python scripts/portraits.py fetch --work mygo
python scripts/portraits.py contact-sheets
# 对照来源逐项检查图册后，再填写对应的 visual_reviewed 和 review_note。
python scripts/portraits.py render
python scripts/portraits.py check --report artifacts/portrait-repair/verification.json
python -m unittest discover -s tests -v
python scripts/verify_portraits.py
```

`check` 是离线检查；身份、视觉复核、完整覆盖、损坏图片、哈希、跨角色重复、双索引和角色资料基线有任一问题即返回非零状态。
角色来源收集适配器在 `scripts/research_portraits.py`；它们只建立身份依据，始终保留单独的视觉复核步骤。
`verify_portraits.py` 还会重建原始基线、实际应用二进制补丁、在临时副本执行回滚，并记录命令、原样输出和退出状态。
`bootstrap` 仅用于首次建立清单，会重建来源记录，已有清单请直接修改具体条目。

## 回滚

本次原文件与哈希保存在 `artifacts/portrait-repair/baseline/`。
运行 `python scripts/rollback_portraits.py` 恢复变更清单中记录的图片与索引；新增维护工具及验证记录保留。
回滚前会检查当前文件仍与交付版本一致，避免覆盖后续人工修改；测试可用 `--root <临时副本>`。
