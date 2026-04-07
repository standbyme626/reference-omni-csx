# 中台（domain-service）全面重构方案

> 基于对 domain-service 的全面代码审计。当前中台已"改不动"，需要彻底重写。
> 原则：按职责分层，消除 Dict[str, Any]，统一 DI 和错误处理，每个服务单一职责。

---

## 整体进度

- [x] Phase 0: 推送代码到新仓库
- [x] Phase 1: 新建目标目录结构 + Models 层 ✅ 2026-04-05
- [x] Phase 2: 适配器层重构（Protocol + 单一直达）✅ 2026-04-05
- [x] Phase 3: Service 层重写（拆分 God Class，单一职责）✅ 2026-04-05
- [x] Phase 4: API 路由层重写（极简 + 统一 DI + 错误处理）✅ 2026-04-05
- [x] Phase 5: 消除重复逻辑 ✅ 2026-04-05
- [x] Phase 6: 修复测试基础设施 + 补充测试 ✅ 2026-04-07 (pytest.ini pythonpath + 129 tests passing)
- [x] Phase 7: 杂项修复 + 清理旧代码 ✅ 2026-04-07 (删除 platform_adapters/, business_context_service.py)
- [x] Phase 8: 收尾迁移 ✅ 2026-04-07 (ContextResolver 替换 BusinessContextService)

---

## Phase 0: 推送代码到新仓库

> 状态：未开始

```bash
git remote add new-origin https://github.com/standbyme626/reference-omni-csx.git
git add -A
git commit -m "checkpoint: pre-refactoring state"
git push new-origin feat/reference-omni-csx
```

---

## Phase 1: 新目录结构 + Models 层

> 状态：未开始

### 1.1 目标目录结构

```
apps/core/domain-service/
├── app/
│   ├── models/                    # Pure Pydantic data models
│   │   ├── __init__.py
│   │   ├── order.py
│   │   ├── shipment.py
│   │   ├── after_sale.py
│   │   ├── conversation.py
│   │   ├── customer.py
│   │   └── context.py
│   │
│   ├── adapters/                  # Platform adapters — Protocol + implementation
│   │   ├── __init__.py
│   │   ├── protocol.py            # OrderAdapter, ShipmentAdapter, etc (Protocol)
│   │   ├── taobao.py
│   │   ├── douyin.py
│   │   ├── jd.py
│   │   ├── xhs.py
│   │   ├── kuaishou.py
│   │   ├── wecom_kf.py
│   │   └── registry.py
│   │
│   ├── services/                  # Domain services — single responsibility
│   │   ├── __init__.py
│   │   ├── order_service.py       # Only order queries
│   │   ├── shipment_service.py    # Only shipment queries
│   │   ├── after_sale_service.py  # Only after-sale queries
│   │   ├── conversation_service.py # Only conversation management
│   │   ├── context_resolver.py    # Only context aggregation
│   │   ├── reply_generator.py     # Only reply/action suggestions
│   │   ├── risk_evaluator.py      # Only risk assessment
│   │   ├── push_events.py         # Push event handling
│   │   ├── analytics.py           # Analytics
│   │   ├── operations.py          # Risk flags, audit logs, followup tasks
│   │   └── platform_gateway.py    # Platform dispatch
│   │
│   ├── api/                       # Routing — params + call service + return
│   │   ├── __init__.py
│   │   ├── deps.py                # Unified FastAPI DI
│   │   ├── errors.py              # Unified exception handler
│   │   ├── router.py              # Route mounting
│   │   └── routes/
│   │       ├── health.py
│   │       ├── orders.py
│   │       ├── shipments.py
│   │       ├── after_sales.py
│   │       ├── conversations.py
│   │       ├── context.py
│   │       ├── recommendations.py
│   │       ├── quality.py
│   │       ├── risk.py
│   │       ├── integration.py
│   │       ├── analytics.py
│   │       ├── operations.py
│   │       ├── push_events.py
│   │       ├── ai_suggestion.py
│   │       ├── customers.py
│   │       ├── kb.py
│   │       └── management.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   └── response.py
│   │
│   ├── schemas/                   # Request/response Pydantic schemas
│   │   ├── __init__.py
│   │   ├── order.py
│   │   ├── shipment.py
│   │   ├── context.py
│   │   └── recommendation.py
│   │
│   └── main.py
│
├── models/                        # Legacy (kept for backward compat during migration)
│   └── unified.py
│
├── adapters/                      # Legacy (kept for backward compat during migration)
│   └── platform_adapter.py
│
└── tests/
    ├── conftest.py
    ├── test_api.py
    └── ...
```

### 1.2 Models 层设计 — 纯 Pydantic，告别 Dict[str, Any]

