# 角色 preview 修复验证报告

- 47 个作品、444 个角色，头像覆盖与身份/视觉核验均为 444/444。
- 249 个缺失头像补齐，现有错图/占位图已核验替换，4 组已知错误复用均已拆开。
- 5 组同一人物的历史归档/化名复用保留，已在来源清单及索引说明。
- 两份索引各 444 张图片全部加载，444 个角色目录链接返回 HTTP 200，配对错误为 0。
- 53 页图册已逐项检查，21 项单元测试通过；全部角色 Skill/research 的内容哈希保持不变。
- 当前离线检查退出 0，原文件基线检查退出 1；完整二进制补丁已在临时副本实际应用并通过检查。
- 回滚脚本已在临时副本实际执行，450 个图片/索引路径恢复原始状态，无关文件保留。工作区仍保留修复结果。

## 可复现验证

```bash
python scripts/portraits.py check
python -m unittest discover -s tests -v
python scripts/verify_portraits.py
```

- 原样命令、输出及退出状态：[commands.json](commands.json)
- 汇总验证：[verification.json](verification.json)
- 图片差异及全部新增维护工具：[repair.patch](repair.patch)
- 核验图册：[review/index.html](review/index.html)
- 浏览器预览截图：[browser-mygo.png](browser-mygo.png)
- 回滚：`python scripts/rollback_portraits.py`（只恢复本次图片/索引；保留新增工具和验证记录，检查后续人工修改）
