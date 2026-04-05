# 仿真链路现状评估（2026-04-02）

## 目的

本文记录当前仓库中两条关键能力链路的现状判断：

1. `user-sim-service` 是否已经完成“用户模拟 agent”的职责
2. `official-sim-server` 是否已经完成“官方 API / callback / webhook 仿真层”的职责
3. `domain-service` 是否已经完成“中台统一层 / 唯一业务入口”的职责

本文是现状评估，不是实施方案。

补充说明（2026-04-02 二次校正）：

- 本文主体记录的是第一次系统评估时的 baseline。
- 2026-04-02 当天后续修复已经补上：
  - `official-sim` 会话 / 消息 run-aware 查询
  - `user-sim` -> `official-sim` artifact -> event 事实落库
  - `OdooProvider` real 模式同步桥接
  - 平台订单号 -> Odoo 单据的最小稳定映射层
- 因此本文中凡是“`official_run_id` 还未真正进入查询链”或“real Odoo 同步调用还不可用”的旧判断，都应以第八章补充校正和 `docs/reports/2026-04-02-system-fix-checklist.md` 的最新记录为准。

---

## 结论摘要

### 1. `user-sim-service`

- 设计方向：合理
- 当前完成度：部分完成
- 当前判断：已经具备“驱动联调”的骨架，但还不是“可信的端到端用户模拟 agent”

原因：

- 它已经能创建 run、绑定 `official_run_id`、驱动多轮对话、调用 `domain-service` 获取推荐回复，并把用户消息/回复写回 `official-sim`
- 但它尚未严格依赖同一条官方事实链运行；当中台回复不可用时，还会回退到 `official-sim` 文本适配器，甚至再回退到 stub 回复，导致链路断了也可能表现成“还能继续对话”

### 2. `official-sim-server`

- 设计方向：合理
- 当前完成度：部分完成
- 当前判断：已经具备“仿真运行时”的核心骨架，但还没有完全成为严格的“官方真相来源”

原因：

- 它已经有 run 生命周期、状态推进、artifact、push、回放、错误注入、report、兼容 mock 路由
- 但 run 状态没有稳定地暴露给 `domain-service` 作为统一事实源；同时部分平台 profile 在 run 推进时生成的是“规范化后的简化 payload”，而不是官方 raw payload

### 3. `domain-service`

- 设计方向：合理
- 当前完成度：部分完成
- 当前判断：已经具备“中台入口层”的基本骨架，但还没有真正成为稳定、严格、统一的业务中枢

原因：

- 它已经有统一路由层、gateway、capability、context 聚合、recommendation、quality、risk、push 接收
- 但当前实现仍存在多套 adapter 路径、静默降级、placeholder 业务逻辑、run 不感知查询等问题，导致“唯一入口”已经建立，“统一真相层”还没有建立

---

## 一、`user-sim-service` 应该做什么

用户模拟 agent 在本项目里不应该充当“业务事实生成器”，而应该充当：

- 虚拟客户：根据订单/物流/售后/情绪生成真实用户消息
- 联调驾驶员：驱动 `domain-service` 走完整条中台链路
- 对话评估器：判断中台回复是否准确、是否敷衍、是否需要升级人工
- run 协调器：让用户侧动作和 `official-sim` 的 run 生命周期处在同一个场景里

对应代码入口：

- `apps/sim/user-sim-service/api/routes/conversation_studio.py`
- `apps/sim/user-sim-service/nodes/conversation_studio.py`
- `apps/sim/user-sim-service/services/domain_service_client.py`
- `apps/sim/user-sim-service/services/official_sim_client.py`

---

## 二、`user-sim-service` 当前做到了什么

### 已做到

- 能创建对话 run，并绑定 `official_run_id`
  - `apps/sim/user-sim-service/api/routes/conversation_studio.py`
- 每轮会优先向 `domain-service` 请求回复推荐
  - `apps/sim/user-sim-service/nodes/conversation_studio.py`