- [x] **设计文档完成**
- [x] `Order` model
- [x] `Shipment` model
- [x] `AfterSale` model
- [x] `Conversation` / `Message` model
- [x] `Context` model (聚合快照)
- [x] `Customer` / `CustomerTag` model (新增)
- [n/a] `ContextSnapshot` — deleted as empty stub

### 涉及文件
- 新建：`app/models/*.py`（6 个文件）
- 新建：`app/schemas/*.py`（API 请求/响应 schema）

### 验证
- `app/models/` 能独立 import，无循环依赖
- 每个 model 有 docstring + example

---

## Phase 2: 适配器层重构

> 状态：未开始

### 2.1 消除双重适配器间接层

- [ ] **删除** `app/adapters/platform_adapters.py`（包裹层，每方法只有一行委派）
- [ ] **删除** `adapters/platform_adapter.py`（遗留路径）
- [ ] 将现有静态方法类改写为实例方法，直接放在 `app/adapters/taobao.py` 等

### 2.2 拆分 BaseAdapter 为 Protocol

- [ ] **新建** `app/adapters/protocol.py`
  ```python
  class OrderAdapter(Protocol):
      def to_unified_order(self, platform_data: dict) -> Order: ...

  class ShipmentAdapter(Protocol):
      def to_unified_shipment(self, platform_data: dict) -> Shipment: ...

  class AfterSaleAdapter(Protocol):
      def to_unified_after_sale(self, platform_data: dict) -> AfterSale: ...

  class ConversationAdapter(Protocol):
      def to_unified_conversation(self, platform_data: dict) -> Conversation: ...
      def to_unified_messages(self, platform_data: dict, limit: int = 100) -> list[Message]: ...
  ```
- [ ] 京东只实现 `OrderAdapter` + `ShipmentAdapter` + `AfterSaleAdapter`
- [ ] WeCom kf 只实现 `ConversationAdapter`
- [ ] 淘宝、抖音、小红书、快手实现完整 4 个

### 2.3 统一 Registry

- [ ] **重写** `app/adapters/registry.py`
  - 按 platform → {order, shipment, after_sale, conversation} 字典注册
  - `has_order_adapter(platform)`, `has_conversation_adapter(platform)` 等查询方法
  - `get_order_adapter(platform) -> OrderAdapter` 等获取方法
  - 删除 class-level mutable dict，改用函数注册

### 涉及文件

| 操作 | 文件 |
|------|------|
| 删除 | `app/adapters/platform_adapters.py` |
| 删除 | `adapters/platform_adapter.py`（遗留） |
| 新建 | `app/adapters/protocol.py` |
| 新建 | `app/adapters/taobao.py` |
| 新建 | `app/adapters/douyin.py` |
| 新建 | `app/adapters/jd.py` |
| 新建 | `app/adapters/xhs.py` |
| 新建 | `app/adapters/kuaishou.py` |
| 新建 | `app/adapters/wecom_kf.py` |
| 重写 | `app/adapters/registry.py` |
| 更新 | `app/services/order_service.py` — import 路径 |

### 验证
- `pytest` 全通过
- `python -m app.main` 能启动
- 无 `NotImplementedError` 残留

---

## Phase 3: Service 层重写

> 状态：未开始

### 3.1 OrderService (< 150 行)

- [ ] **新建** `app/services/order_service.py`
  - `get_order(platform, order_id, official_run_id?) -> Order`
  - `get_order_with_user(platform, order_id) -> dict`
  - `batch_get_orders(requests) -> list[Order]`
  - `get_order_timeline(platform, order_id) -> list[dict]`
  - 委托 adapter 做 raw → Order 转换
  - 删除 `_raw_to_response`（105 行 if-elif 地狱），平台映射逻辑移至各自 adapter

### 3.2 ShipmentService (< 80 行)

- [ ] **新建** `app/services/shipment_service.py`
  - `get_shipment(platform, order_id, official_run_id?) -> Shipment`
  - `batch_get_shipments(requests) -> list[Shipment]`
  - 委托 adapter

### 3.3 AfterSaleService (< 80 行)

- [ ] **新建** `app/services/after_sale_service.py`
  - `get_after_sale(platform, after_sale_id, official_run_id?) -> AfterSale`
  - `get_after_sale_by_order(platform, order_id, official_run_id?) -> AfterSale`
  - 委托 adapter

### 3.4 ConversationService (< 200 行)

- [ ] **新建** `app/services/conversation_service.py`
  - 将模块级 helper 函数合并为内部方法
  - `get_conversation(platform, conversation_id) -> Conversation`
  - `get_conversation_messages(platform, conversation_id, limit) -> list[Message]`
  - `search_conversations(platform, query, skip, limit) -> dict`
  - `resolve_business_reference(platform, biz_id) -> dict`
  - fixture 加载作为内部 helper，不暴露

