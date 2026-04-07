# platform-sim 项目结构文档

> 项目是一个"多平台官方行为仿真层 + 客服中台统一层"的开发环境。

---

## 1. 整体目录结构

```
platform-sim/
├── apps/
│   ├── core/
│   │   └── domain-service/          # 中台统一业务层 (port 8000)
│   ├── sim/
│   │   ├── official-sim-server/     # 平台行为仿真器 (port 8001)
│   │   └── user-sim-service/        # 用户行为仿真器 (port 8002)
│   └── frontend/                   # 前端 (预留)
├── providers/                      # 6 平台 provider (mock/official_sim/real)
├── reference/                      # 参考原始系统 (只读)
├── scripts/                        # 工具脚本
├── tests/                          # 集成测试
├── docs/                           # 文档
└── pytest.ini                      # pytest 配置
```

---

## 2. domain-service 详解

### 2.1 目录结构

```
apps/core/domain-service/
├── app/
│   ├── adapters/                   # 平台适配器 (Protocol 模式)
│   │   ├── protocols.py            # 定义 OrderAdapter, ShipmentAdapter 等 Protocol
│   │   ├── registry.py             # 平台注册表 + capabilities
│   │   ├── taobao.py
│   │   ├── jd.py
│   │   ├── douyin.py
│   │   ├── xhs.py
│   │   ├── kuaishou.py
│   │   └── wecom_kf.py
│   │
│   ├── api/
│   │   ├── errors.py               # 统一异常处理
│   │   ├── router.py                # 路由聚合
│   │   └── routes/                  # 15 个路由组
│   │       ├── health.py            (12 行)
│   │       ├── orders.py            (51 行)
│   │       ├── shipments.py         (40 行)
│   │       ├── after_sales.py       (40 行)
│   │       ├── conversations.py     (153 行) ⚠️ 超长
│   │       ├── context.py           (62 行)
│   │       ├── recommendations.py  (154 行) ⚠️ 超长
│   │       ├── quality.py           (56 行)
│   │       ├── risk.py              (56 行)
│   │       ├── operations.py        (291 行) 🔴 严重超长
│   │       ├── analytics.py         (48 行)
│   │       ├── push_events.py       (56 行)
│   │       ├── ai_suggestion.py      (65 行)
│   │       ├── integration.py       (113 行) ⚠️ 超长
│   │       ├── customers.py         (42 行)
│   │       ├── kb.py                (31 行)
│   │       └── management.py        (36 行)
│   │
│   ├── services/                    # 单一职责 Domain Services
│   │   ├── order_service.py         (237 行) ⚠️
│   │   ├── shipment_service.py      (91 行)
│   │   ├── after_sale_service.py    (92 行)
│   │   ├── conversation_service.py  (391 行) ⚠️ 超长
│   │   ├── context_resolver.py       (367 行) ⚠️
│   │   ├── reply_generator.py        (157 行)
│   │   ├── risk_evaluator.py         (95 行)
│   │   ├── recommendation_service.py (72 行)
│   │   ├── push_events_service.py    (64 行)
│   │   ├── operations_service.py     (187 行)
│   │   ├── analytics_service.py      (186 行)
│   │   ├── quality_service.py        (131 行)
│   │   ├── risk_service.py           (109 行)
│   │   ├── integration_service.py    (103 行)
│   │   ├── platform_gateway_service.py (201 行)
│   │   ├── official_sim_provider.py   (1058 行) 🔴 严重超长
│   │   ├── compat_data.py            (329 行) ⚠️ 可能废弃
│   │   ├── push_event_tracker.py     (65 行)
│   │   └── __init__.py
│   │
│   ├── models/                      # Pydantic Unified Models
│   │   ├── unified.py                # 核心统一模型
│   │   ├── order.py
│   │   ├── shipment.py
│   │   ├── after_sale.py
│   │   ├── conversation.py
│   │   ├── context.py
│   │   └── customer.py
│   │
│   ├── schemas/                     # API Request/Response Schemas
│   │   ├── order.py
│   │   ├── shipment.py
│   │   ├── after_sale.py
│   │   ├── conversation.py
│   │   ├── context.py
│   │   └── recommendation.py
│   │
│   ├── core/
│   │   ├── config.py                 # 配置
│   │   ├── deps.py                   # 依赖注入 (已合并到 dependencies.py)
│   │   ├── errors.py                 # 错误定义
│   │   └── response.py               # 统一响应
│   │
│   ├── dependencies.py               # 统一依赖注入
│   └── main.py                       # FastAPI 入口
│
├── tests/                           # 单元测试 (159 tests)
│   ├── test_api.py
│   ├── test_adapters.py
│   ├── test_unified.py
│   ├── test_context_bridge.py
│   ├── test_business_context_odoo.py
│   ├── test_integration_analytics.py
│   ├── test_push_events.py
│   ├── test_registry.py
│   ├── test_registry_gateway.py
│   └── ...
│
└── __init__.py
```