- 每轮会把用户消息、对话轮次、推荐回复 artifact 写回 `official-sim`
  - `apps/sim/user-sim-service/api/routes/conversation_studio.py`
- 能根据回复质量和重复追问情况决定是否升级人工
  - `apps/sim/user-sim-service/nodes/conversation_studio.py`

### 还没做到

#### 1. 没有严格围绕同一个官方事实链运行

`user-sim-service` 会把 `official_run_id` 传给 `domain-service`：

- `apps/sim/user-sim-service/nodes/conversation_studio.py`

但 `domain-service` 查询订单/物流/售后时，并没有使用这个 `official_run_id` 去读取 run 当前状态，只是普通按 `platform + biz_id` 查询：

- `apps/core/domain-service/app/services/business_context_service.py`
- `apps/core/domain-service/app/services/official_sim_provider.py`

这意味着：

- 对话 run 和官方 run 虽然“绑定了 ID”
- 但中台查询到的事实，不一定来自这个 run 的当前状态

#### 2. 对链路失败的暴露不够严格

当前回复链路是：

1. 先调用 `domain-service`
2. 如果失败，再调用 `official-sim` 文本适配器
3. 如果还失败，再调用 stub 回复

对应代码：

- `apps/sim/user-sim-service/nodes/conversation_studio.py`
- `apps/sim/user-sim-service/nodes/reply/unified.py`
- `apps/sim/user-sim-service/nodes/reply/official_sim.py`
- `apps/sim/user-sim-service/nodes/reply/stub.py`

这会带来一个问题：

- 实际中台链路已经断了
- 但用户模拟 agent 仍然能“给出一个回复”

因此它更像“演示 agent”，而不是“严格验链 agent”。

### 对 `user-sim-service` 的判断

`user-sim-service` 的宏观职责定义是正确的，但当前实现还没有达到“它该做的事情”。

更准确地说：

- 它已经是一个可用的多轮联调驱动器
- 还不是一个可靠的、以官方真相为唯一基础的用户模拟测试 agent

---

## 三、`official-sim-server` 应该做什么

官方仿真层的职责应该是：

- 以 fixture + state machine 为真相来源
- 仿真官方 API、push、callback、webhook
- 管理 run 生命周期
- 记录 artifact、push event、snapshot、evaluation report
- 对外暴露可回放、可审计、可验证的官方行为

对应代码入口：

- `apps/sim/official-sim-server/app/api/routes/runs.py`
- `apps/sim/official-sim-server/app/api/routes/raw_query.py`
- `apps/sim/official-sim-server/app/api/routes/mock_compat.py`
- `apps/sim/official-sim-server/app/domain/scenario_engine.py`
- `apps/sim/official-sim-server/app/platforms/*/profile.py`

---

## 四、`official-sim-server` 当前做到了什么

### 已做到

#### 1. run 生命周期骨架完整

已具备：

- 创建 run
- 推进一步
- 查询 run
- 查询 artifacts
- 查询 pushes
- replay push
- inject error
- report 汇总

对应代码：

- `apps/sim/official-sim-server/app/api/routes/runs.py`

#### 2. 持久化和可审计对象基本齐全

当前已有表模型：

- `simulation_runs`
- `simulation_events`
- `state_snapshots`
- `push_events`
- `artifacts`
- `evaluation_reports`

对应代码：

- `apps/sim/official-sim-server/app/models/models.py`

#### 3. 平台 profile、场景和错误注入已经成型

当前已经具备：

- 多平台状态机场景
- push 模板
- 错误注入
- mock 兼容层

对应代码：

- `apps/sim/official-sim-server/app/platforms/*/profile.py`
- `apps/sim/official-sim-server/app/api/routes/mock_compat.py`

#### 4. 测试面覆盖到基础行为

现有测试已经覆盖：

- 各平台 profile
- runs 路由
- artifacts
- 错误注入
- push notifier
- report

对应目录：

