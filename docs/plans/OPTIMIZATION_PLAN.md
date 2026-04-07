# 架构优化计划 (Phase 9-14)

> 基于项目结构分析后的系统性修复计划。按优先级排序，每个 Phase 独立执行和提交。

---

## 背景

重构完成后，项目存在以下遗留问题：

| 问题类型 | 数量 | 严重度 |
|----------|------|--------|
| 超长文件 (>200行) | 6 | 🔴 高 |
| 重复/废弃代码 | 3 | 🟡 中 |
| 测试覆盖缺失 | 3 个路由组 | 🟡 中 |
| 硬编码配置 | 1 | 🟢 低 |

---

## 执行计划总览

| Phase | 任务 | 文件数 | 优先级 | 预期结果 |
|-------|------|--------|--------|----------|
| **Phase 9** | 拆分 `operations.py` 路由 | 4 | 🔴 高 | 291行 → 3x80行 |
| **Phase 10** | 拆分 `official_sim_provider.py` | 4 | 🔴 高 | 1058行 → 模块化 |
| **Phase 11** | 合并重复代码 + CORS | 4 | 🟡 中 | 删除 2 个废弃文件 |
| **Phase 12** | 补充测试覆盖 | 3 | 🟡 中 | 3 个新测试文件 |
| **Phase 13** | 拆分 `conversation_service.py` | 3 | 🟢 低 | 391行 → 模块化 |
| **Phase 14** | 清理 `compat_data.py` | 1 | 🟢 低 | 删除或重构 |

---

## Phase 9: 拆分 operations.py 路由

### 9.1 目标

将 `api/routes/operations.py` (291 行) 拆分为三个独立路由文件。

### 9.2 当前状态

```python
# operations.py 混合了：
- risk_flag CRUD     # 风险标记
- audit_log CRUD     # 审计日志
- followup_task CRUD # 跟进任务
```

### 9.3 拆分方案

```
api/routes/operations.py (291行)
    ↓
api/routes/risk_flags.py      (~80行)   # risk_flag CRUD
api/routes/audit_logs.py      (~80行)   # audit_log CRUD  
api/routes/followup_tasks.py  (~80行)   # followup_task CRUD
```

### 9.4 路由变更

| 原路由 | 新路由 |
|--------|--------|
| `POST /api/operations/risk-flags` | `POST /api/risk-flags` |
| `GET /api/operations/risk-flags` | `GET /api/risk-flags` |
| `GET /api/operations/risk-flags/{id}` | `GET /api/risk-flags/{id}` |
| `PUT /api/operations/risk-flags/{id}` | `PUT /api/risk-flags/{id}` |
| `DELETE /api/operations/risk-flags/{id}` | `DELETE /api/risk-flags/{id}` |
| `POST /api/operations/audit-logs` | `POST /api/audit-logs` |
| `GET /api/operations/audit-logs` | `GET /api/audit-logs` |
| ... | ... |

> **注意**：需要更新 `router.py` 引入新路由，并保持向后兼容（可选：旧路由重定向到新路由）

### 9.5 验证

- [ ] 所有 14 个端点测试通过
- [ ] 旧路由仍可访问（或有明确废弃提示）
- [ ] 单元测试覆盖每个新文件

### 9.6 提交信息

```
Phase 9: split operations.py route into risk_flags, audit_logs, followup_tasks

- Split 291-line operations.py into 3 route files
- Add new route registrations in router.py
- All 14 endpoints functional
```

---

## Phase 10: 拆分 official_sim_provider.py

### 10.1 目标

将 `app/services/official_sim_provider.py` (1058 行) 移入 providers/ 目录并模块化。

### 10.2 当前状态

```
app/services/official_sim_provider.py (1058 行)
├── OfficialSimProxyProvider 类          # 主类
├── OfficialSimNotFoundError              # 自定义错误
├── _normalize_xxx() 方法                  # 多个平台规范化方法
└── _request_json()                       # HTTP 客户端
```

### 10.3 拆分方案

```
providers/official_sim/
├── __init__.py
├── provider.py          # OfficialSimProxyProvider 主类 (~300行)
├── errors.py            # OfficialSimNotFoundError 等 (~50行)
├── client.py            # HTTP 请求逻辑 (~200行)
├── platform_mapper.py  # 平台特定规范化 (~300行)
└── protocol.py          # 定义 Provider Protocol
```

### 10.4 import 变更

```python
# 旧
from app.services.official_sim_provider import OfficialSimProxyProvider

# 新
from providers.official_sim import OfficialSimProxyProvider
```

### 10.5 验证

- [ ] domain-service 正常启动
- [ ] 调用 official-sim-server 的功能正常
- [ ] 测试通过

### 10.6 提交信息

```
Phase 10: extract official_sim_provider to providers/official_sim/

- Move service to providers/ directory
- Split into modular components (provider, client, errors, mapper)
- Update all imports across domain-service
```

---

## Phase 11: 合并重复代码

### 11.1 目标

删除废弃文件，统一配置管理。

### 11.2 问题清单