### 2.2 API 路由汇总

| 路由前缀 | 说明 | 路由文件 |
|----------|------|----------|
| `/healthz` | 健康检查 | health.py |
| `/api/orders` | 订单查询 | orders.py |
| `/api/shipments` | 物流跟踪 | shipments.py |
| `/api/after-sales` | 退款/售后 | after_sales.py |
| `/api/conversations` | 会话管理 | conversations.py |
| `/api/context` | 业务上下文 | context.py |
| `/api/recommendations` | AI 推荐 | recommendations.py |
| `/api/quality` | 服务质量 | quality.py |
| `/api/risk` | 风险标记 | risk.py |
| `/api/operations` | 运营管理 | operations.py |
| `/api/analytics` | 业务指标 | analytics.py |
| `/api/push-events` | 推送事件 | push_events.py |
| `/api/ai` | AI 建议 | ai_suggestion.py |
| `/api/integration` | ERP 集成 | integration.py |
| `/api/customers` | 客户资料 | customers.py |
| `/api/kb` | 知识库 | kb.py |
| `/api/management` | 管理接口 | management.py |

---

## 3. official-sim-server 详解

### 3.1 目录结构

```
apps/sim/official-sim-server/
├── app/
│   ├── api/
│   │   ├── router.py
│   │   └── routes/
│   │       ├── runs.py              # simulation runs
│   │       ├── raw_query.py         # raw fixture 查询
│   │       └── mock_compat.py        # 向后兼容
│   │
│   ├── domain/
│   │   ├── scenario_engine.py       # 场景状态机引擎
│   │   ├── artifact_builder.py      # artifact 构建
│   │   ├── push_dispatcher.py       # push 调度
│   │   └── push_notifier.py         # push 通知
│   │
│   ├── platforms/                    # 6 平台 profile
│   │   ├── taobao/profile.py
│   │   ├── jd/profile.py
│   │   ├── douyin_shop/profile.py
│   │   ├── xhs/profile.py
│   │   ├── kuaishou/profile.py
│   │   └── wecom_kf/profile.py
│   │
│   ├── repositories/                 # 数据访问
│   │   ├── run_repo.py
│   │   ├── event_repo.py
│   │   ├── snapshot_repo.py
│   │   ├── push_event_repo.py
│   │   └── artifact_repo.py
│   │
│   ├── models/
│   │   └── models.py                # SQLAlchemy models
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── errors.py
│   │
│   └── main.py
│
├── fixtures/                         # 官方级 payload fixtures
│   ├── taobao/
│   ├── jd/
│   ├── douyin_shop/
│   ├── xhs/
│   ├── kuaishou/
│   └── wecom_kf/
│
├── alembic/                          # 数据库迁移
│   └── versions/
│
└── tests/
    ├── test_runs.py
    ├── test_fixtures.py
    ├── test_artifacts.py
    ├── test_push_notifier.py
    └── ...
```

---

## 4. user-sim-service 详解

### 4.1 目录结构

```
apps/sim/user-sim-service/
├── api/
│   └── routes/
│       └── conversation_studio.py   # 对话工作室 API
│
├── nodes/                            # LangGraph 节点
│   ├── conversation_studio.py
│   ├── user_simulator.py
│   ├── evaluator.py
│   ├── suggestion.py
│   ├── state.py
│   ├── base.py
│   ├── conversation/
│   │   └── context.py
│   └── reply/
│       ├── base.py
│       ├── unified.py
│       └── official_sim.py
│
├── graphs/
│   └── orchestrator.py               # LangGraph 编排
│
├── services/
│   ├── llm_service.py                # LLM 调用
│   ├── llm_config.py                 # LLM 配置
│   ├── domain_service_client.py      # 调用 domain-service
│   └── official_sim_client.py         # 调用 official-sim-server
│
├── prompts/                          # Prompt 模板
├── static/
│   └── conversation_studio.html     # 前端页面
│
├── run_server.py
├── console.py
└── tests/
    ├── test_conversation_studio_chain.py
    ├── test_llm_e2e.py
    └── ...
```