- `apps/sim/official-sim-server/tests/`

### 还没做到

#### 1. 它还没有稳定地成为 `domain-service` 的唯一真相来源

虽然 `domain-service` 当前默认走 `official_sim` provider mode，但实际读取订单时调用的是：

- `GET /official-sim/raw/orders/{order_id}?platform=...`

对应代码：

- `apps/core/domain-service/app/services/official_sim_provider.py`

而 raw query 路由并不按 `run_id` 读取，也不真正按 `order_id` 命中某个实体，只是返回平台可用 fixture：

- `apps/sim/official-sim-server/app/api/routes/raw_query.py`

这意味着：

- `official-sim` 有 run
- 但 `domain-service` 查询时没在读 run 的当前状态

这是当前仿真链路最大的断点之一。

#### 2. raw query 更像“fixture 浏览器”，不是“实体查询接口”

当前 raw order 查询逻辑：

- 如果显式给了 `scenario_key`，就返回该 fixture
- 否则返回该平台第一个能加载的场景

对应代码：

- `apps/sim/official-sim-server/app/api/routes/raw_query.py`

这不满足真正的“官方 API 仿真查询”要求，因为：

- 它不基于 run 当前 step
- 不基于 order 实体状态
- 不基于 order_id 映射到具体场景

#### 3. run 内实体 ID 与中台查询实体 ID 没有统一

`ScenarioEngine` 在推进 run 时会生成自己的订单号：

- `apps/sim/official-sim-server/app/domain/scenario_engine.py`

而 `user-sim-service` / `domain-service` 在查询上下文时，使用的是用户侧选择出来的 `order_id`。

这会导致：

- run 里推进的是一套实体
- 中台查询的是另一套实体

从架构上看，这说明“run 编排链”和“中台读事实链”还没有闭合。

#### 4. 平台 profile 输出形态不一致

这是当前 `official-sim-server` 最大的设计偏差之一。

现状分为两类：

- Taobao / Douyin 的 `get_default_order_payload()` 更接近官方 fixture 形态
- JD / XHS / Kuaishou 的 `get_default_order_payload()` 会先把 fixture 提炼成一层简化后的统一字段结构

对应代码：

- `apps/sim/official-sim-server/app/platforms/taobao/profile.py`
- `apps/sim/official-sim-server/app/platforms/douyin_shop/profile.py`
- `apps/sim/official-sim-server/app/platforms/jd/profile.py`
- `apps/sim/official-sim-server/app/platforms/xhs/profile.py`
- `apps/sim/official-sim-server/app/platforms/kuaishou/profile.py`

这与项目原则存在冲突：

- 仿真层应该输出“官方 payload”
- 统一字段映射应该留给 provider / adapter / domain-service

目前 JD / XHS / Kuaishou profile 已经越过了这个边界。

#### 5. fixture 被直接修改，且与全局缓存共享

`FixtureLoader` 带全局缓存：

- `providers/utils/fixture_loader.py`

但多个平台 profile 会直接修改 `FixtureLoader.get_response()` 返回的对象：

- `apps/sim/official-sim-server/app/platforms/taobao/profile.py`
- `apps/sim/official-sim-server/app/platforms/douyin_shop/profile.py`

这会导致：

- 不同 run 之间共享可变 fixture
- 后一次调用可能污染前一次调用的结果

这是一个真实的仿真隔离问题，不只是代码风格问题。

#### 6. mock 兼容层、raw 路由、测试预期之间还存在不一致

当前仓库里可以看到以下并存现象：

- router 中注册了 `/official-sim/query`
- 但某些测试又声明不应存在 `/query`
- 部分旧测试提到 `/official-sim/unified/*`
- 但当前 router 并未注册 unified 路由

对应代码和测试：

- `apps/sim/official-sim-server/app/api/router.py`
- `apps/sim/official-sim-server/tests/test_router.py`
- `apps/sim/official-sim-server/tests/test_integration.py`

这说明：

