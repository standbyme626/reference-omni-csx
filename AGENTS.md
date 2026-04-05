# AGENTS.md

## 1. 项目目标

本仓库是一个"多平台官方行为仿真层 + 客服中台统一层"的完整开发环境。

核心价值：**在没有真实官方 API 和真实用户的情况下，仍能完整开发、测试、联调客服中台系统。**

### 1.1 当前架构

```
┌─────────────────────────────────────────────────────────────────┐
│  仿真环境（当前仓库运行时）                                        │
│                                                                  │
│  user-sim-service :8002       official-sim-server :8001          │
│  ┌─────────────────────┐     ┌───────────────────────────┐       │
│  │ ConversationStudio  │────>│ 仿真平台官方行为              │       │
│  │  - 用户意图模拟      │     │  - run 生命周期管理         │       │
│  │  - 消息生成/评估     │     │  - 场景状态机引擎            │       │
│  │  - AI Reply 测试    │<────│  - 事件/推送/artifact       │       │
│  │  - 前端: HTML 页面  │     │  - 错误注入/回放             │       │
│  └─────────┬───────────┘     └───────────────────────────┘       │
│            │                                                       │
│            │ POST /api/recommendations/reply                      │
│            ↓                                                       │
│  ┌─────────────────────────────────────────────────────┐          │
│  │ 中台 domain-service :8000                             │          │
│  │  统一 API: /api/orders, /shipments, /after-sales,    │          │
│  │           /conversations, /context, /recommendations │          │
│  │           /quality, /risk, /analytics, /integration  │          │
│  │  ┌──────────────────────────┐                        │          │
│  │  │  PlatformGatewayService  │                        │          │
│  │  │   ┌───┬────┬───┬─────┐  │                        │          │
│  │  │   │ TB│ DY │ JD│ XHS │  → Providers (mock / sim / real)   │
│  │  │   │   │    │   │ Kua │  → Adapters → Unified models       │
│  │  │   └───┴────┴───┴─────┘  │                              │          │
│  │  └──────────────────────────┘                              │          │
│  └─────────────────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                    ↑ 全程不需要真实用户和真实官方 API

┌─────────────────────────────────────────────────────────────────┐
│  前端（reference/omni-csx-v35，独立开发，最终目标产品）           │
│                                                                  │
│  Agent Console :3001         Admin Console :3002                 │
│  Next.js React               Next.js React                       │
│  坐席工作台                    管理后台                            │
│  - 会话列表/详情               - 质量管理/风险管理                │
│  - AI 推荐面板                - 知识库/培训                      │
│  - 客户资料/跟进/风险标记     - 看板/运营管理                    │
│  - 数据分析/运营               - 平台账号管理/集成管理            │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 两大独立职责

**1. user-sim-service（仿真驱动层）**：
- 模拟用户行为，生成带意图、情感、上下文的自然语言消息
- 调用 domain-service 获取 AI 推荐回复
- 评估回复质量，必要时自动升级到人工
- 前端入口：`user-sim-service/static/conversation_studio.html`

**2. official-sim-server（平台仿真层）**：
- 模拟真实平台官方 API / callback / webhook 的行为
- 基于 fixtures 输出完整的官方级 payload
- 管理仿真 run 的生命周期、状态机、事件记录

### 1.3 核心规则

- LLM 只能用于：计划生成、场景编排、报告生成、测试说明、文档整理、用户意图模拟
- **不能**用 LLM 生成"官方真实 payload"（真相来源只能是 fixtures + state machine）
- 前端最终对接的是 domain-service 的统一 API，不是直接连仿真服务

---

## 2. 当前阶段范围

### 已完成（P0-P1）

- 6 平台 Provider 层（mock / official-sim / real 三种模式）
- Unified 统一数据模型层（Order / Shipment / Refund / Conversation / Message）
- PlatformGatewayService + Adapter Registry + Capabilities
- official-sim-server 仿真引擎（run 生命周期、场景引擎、Artifact、Push、错误注入）
- 3 个平台 profile：taobao, douyin_shop, wecom_kf
- jd, xhs, kuaishou 订单状态 fixtures 就绪
- user-sim-service 对话仿真（双循环：用户意图 + 系统回复评估、转接、错误处理）
- domain-service 统一业务层路由（15 个路由组：health, orders, shipments, after_sales, conversations, context, recommendations, quality, risk, integration, analytics, operations, push_events, ai_suggestion）
- 152 个测试通过

### 当前进行中

- 前端：基于 reference/omni-csx-v35 的 Agent Console 和 Admin Console
- 完善 shipment、refund、conversation 在各 e-commerce 平台的 adapter
- 完善 quality、risk、analytics 路由

### 暂不做的

- 全平台 100% 字段拟真
- DeerFlow / DeepAgents 作为核心运行时
- 复杂 RAG
- 自动发送客服回复
- MQ / Kafka 重型基础设施
- 所有平台一次性全覆盖

---

## 3. 必须遵守的设计原则

### 3.1 真相来源

官方 API 返回、消息推送、错误码、状态推进，必须来自以下组合：

- **fixtures**（主要来源，官方级完整字段）
- state machine
- validators
- emitters
- repositories

**禁止用 LLM 直接生成"官方真相 payload"。**

### 3.2 统一分层

严格保持以下边界：

- `official-sim-server`：模拟平台行为
- `providers/*`：平台 provider，负责对接或消费 official-sim / real API
- `domain-service` / `unified`：标准化领域对象
- `user-sim-service`：仿真用户行为并驱动联调
- **前端（reference/omni-csx-v35/apps/*-console/）**：只调用 domain-service 的统一 API

### 3.3 可回放

所有仿真 run 都必须至少支持：

- 查询当前状态
- 查询状态快照
- 查询 artifacts
- 查询 push events
- 回放 push event
- 生成 evaluation report

### 3.4 可测试

任何新增功能都必须附带测试，最低要求：

- 单元测试
- 状态机转移测试
- API 路由测试
- fixture 一致性测试

### 3.5 可审计

所有重要对象都必须带：

- run_id
- request_id
- platform
- scenario_key
- step_no
- created_at / updated_at

---

## 4. 仓库约定

### 4.1 目录结构概览

```
apps/
  core/
    domain-service/          # 中台统一业务层 (port 8000)
      app/
        api/routes/          # 15 个路由模块
        core/                # 配置、依赖
        services/            # 领域服务
        adapters/            # 平台 adapter + registry
      models/unified.py      # 统一数据模型
      providers/             # 6 平台 provider
        taobao/, douyin_shop/, jd/, xhs/, kuaishou/, wecom_kf/
      tests/
  sim/
    official-sim-server/     # 平台行为仿真器 (port 8001)
      app/
        api/routes/          # runs, query, mock_compat
        domain/              # scenario_engine
        platforms/           # 平台 profile
        models/              # SQLAlchemy DB 模型
      fixtures/              # 平台 fixture 数据
    user-sim-service/        # 用户行为仿真器 (port 8002)
      nodes/                 # conversation_studio, user_simulator, etc.
      graphs/                # LangGraph orchestrator
      services/              # 外部服务客户端
      static/                # conversation_studio.html

reference/omni-csx-v35/      # 原始完整系统（参考用）
  apps/
    agent-console/           # Next.js 坐席工作台
    admin-console/           # Next.js 管理后台
    domain-service/          # 原始 domain-service
    ai-orchestrator/         # 原始 AI 编排
  infra/
    docker/docker-compose.yml
    migrations/              # 39 SQL 迁移
```

### 4.2 不要擅自改动

除非任务明确要求，不要大改以下模块的既有行为：

- `reference/omni-csx-v35/` 下的任何代码（仅供参考，不要改）
- 现有 `providers/*` 的 public interface

允许在必要时增加 adapter / integration 接口，但不要破坏已有契约。

---

## 5. 数据与状态建模规则

### 5.1 仿真表（official-sim-server）

已实现：

- simulation_runs
- simulation_events
- state_snapshots
- push_events
- artifacts
- evaluation_reports

### 5.2 统一字段约定

- 金额用 `Decimal` / Pydantic `condecimal`
- 时间统一存 UTC，接口输出带时区
- 外部对象 ID 原样保留，内部对象使用独立主键
- 平台枚举统一用小写 snake，不混用
- 所有状态字段必须有 enum 定义，不允许裸字符串散落在逻辑中

---

## 6. API 约定

### 6.1 domain-service

| 路由前缀 | 说明 |
|---|---|
| `/api/orders` | 订单查询 |
| `/api/shipments` | 物流跟踪 |
| `/api/after-sales` | 退款/售后管理 |
| `/api/conversations` | 会话管理 |
| `/api/context` | 业务上下文聚合 |
| `/api/recommendations` | AI 回复建议 |
| `/api/quality` | 服务质量监控 |
| `/api/risk` | 风险标记 |
| `/api/integration` | ERP / 外部集成 |
| `/api/analytics` | 业务指标 |
| `/api/operations` | 运营管理 |
| `/api/push-events` | 推送事件跟踪 |
| `/api/ai` | AI 建议 |

### 6.2 official-sim-server

- `POST /official-sim/runs`
- `GET /official-sim/runs/{run_id}`
- `POST /official-sim/runs/{run_id}/advance`
- `GET /official-sim/runs/{run_id}/artifacts`
- `POST /official-sim/runs/{run_id}/inject-error`
- `POST /official-sim/runs/{run_id}/replay-push`
- `GET /official-sim/runs/{run_id}/report`
- `GET|POST /official-sim/query/...`
- `/mock/{platform}/...` (向后兼容路由)

### 6.3 user-sim-service

- `POST /conversation-studio/runs`
- `POST /conversation-studio/runs/{id}/next`
- `GET /conversation-studio/runs/{id}`
- `GET /conversation-studio/runs/{id}/debug`
- `GET /conversation-studio/runs/{id}/messages`
- `GET /conversation-studio/runs/{id}/report`

要求：

1. 所有接口返回统一 envelope 或明确 schema。
2. 所有错误都有稳定 code / message / request_id。

---

## 7. fixture 规则

### 7.1 目录规则

每个平台至少有三类 fixture：

- `success/`
- `edge_case/`
- `error_case/`

### 7.2 命名规则

示例：

- `order_wait_ship.json`
- `order_shipped_partial.json`
- `refund_pending_review.json`
- `push_order_status_changed.json`
- `callback_enter_session.json`

### 7.3 fixture 使用原则

- fixture 不是任意 JSON 样例，而是状态机产物或状态机模板
- fixture 必须能被测试引用
- fixture 版本变更必须同步更新测试
- 同一个状态不可出现多个互相冲突的 schema

---

## 8. 测试与验证

每完成一个 milestone，必须运行：

1. lint
2. 单元测试
3. 集成测试

若任一验证失败：

- 先修复
- 再继续下一 milestone
- 禁止带着失败测试进入下个阶段

---

## 9. 编码要求

### 9.1 Python 代码

- 优先使用清晰、可维护、显式的类型定义
- 核心 domain/service/repository 必须有类型注解、Pydantic schema 与 DB model 分离
- 路由层不直接写复杂业务逻辑
- 状态机逻辑集中管理，不允许分散在 route 中

### 9.2 FastAPI 要求

- 路由按平台 / runs 分模块
- 统一在 `api/router.py` 聚合
- 使用依赖注入获取 service / repo
- 路由层只做：参数校验、service 调用、response 序列化

### 9.3 数据库要求

- migration 必须可重复执行
- 所有外键和索引要明确
- 核心查询路径必须有索引
- 重要写入必须在事务内

---

## 10. 日志、审计、回放

必须记录：

- run 创建 / state advance / artifact build
- push event emit / ack
- inject-error / replay-push
- evaluation 生成

日志字段：run_id, platform, scenario_key, step_no, request_id, event_type

---

## 11. 完成定义（Definition of Done）

1. 目标代码已实现
2. tests 通过
3. fixtures 已提交（如适用）
4. README/usage 示例可运行（如适用）
5. 未决问题已明确写入 TODO / decision notes

---

## 12. 优先级判断规则

1. 正确性
2. 可回放
3. 可测试
4. 可审计
5. 与现有 unified/provider 兼容
6. 代码优雅性
7. 开发速度

---

## 13. 不确定时处理

1. 不要臆造平台事实
2. 优先保守实现最小可运行版本
3. 写出 TODO / decision note
4. 保持接口稳定
5. 用 fixture + test 锁定当前行为

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