### 3.5 ContextResolver (< 200 行) ← 从 BusinessContextService 拆解

原 BusinessContextService 636 行，拆为：

- [ ] **新建** `app/services/context_resolver.py`
  - `resolve(platform, biz_id, biz_type, options, official_run_id?) -> Context`
  - `build_order_context(platform, order_id, options, official_run_id?) -> Context`
  - `build_conversation_context(platform, conversation_id, options, official_run_id?) -> Context`
  - `build_after_sale_context(platform, after_sale_id, options, official_run_id?) -> Context`
  - 只负责：调用各 service 拿快照 + 组装 Context

### 3.6 RiskEvaluator (< 100 行) ← 从 BusinessContextService 拆解

- [ ] **新建** `app/services/risk_evaluator.py`
  - `evaluate(context: Context) -> RiskFlags`
  - 规则：after_sale → medium, exceptions → high/critical, refunding → high

### 3.7 ReplyGenerator (< 150 行) ← 合并两处重复逻辑

- [ ] **新建** `app/services/reply_generator.py`
  - `generate_replies(context: Context) -> list[ReplyCandidate]`
  - `generate_actions(context: Context) -> list[ActionCandidate]`
  - 替代 `RecommendationService._generate_replies()` + `BusinessContextService._generate_reply_candidates()` 两处重复

### 3.8 PushEventsService (< 100 行) ← 从 BusinessContextService 拆解

- [ ] **新建** `app/services/push_events.py`
  - `get_push_events(official_run_id) -> list[PushEvent]`
  - `apply_push_state(context: Context, events: list[PushEvent]) -> Context`

### 3.9 OperationsService (< 100 行) ← 从 operations.py route 迁移

- [ ] **新建** `app/services/operations.py`
  - 将 route 层的 CRUD 操作（risk_flag, audit_log, followup_task）移到这里
  - 加线程锁保护
  - 提取 `next_id()` 工具函数

### 涉及文件（新建/重写）

| 文件 | 目标行数 |
|------|---------|
| `app/services/order_service.py` | < 150 |
| `app/services/shipment_service.py` | < 80 |
| `app/services/after_sale_service.py` | < 80 |
| `app/services/conversation_service.py` | < 200 |
| `app/services/context_resolver.py` | < 200 |
| `app/services/risk_evaluator.py` | < 100 |
| `app/services/reply_generator.py` | < 150 |
| `app/services/push_events.py` | < 100 |
| `app/services/operations.py` | < 100 |
| `app/services/platform_gateway.py` | < 80 |
| `app/services/analytics.py` | < 120 |

### 验证
- 所有 API endpoint 返回与重构前相同 JSON 结构
- 每个 service 文件 < 200 行
- 无 Dict[str, Any] 在 service 间传递，全部用 Pydantic model

---

## Phase 4: API 路由层重写

> 状态：未开始

### 4.1 统一依赖注入

- [ ] **重写** `app/api/deps.py`
  ```python
  @lru_cache()
  def get_order_service() -> OrderService: ...

  @lru_cache()
  def get_shipment_service() -> ShipmentService: ...

  @lru_cache()
  def get_after_sale_service() -> AfterSaleService: ...

  @lru_cache()
  def get_conversation_service() -> ConversationService: ...

  @lru_cache()
  def get_context_resolver() -> ContextResolver: ...
  ...
  ```
  - 所有 get_xxx_service() 都带 `@lru_cache()`
  - DI 图：ContextResolver → OrderService → PlatformGateway → Registry

### 4.2 统一错误处理

- [ ] **新建** `app/api/errors.py`
  ```python
  class ServiceError(Exception): ...
  class NotFoundError(ServiceError): ...

  def handle_service_errors(exc: ServiceError, request: Request) -> JSONResponse:
      ...
  ```
  - 注册到 FastAPI 的 `app.add_exception_handler(ServiceError, handle_service_errors)`
  - Route 层不再写 try/except

### 4.3 Route 文件 — 极简模式

每个 route 文件 < 30 行，只做：参数 + 调 service + 返回

- [ ] **重写** `app/api/routes/orders.py` (< 25 行)
- [ ] **重写** `app/api/routes/shipments.py` (< 25 行)
- [ ] **重写** `app/api/routes/after_sales.py` (< 25 行)
- [ ] **重写** `app/api/routes/conversations.py` (< 30 行)
- [ ] **重写** `app/api/routes/context.py` (< 20 行)
- [ ] **重写** `app/api/routes/recommendations.py` (< 20 行)
- [ ] **重写** `app/api/routes/quality.py` (< 20 行)
- [ ] **重写** `app/api/routes/risk.py` (< 20 行)
- [ ] **重写** `app/api/routes/operations.py` (< 30 行)
- [ ] **重写** `app/api/routes/push_events.py` (< 15 行)
- [ ] **重写** `app/api/routes/ai_suggestion.py` (< 15 行)
- [ ] **重写** `app/api/routes/analytics.py` (< 20 行)
- [ ] **重写** `app/api/routes/customers.py` (< 15 行)
- [ ] **重写** `app/api/routes/kb.py` (< 15 行)
- [ ] **重写** `app/api/routes/management.py` (< 15 行)

