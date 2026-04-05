# Branch vs Main 分析（2026-04-01）

## 结论

当前 `feat/reference-omni-csx` 相对 `origin/main` 的变更规模已经达到“两个项目并行”的量级：

- 变更统计：`601 files changed, 47527 insertions(+), 4 deletions(-)`
- 其中大头来自历史 Omni-CSX 代码树（现已归档为 `reference/omni-csx-v35`）

因此本分支必须保持**隔离交付**，不能直接把全量历史代码流入 `main`。

## 量化证据（按目录）

`git diff --name-only $(git merge-base HEAD origin/main)..HEAD` 统计：

- `multiplatform_mock_openapi_zh/apps`：244
- `multiplatform_mock_openapi_zh/packages`：82
- `multiplatform_mock_openapi_zh/tests`：62
- `multiplatform_mock_openapi_zh/infra`：47
- `apps/domain-service`：47
- `multiplatform_mock_openapi_zh/.ai`：46
- `multiplatform_mock_openapi_zh/providers`：34

说明：历史仓库体量明显大于中台主线变更，必须以 `reference/*` 方式归档，不进入主运行路径。

## 本仓库建议边界

- 主线运行区（可进入 `main`）：
  - `apps/core/*`
  - `apps/sim/*`
  - `apps/frontend/*`
  - `providers/*`
  - `docs/*`（架构与运行文档）
- 参考归档区（不进入主运行链路）：
  - `reference/*`

## 防污染策略

1. 只提交“中台主线可运行”所需文件到主线 PR。
2. `reference/*` 只作为文档/映射参考，不作为 CI 默认测试目标。
3. 保留旧路径软链作为过渡兼容，但新代码一律使用 canonical 路径。
4. 合并采用分批 PR：
   - PR-A：目录重组与兼容软链
   - PR-B：链路修复（仿真契约、Odoo 聚合）
   - PR-C：文档与治理规则

## 当前状态

已完成：目录 canonical 化、reference 归档、关键路径兼容。

待持续：将历史路径引用逐步清理为 canonical 路径，压缩“非主线”变更噪音。