---

## 5. providers 详解

### 5.1 目录结构

```
providers/
├── base/
│   └── provider.py                   # BaseProvider 抽象类
│
├── taobao/
│   └── provider.py
│
├── jd/
│   └── provider.py
│
├── douyin_shop/
│   └── provider.py
│
├── xhs/
│   └── provider.py
│
├── kuaishou/
│   └── provider.py
│
├── wecom_kf/
│   └── provider.py
│
├── odoo/
│   ├── provider.py                   # OdooProvider (主类)
│   ├── mock/
│   │   └── provider.py               # Mock 模式
│   └── real/
│       ├── provider.py               # Real 模式
│       └── link_resolver.py          # 订单链接解析
│
├── utils/
│   ├── fixture_loader.py
│   └── sim_identity.py
│
└── tests/
    ├── test_base_provider.py
    ├── test_p1_providers.py
    └── test_taobao_provider.py
```

### 5.2 Provider 模式

每个 platform provider 支持三种模式：

| 模式 | 说明 | 用途 |
|------|------|------|
| `mock` | 本地 mock 数据 | 开发/测试 |
| `official_sim` | 调用 official-sim-server | 联调 |
| `real` | 调用真实平台 API | 生产 |

---

## 6. 文件统计

| 模块 | Python 文件数 | 总行数 |
|------|--------------|--------|
| domain-service/app | 68 | ~6000 |
| official-sim-server | 35 | ~3500 |
| user-sim-service | 22 | ~2000 |
| providers | 20 | ~2500 |
| scripts | 8 | ~1500 |
| tests | 20 | ~2000 |
| **总计** | **~173** | **~17500** |

---

## 7. 当前问题清单

### 7.1 代码超长 (需要拆分)

| 文件 | 行数 | 建议 |
|------|------|------|
| `operations.py` 路由 | 291 | 拆分为 risk/audit/followup 三个路由文件 |
| `official_sim_provider.py` | 1058 | 拆分到 providers/ 目录 |
| `conversation_service.py` | 391 | 拆分 fixture 加载逻辑 |
| `conversation.py` 路由 | 153 | 拆分为 list/get/messages 三个方法 |
| `recommendations.py` 路由 | 154 | 使用依赖注入替代 Service 实例化 |
| `compat_data.py` | 329 | 确认是否仍需要 |

### 7.2 重复/废弃代码

| 问题 | 文件 | 建议 |
|------|------|------|
| 重复导入 | `core/deps.py` 和 `dependencies.py` | 统一为一个文件 |
| 硬编码 CORS | `main.py` | 移到 settings |
| 废弃文件 | `core/errors.py` 和 `api/errors.py` | 统一为一个 |

### 7.3 测试覆盖

| 路由组 | 测试文件 | 状态 |
|--------|----------|------|
| operations | ❌ 缺失 | 需补充 |
| analytics | ⚠️ 部分 | 需拆分独立文件 |
| ai_suggestion | ❌ 缺失 | 需补充 |
| quality | ⚠️ 在 test_api.py | 需拆分 |
| risk | ⚠️ 在 test_api.py | 需拆分 |

### 7.4 目录结构

| 问题 | 建议 |
|------|------|
| providers/ 在 workspace 根目录 | 考虑移入 domain-service/app/ |
| official_sim_provider.py 在 services/ | 考虑移入 providers/ |

---

## 8. 依赖关系图

```
┌─────────────────────────────────────────────────────────────────┐
│  user-sim-service (port 8002)                                   │
│  nodes → graphs → LLM → domain-service API                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  domain-service (port 8000)                                     │
│  API Routes → Services → PlatformGateway → Registry → Adapters │
│         ↑                                                        │
│         └───────────── providers/ (mock/official_sim/real) ─────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  official-sim-server (port 8001)                                │
│  runs → scenario_engine → fixtures → push_events               │
└─────────────────────────────────────────────────────────────────┘
```