### 4.4 Router

- [ ] **重写** `app/api/router.py`
  - 删除重复的 `/healthz`，只保留 health.py 中的
  - 统一 prefix 定义

### 4.5 main.py

- [ ] **重写** `app/main.py`
  - 删除内联 `/healthz` 和 `/` 端点
  - CORS origins 从 settings 读取
  - 注册统一错误处理器
  - 只负责：app 创建 + middleware + router + exception handlers

### 验证
- 所有 15 个 route group 的 API 路径和响应格式不变
- `curl localhost:8000/healthz` 正常
- 每个 route 文件 < 35 行

---

## Phase 5: 消除重复逻辑

> 状态：未开始

### 5.1 Reply/Action 去重

- [ ] 从 `RecommendationService` 和旧 `BusinessContextService` 提取公共逻辑到 `ReplyGenerator`
- [ ] 删除旧的 `_generate_replies` / `_generate_reply_candidates` / `_generate_actions` / `_generate_action_candidates` 方法

### 5.2 operations 迁移

- [ ] 将 `operations.py` route 中的所有 in-memory CRUD 移到 `OperationsService`
- [ ] 消除 3 处 `max(..., default=0) + 1` 重复为 `next_id()` 函数
- [ ] 加线程锁

### 验证
- 推荐 API 返回相同格式
- Operations CRUD 正常工作

---

## Phase 6: 修复测试

> 状态：未开始

### 6.1 修复 conftest.py

- [ ] 删除 `sys.path` / `sys.modules` 操作
- [ ] 在 `pytest.ini` 配置 `pythonpath = apps/core/domain-service`
- [ ] 确保 import 路径正确（`from app.xxx`）

### 6.2 补充缺失测试

- [ ] `tests/test_operations.py` — 覆盖 14 个端点
- [ ] `tests/test_push_events.py` — 覆盖 2 个端点
- [ ] `tests/test_ai_suggestion.py` — 覆盖 1 个端点
- [ ] `tests/test_analytics.py` — 覆盖 4 个端点

### 6.3 增强现有测试

- [ ] `test_api.py` — 不仅检查 status_code，验证响应内容
- [ ] `test_registry.py` — 验证具体适配器注册和能力

### 验证
- `pytest` 100% 通过
- 所有新 endpoint 有测试覆盖

---

## Phase 7: 杂项修复

> 状态：未开始

- [ ] 6A: 删除 main.py 中重复的 `/healthz`
- [ ] 6B: CORS origins 从 settings 读取
- [ ] 6C: operations.py Optional[str] 类型标注
- [ ] 6D: AnalyticsService.get_platforms_coverage 从 Registry 动态获取
- [ ] 6E: user-sim-service/pyproject.toml 和 setup.py 改名为 platform-sim
- [ ] 删除遗留的 `adapters/` 和 `models/` 根目录文件（确认无引用后）
- [ ] 删除旧的 `*.py` 文件（order_domain_service.py, business_context_service.py, etc.）

---

## 依赖关系图

```
Phase 0 (推送)
  │
  ▼
Phase 1 (Models + 目录结构)
  │
  ▼
Phase 2 (Adapters: Protocol + Registry)
  │
  ▼
Phase 3 (Services: 拆 God Class, 去 Dict[str, Any])
  │
  ▼
Phase 4 (API Routes: 极简 + 统一 DI + 错误处理)
  │
  ├─→ Phase 5 (去重) ←─────────── 可与 Phase 4 并行
  │
  ├─→ Phase 6 (测试) ←─────────── 可与 Phase 4-5 并行
  │
  └─→ Phase 7 (杂项 + 清理旧文件)
```

---

## 关键原则

1. **Model 优先** — 所有 domain 对象都是 Pydantic model，不再 dict 传递
2. **单一职责** — 每个 service 只做一件事，每文件 < 200 行
3. **Protocol 适配** — 平台只实现自己支持的接口，不 raise NotImplementedError
4. **统一错误** — Route 层不写 try/except，统一异常处理器
5. **统一 DI** — 所有 service 通过 deps.py + FastAPI Depends() 注入
6. **API 兼容** — 响应 JSON 格式不变，前端无感知