- `official-sim-server` 的对外接口边界还没有完全收敛
- 文档、测试、现实现状之间仍有历史残留

### 对 `official-sim-server` 的判断

`official-sim-server` 的设计方向是正确的，而且其“运行时骨架”已经相当完整。

但如果按“官方 API 仿真层”的严格标准来判断，当前只能算：

- 已经完成了运行时管理能力
- 还没有完全完成真相层职责

更准确地说：

- 它已经像一个功能完整的 simulation runtime
- 还不像一个严格的、由 run 当前状态驱动的官方事实服务

---

## 五、当前全链路的关键断点

### P0 断点

1. `official_run_id` 没有真正进入平台事实查询链
2. raw query 不是 run-aware，也不是 order-aware
3. run 内订单 ID 与中台查询订单 ID 没有统一

### P1 断点

1. adapter 失败被静默吞掉，导致“接口成功但数据为空”
2. `user-sim-service` 有多级 fallback，掩盖真实断链
3. `official-sim` profile 输出形态不一致，部分平台提前做了规范化

### P2 断点

1. fixture 共享缓存被原地修改，存在跨 run 污染
2. push 目前在 `domain-service` 侧是进程内内存态，适合联调，不适合稳定事实归档
3. 文档、测试、router 对外契约仍存在历史不一致

---

## 六、`domain-service` 应该做什么

中台统一层在本项目中的职责应当是：

- 成为前端与上层系统唯一访问入口
- 屏蔽不同平台官方 payload 差异
- 通过 provider + adapter + unified model 输出稳定领域对象
- 聚合平台事实、ERP 事实、push 事实、上下文、推荐、质检、风控
- 保持对 `official-sim-server`、真实 provider、mock provider 的接口稳定

对应代码入口：

- `apps/core/domain-service/app/api/router.py`
- `apps/core/domain-service/app/services/platform_gateway_service.py`
- `apps/core/domain-service/app/services/*`
- `apps/core/domain-service/app/adapters/*`
- `apps/core/domain-service/models/unified.py`

---

## 七、`domain-service` 当前做到了什么

### 已做到

#### 1. “唯一业务入口”这件事在 API 结构上已经成立

当前已经有统一路由层：

- `/api/orders`
- `/api/shipments`
- `/api/after-sales`
- `/api/conversations`
- `/api/context`
- `/api/recommendations`
- `/api/quality`
- `/api/risk`
- `/api/analytics`
- `/api/integration`
- `/api/push-events`

对应代码：

- `apps/core/domain-service/app/api/router.py`

从服务边界设计上看，这个方向是对的。

#### 2. gateway / provider mode / capability 骨架已经建立

当前已经有：

- `PlatformGatewayService`
- provider mode 切换（`official_sim` / `mock` / `real`）
- 平台 capability
- registry

对应代码：

- `apps/core/domain-service/app/services/platform_gateway_service.py`
- `apps/core/domain-service/app/adapters/registry.py`
- `apps/core/domain-service/app/adapters/capabilities.py`

这说明中台已经具备“多平台统一入口”的最基本控制平面。

#### 3. unified model 已经存在

当前已有：

- `UnifiedOrder`
- `UnifiedShipment`
- `UnifiedRefund`
- `UnifiedConversation`

对应代码：

- `apps/core/domain-service/models/unified.py`

这说明统一层不是完全缺失，而是已经开始成型。

#### 4. context / recommendation / push 接收链路已经接入

当前已经具备：

- 业务上下文聚合
- 推荐生成
- push 事件接收与注入 context

对应代码：

- `apps/core/domain-service/app/services/business_context_service.py`
- `apps/core/domain-service/app/services/recommendation_service.py`
- `apps/core/domain-service/app/api/routes/push_events.py`

这说明中台层已经在承担“编排与聚合”的职责，而不是纯转发。

### 还没做到

#### 1. adapter 架构没有真正收敛为单一路径

当前仓库里同时存在：