| 问题 | 文件 | 解决方案 |
|------|------|----------|
| 重复依赖注入 | `app/core/deps.py` (空) + `app/dependencies.py` (在用) | 删除 `core/deps.py` |
| 重复错误定义 | `app/core/errors.py` + `app/api/errors.py` | 保留 `api/errors.py`，删除 `core/errors.py` |
| CORS 硬编码 | `app/main.py` | 移到 `config.py` 的 `cors_origins` |

### 11.3 执行步骤

#### 11.3.1 删除废弃 deps.py

```bash
# 确认无引用
grep -r "app.core.deps" apps/core/domain-service/

# 删除
rm apps/core/domain-service/app/core/deps.py
```

#### 11.3.2 删除废弃 errors.py

```bash
# 确认无引用
grep -r "app.core.errors" apps/core/domain-service/

# 删除
rm apps/core/domain-service/app/core/errors.py
```

#### 11.3.3 CORS 配置化

```python
# app/core/config.py
class Settings(BaseSettings):
    # ... existing fields
    cors_origins: list[str] = [
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 11.4 验证

- [ ] domain-service 正常启动
- [ ] CORS 头正确返回配置值

### 11.5 提交信息

```
Phase 11: consolidate duplicate code and externalize CORS config

- Remove redundant app/core/deps.py
- Remove redundant app/core/errors.py
- Move CORS origins to settings config
```

---

## Phase 12: 补充测试覆盖

### 12.1 目标

为缺失测试的路由组创建独立测试文件。

### 12.2 新增文件清单

| 文件 | 覆盖内容 | 路由数 |
|------|----------|--------|
| `tests/test_operations.py` | risk_flag, audit_log, followup_task CRUD | 14 |
| `tests/test_analytics.py` | orders_summary, conversations_summary, platforms_coverage | 3 |
| `tests/test_ai_suggestion.py` | /api/ai/suggestion 端点 | 1 |

### 12.3 test_operations.py 结构

```python
class TestRiskFlags:
    def test_create_risk_flag(self): ...
    def test_list_risk_flags(self): ...
    def test_get_risk_flag(self): ...
    def test_update_risk_flag(self): ...
    def test_delete_risk_flag(self): ...

class TestAuditLogs:
    def test_create_audit_log(self): ...
    # ...

class TestFollowupTasks:
    def test_create_followup_task(self): ...
    # ...
```

### 12.4 验证

- [ ] 每个新测试文件 > 5 个测试用例
- [ ] pytest 通过

### 12.5 提交信息

```
Phase 12: add test coverage for operations, analytics, ai_suggestion

- Add tests/test_operations.py (14 endpoints)
- Add tests/test_analytics.py (3 endpoints)
- Add tests/test_ai_suggestion.py (1 endpoint)
```

---

## Phase 13: 拆分 conversation_service.py

### 13.1 目标

将 `app/services/conversation_service.py` (391 行) 模块化。

### 13.2 当前状态

```python
# conversation_service.py 混合了：
- fixture 加载逻辑
- 搜索逻辑 (search_conversations)
- 业务引用解析 (resolve_business_reference)
- 会话管理 (get_conversation, get_messages)
```

### 13.3 拆分方案

```
services/conversation_service.py (391行)
    ↓
services/conversation_service.py  # 核心逻辑 (~180行)
services/conversation_fixtures.py  # fixture 加载 (~100行)
services/conversation_search.py   # 搜索逻辑 (~120行)
```

### 13.4 验证

- [ ] conversations 相关 API 正常
- [ ] 搜索功能正常

### 13.5 提交信息

```
Phase 13: split conversation_service.py into modular components

- Extract fixture loading to conversation_fixtures.py
- Extract search logic to conversation_search.py
- Keep core service with essential methods
```

---

## Phase 14: 清理 compat_data.py

### 14.1 目标

评估 `app/services/compat_data.py` (329 行) 是否仍需要。

### 14.2 检查步骤

```bash
# 检查引用
grep -r "compat_data" apps/core/domain-service/
grep -r "from app.services.compat_data" apps/
```

### 14.3 决策

| 引用情况 | 处理方式 |
|----------|----------|
| 无引用 | 直接删除 |
| 有少量引用 | 迁移到目标 service，删除 |
| 有大量引用 | 评估是否重构 |

### 14.4 验证

- [ ] 删除后无 import 错误

### 14.5 提交信息

```
Phase 14: remove compat_data.py if unused

- Check all imports
- Remove if no references
- Migrate if small number of references
```

---

## 执行顺序

```
Phase 9  ──→ 测试通过 ──→ Phase 10 ──→ 测试通过
  │                              │
  ↓                              ↓
Phase 11 ←───────────────────── Phase 12 ──→ 测试通过
  │                                     │
  ↓                                     ↓
Phase 13 ──→ Phase 14 ──→ 全部完成 ✓
```

---

## 回滚策略

每个 Phase 独立 commit，如有问题可直接：

```bash
git revert <commit_hash>
```

---

## 完成标准

| 指标 | 目标 |
|------|------|
| 最大路由文件 | < 100 行 |
| 最大 service 文件 | < 300 行 |
| 测试覆盖率 | 所有路由有独立测试 |
| 废弃文件 | 0 |
| 硬编码配置 | 0 |