- `app/adapters/platform_adapters.py`
- `adapters/platform_adapter.py`

而运行时链路实际上大量直接使用根级 `adapters/platform_adapter.py`，例如：

- `apps/core/domain-service/app/services/order_domain_service.py`

与此同时，registry 又包装了一层 `app/adapters/platform_adapters.py`：

- `apps/core/domain-service/app/adapters/registry.py`

这说明中台的 adapter 抽象还没有真正收敛为“唯一实现路径”。

结果是：

- 架构上有 registry / contract
- 运行时又在绕过 registry 直接手写 adapter 映射

这会削弱“统一层”的可维护性。

#### 2. 统一层存在大量静默降级

这是当前中台层最严重的问题之一。

例如订单链路：

- 先调用 adapter
- adapter 抛异常后直接吞掉
- 再回退到 generic raw normalization

对应代码：

- `apps/core/domain-service/app/services/order_domain_service.py`

但 generic raw normalization 并不理解官方嵌套 payload，因此会出现：

- 接口 200
- 但字段为空、金额为 0、products 为空

context 聚合层也有类似问题：

- 订单失败就 `pass`
- 物流失败就 `pass`
- 售后失败就 `pass`

对应代码：

- `apps/core/domain-service/app/services/business_context_service.py`

这会让“统一入口”变成“尽量返回一些东西”，而不是“稳定返回可信统一对象”。

#### 3. `official_run_id` 进入了 API，但没有真正进入统一事实查询链

推荐和 context 接口已经接收 `official_run_id`：

- `apps/core/domain-service/app/api/routes/context.py`
- `apps/core/domain-service/app/api/routes/recommendations.py`

但在 `BusinessContextService` 中，它只用于查 push events，不用于真实订单/物流/售后查询：

- `apps/core/domain-service/app/services/business_context_service.py`

而底层 provider 查询也不带 `run_id`：

- `apps/core/domain-service/app/services/official_sim_provider.py`

这意味着中台层还没有真正做到：

- “围绕同一个 official run 聚合上下文”

这一点直接影响“中台统一层”是否成立。

#### 4. 多个领域服务仍处于 placeholder / 半实现状态

几个明显例子：

- `AnalyticsService` 仍在用手写 `scenario_map` 和 `amount_map` 产出统计，不是从真实 gateway / context 聚合出来的
  - `apps/core/domain-service/app/services/analytics_service.py`
- `RiskService` 和 `QualityService` 仍是本地规则引擎骨架，没有与统一上下文形成更深耦合
  - `apps/core/domain-service/app/services/risk_service.py`
  - `apps/core/domain-service/app/services/quality_service.py`
- `ConversationDomainService` 仍会直接读 sim fixture，绕过统一 gateway/provider 边界
  - `apps/core/domain-service/app/services/conversation_domain_service.py`

这些都说明：

- 中台的“服务层结构”已经有了
- 但很多业务还没真正接入统一事实源

#### 5. 部分接口契约已经出现“双轨制”

例如 conversations 路由同时服务：

- agent-console 兼容扁平 JSON
- 现有 envelope 风格接口

对应代码：

- `apps/core/domain-service/app/api/routes/conversations.py`

这对短期兼容是有帮助的，但对中长期会带来问题：

- 一个中台层同时暴露两套风格不同的 API 契约
- “统一入口”在接口层开始分裂

#### 6. 依赖装配也存在重复路径

当前同时存在：

- `app/dependencies.py`
- `app/core/deps.py`

二者都在装配 registry / gateway。

这说明依赖注入路径也还没有完全收敛。

这不是 P0 问题，但它是“中台统一层还在演化中”的一个明确信号。

#### 7. 测试覆盖有一定数量，但对“统一性”的验证还不够强

当前已有：

- adapter 测试
- API 测试
- registry / gateway 测试
- push event 测试

对应目录：

- `apps/core/domain-service/tests/`

但从测试内容看，很多断言仍停留在：

- 状态码为 200
- 返回里包含某个字段

而不是验证：

- 官方 payload 是否被稳定适配为统一模型
- fallback 是否掩盖了链路错误
- context 是否严格绑定 official run
- 中台返回是否来自统一真相链

所以“测试存在”不等于“统一层成立”。

### 对 `domain-service` 的判断

`domain-service` 的设计方向是正确的，分层结构也已经相当明确。

但它当前更像：

- “多平台业务入口 + 统一层骨架”

而不是：

- “严格、稳定、可依赖的统一业务中枢”

更准确地说：

- 它已经完成了入口聚合
- 还没有完成统一真相收敛

---

## 八、`domain-service` 对 Odoo 的最小侵入接入现状

### 设计位置是否合理

如果约束是“最小侵入接入 Odoo，不大改现有平台链路”，当前放置位置基本是对的。

现状是：

- Odoo 没有被塞进各平台 provider / adapter
- Odoo 主要挂在 `BusinessContextService` 和 `IntegrationService`
- 也就是说，它被当作“中台补充事实源 / ERP 补充信息源”，而不是平台官方真相源

对应代码：

- `providers/odoo/provider.py`
- `apps/core/domain-service/app/services/business_context_service.py`
- `apps/core/domain-service/app/services/integration_service.py`
- `apps/core/domain-service/app/api/routes/integration.py`

这个边界是合理的，因为：

- 平台订单、物流、售后事实仍然应该先来自平台 provider + adapter
- Odoo 更适合补充库存、审核、异常、履约等 ERP 侧信息
- 这样接入不会破坏现有 `official-sim` / `mock` / `real` 平台链路

### 当前已经做到的

#### 1. Odoo 已经以独立 provider 的形式挂进中台依赖

依赖装配已经存在：

- `apps/core/domain-service/app/dependencies.py`

中台当前会创建 `OdooProvider`，并把它注入：

- `BusinessContextService`
- `IntegrationService`

这说明“接入点”已经选定，而且不是侵入各平台 adapter。

#### 2. mock Odoo 路径已经可用

当前 mock provider 已经提供：

- inventory
- order audit
- order exception
- fulfillment

对应代码：

- `providers/odoo/mock/provider.py`

相关测试也主要覆盖了这条路径：

- `apps/core/domain-service/tests/test_odoo_provider.py`
- `apps/core/domain-service/tests/test_business_context_odoo.py`

这说明：

- 本地联调和页面占位所需的 Odoo 侧数据已经能跑起来
- 但主要是 mock 能跑，不代表 real Odoo 已经打通

#### 3. Odoo 当前被用作 context enrichment，这个方向是对的

`BusinessContextService` 当前会在订单上下文里补充：

- `inventory_snapshot`
- `order_audit_snapshot`
- `order_exception_snapshots`
- `fulfillment_snapshot`

对应代码：

- `apps/core/domain-service/app/services/business_context_service.py`

从职责上看，这符合“最小侵入”原则：

- 不改统一订单主模型来源
- 只在 context 聚合层做扩展字段补充

### 当前补充校正

#### 1. `official-sim` 和 Odoo 不是“没关系”，而是“非直连、强关联”

更准确地说，三者关系现在应理解为：

- `official-sim` 负责平台官方事实
- `domain-service` 负责统一读取、聚合、标准化
- Odoo 负责 ERP 补充事实

这意味着：

- `official-sim` 不直接模拟 Odoo API
- Odoo 也不反向生成平台官方 payload
- 但两者会在 `domain-service` 中通过 `platform + biz_id/order_id (+ official_run_id)` 汇合

所以“模拟层和 Odoo 没关系”这个说法不准确；准确说法应该是：

- 没有 direct API 仿真关系
- 有明确的业务关联和主数据关联需求

#### 2. real Odoo 同步桥已经可用，但映射收口还未完全结束

`OdooProvider` 现在已经提供 real 模式同步桥，`BusinessContextService` 可以直接调用：

- `get_order_audit(order_id, platform=platform)`
- `get_fulfillment(order_id, platform=platform)`

这说明：

- “real Odoo 只能 async，现有同步服务层完全不能用”这条旧结论已经过期
- `context` 链路已经能稳定消费 real Odoo

但仍有一个收口缺口：

- `IntegrationService` 目前仍然只按 `order_id` 调 Odoo，没有把 `platform` 继续传入

因此当前更准确的状态是：

- `context` 路径：已能使用平台订单号稳定映射
- `integration` 路径：仍未完全共享同一套映射收口

#### 3. 平台订单号与 Odoo 的关系已经建了运行态稳定映射，但还不是 Odoo 原生字段天然对上

仓库当前已经新增最小稳定映射层，用来把平台订单号稳定挂到 Odoo `sale.order` / `stock.picking`：

- `providers/odoo/real/link_resolver.py`

但这层关系之所以需要在运行时补，是因为现有导数 / 导入脚本没有把外部平台订单号稳定保留下来：

- `scripts/data_tools/convert_to_odoo.py`
- `scripts/data_tools/import_to_odoo.py`

也就是说，当前关系是：

- 设计上：平台订单号应该能关联到 ERP 单据
- 运行时：已经通过持久化映射器补上
- 数据源层：Odoo 导入数据还没有天然保存好这层自然键

#### 4. Odoo 目前仍然是 enrichment，不是平台真相源

这条边界没有变，而且仍然合理。

当前 Odoo 只进入：

- `/api/context`
- `/api/integration`

它不直接决定：

- `/api/orders`
- `/api/shipments`
- `/api/after-sales`

因此当前体系更准确的定义是：

- 平台事实以 `official-sim` / provider 为主
- Odoo 补充库存、审核、异常、履约等 ERP 事实
- 两者通过中台聚合，而不是并列充当“平台官方真相源”

### 对 Odoo 接入现状的判断

如果评价标准是“最小侵入接入 + 能稳定做 ERP enrichment”，当前方向是对的，而且已经不只是 mock 骨架。

更准确地说：

- Odoo 在中台里的架构位置是对的
- real Odoo 同步桥已经打通
- 平台订单号 -> Odoo 单据的最小稳定映射已经存在
- 当前最大缺口不是“要不要接 Odoo”，而是“让 `integration` 链也共享 `platform` 感知映射，并把导数脚本里的自然键补回来”

## 九、最终判断

### 关于 `user-sim-service`

设计合理，但当前还没做到“它该做的事情”。

当前状态更接近：

- “能跑起来的联调驱动器”

而不是：

- “严格依赖官方真相链路的用户模拟 agent”

### 关于 `official-sim-server`

设计合理，但当前还没完全做好“官方 API 接口模拟”这件事。

当前状态更接近：

- “功能完整的仿真运行时”

而不是：

- “严格以 fixture + state machine + run 当前状态为唯一真相来源的官方仿真层”

### 关于 `domain-service`

设计合理，但当前还没有完全做好“中台统一层”这件事。

当前状态更接近：

- “统一入口 + 聚合骨架”

而不是：

- “稳定、严格、真正统一的平台中台”

它当前最大的价值已经建立在：

- API 入口统一
- provider mode 抽象
- business context 聚合

但当前最大的缺口仍然是：

- 真相来源没有真正统一
- fallback 过多且过于静默
- adapter / registry / service 边界尚未完全收敛

### 总体结论

当前三层都已经有了正确方向的骨架，但还没有真正闭合成同一条事实链。

项目下一阶段最重要的工作，不是继续增加更多页面或更多字段，而是先把下面这件事做实：

> `user-sim-service`、`domain-service`、`official-sim-server` 必须围绕同一个 `official_run_id`、同一个业务实体 ID、同一个 run 当前状态运行。

在这个条件成立之前，系统可以演示、可以联调、可以局部验证，但还不能算“严格打通”。
