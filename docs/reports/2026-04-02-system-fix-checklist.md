# 系统级修复实施清单（2026-04-02）

## 目标

本清单用于落实以下系统级修复目标：

- 打通 `user-sim-service` / `domain-service` / `official-sim-server` 的统一事实链
- 让 `domain-service` 真正成为统一中台入口，而不是“入口 + 静默 fallback 骨架”
- 以最小侵入方式接入 Odoo，使其稳定承担 context / integration 的 ERP 补充事实职责
- 让订单、上下文、集成接口达到“可联调、可验证、可解释”的可用状态

约束：

- 不大改现有平台 provider public interface
- 不修改 fixture 契约，不用 LLM 生成官方 payload
- Odoo 不进入平台 adapter 主链，只作为中台聚合补充事实源

---

## 任务清单

### A. 统一事实链

- [x] A1. 明确并固化统一事实边界：平台事实来自 `official-sim` / provider，ERP 补充事实来自 Odoo
- [x] A2. 将 `official_run_id` 从 context / recommendation 透传到订单事实查询链
- [x] A3. 让 `official-sim` raw/query 路径在提供 `run_id` 时优先返回 run 当前状态
- [x] A4. 保持未传 `run_id` 时的兼容行为，避免破坏现有 smoke / mock 使用方式

### B. 订单链路

- [x] B1. 收敛订单链路的 adapter 使用路径，避免“registry 一套、运行时一套”继续扩散
- [x] B2. 修复订单链路中“adapter 失败后静默成功但数据为空”的行为
- [x] B3. 修复淘宝 / 京东当前已定位的订单适配问题
- [x] B4. 验证 `/api/orders/{platform}/{id}` 在 taobao / jd / douyin_shop / xhs 上可稳定返回统一数据

### C. Context 聚合

- [x] C1. 让 `/api/context` 对订单事实、push 事实、Odoo 补充事实的来源可区分
- [x] C2. 减少关键字段静默吞错，至少在事实缺失时给出可诊断信号
- [x] C3. 验证 `official_run_id` 驱动的 context 确实围绕同一 run 聚合

### D. Odoo 最小侵入接入

- [x] D1. 保持 Odoo 只挂在 `BusinessContextService` 和 `IntegrationService`
- [x] D2. 让 Odoo real 模式在中台调用链中可用，不再停留在同步接口抛错状态
- [x] D3. 保留现有 mock 兼容能力，但清理明显误导性的静默 fallback
- [x] D4. 验证 `/api/integration/inventory`、`/order-audits`、`/order-exceptions`、`/fulfillment` 在 mock / real 下行为一致

### E. 测试与验证

- [x] E1. 为 run-aware 官方事实查询补测试
- [x] E2. 为订单 adapter / 订单域服务补回归测试
- [x] E3. 为 Odoo context / integration mock / real 路径补测试
- [x] E4. 跑通目标测试集并记录结果
- [x] E5. 完成 smoke 验证并记录接口结果

### F. 文档与决策记录

- [x] F1. 维护本清单的勾选状态
- [x] F2. 记录每次关键修改的文件、目的、影响范围
- [x] F3. 将未完成项和 residual risk 写入决策记录

### G. 三者关系纠偏与主数据映射收口（2026-04-02 补记）

- [x] G1. 在文档中明确 `official-sim` / `domain-service` / Odoo 的职责边界
- [x] G2. 在文档中纠正“模拟层和 Odoo 没关系”的误读，明确其属于“经中台聚合的关联关系”
- [x] G3. 在文档中记录当前已存在的运行态稳定映射层：平台订单号 -> Odoo 单据
- [x] G4. 让 `IntegrationService` 也把 `platform` 透传到 Odoo provider，统一 `context` / `integration` 的映射行为
- [x] G5. 调整 Odoo 导数 / 导入链，保留平台外部订单号到 Odoo 自然字段或独立映射资产
- [x] G6. 为 `integration` 路径映射收口和导数映射保留补充回归测试

### H. 五平台售后主链与 ID 语义收口（2026-04-03 补记）

- [x] H1. 为 5 个电商平台建立“按订单查售后”的统一事实入口，不再把 `order_id` 直接当 `refund_id`
- [x] H2. 在 `official-sim` 增加 `/official-sim/raw/after-sales/by-order/{order_id}`，同时让 direct after-sale lookup 识别 canonical / external 两类售后 ID
- [x] H3. 补齐 sim 订单别名与 canonical `after_sale_id` 规则，让 `*_ORDER_*` 与公共平台订单号都能落到同一条售后事实
- [x] H4. 让 `BusinessContextService` / `RecommendationService` 消费真实售后状态，不再统一回答“未知”
- [x] H5. 完成五平台售后 live smoke 和 `wecom_kf -> jd after-sale` 桥接 smoke，并把结果写回文档
- [x] H6. 补记同类产品 external ID / canonical ID 的通用做法，并记录当前仓库的落地原则

### I. 五平台物流主链与公共订单样本收口（2026-04-03 补记）

- [x] I1. 让 `official-sim` 的 `/raw/orders` / `/raw/shipments` 在公共订单样本上优先命中 shipped / delivering fixture，而不是落回第一个 `wait_pay` 样本
- [x] I2. 让 `OfficialSimProxyProvider` 归一化 `taobao / douyin_shop / xhs / kuaishou` 的官方 shipment payload，不再只有 JD 能读出物流事实
- [x] I3. 收口 `ask_shipment` 推荐逻辑，避免在物流缺失时误回售后模板
- [x] I4. 修复 `JDAdapter` 对官方 `33xxx / 34xxx / 90000` 订单状态码的统一映射
- [x] I5. 完成五平台 `orders / shipments / ask_shipment` real smoke，并把结果写回文档

### J. 五平台 alias / canonical ID 收口（2026-04-03 补记）

- [x] J1. 将五平台平台单 alias 规则统一收敛到公共 `sim_identity`，不再只写 JD 特例
- [x] J2. 让 `ConversationDomainService` 的 `wecom_kf -> biz_platform` 桥接支持 `taobao / douyin_shop / jd / xhs / kuaishou`
- [x] J3. 为 `orders / shipments / after-sales / context` 统一补出 `requested_order_id / external_order_id / canonical_order_id`
- [x] J4. 让 `OfficialSimProxyProvider` 接受 alias 与 public order id 的等价匹配，不再因 official payload 返回的是 public id 就误判 404
- [x] J5. 修复 `kuaishou` 退款中订单在 `/official-sim/raw/orders` 上误回 refund payload，保证 order 路径只返回订单事实
- [x] J6. 完成五平台 alias 直查和 `wecom_kf` 桥接的 live smoke，并把结果写回文档

### K. user fixture 唯一 external ID 与 wecom 多平台固定会话收口（2026-04-03 深夜补记）

- [x] K1. 为五平台 `users` fixture 中的 45 个业务订单补齐显式 `external_order_id`，不再默认多单共享一个公共样本单号
- [x] K2. 让 `providers/utils/sim_identity.py` 从 user fixtures 自动构建 alias <-> external id 映射，而不是继续依赖手写聚合表
- [x] K3. 让 `scripts/data_tools/odoo_seed_mapping.py` 把 user fixtures 订单也纳入 seed 收集，保证 Odoo link seed 与真实业务订单全集一致
- [x] K4. 扩充 `wecom_kf/users` 固定会话样本到 `taobao / douyin_shop / xhs / kuaishou`，并让 `ConversationDomainService` 在无 provider/run 时也能从 fixture 会话桥回对应业务平台
- [x] K5. 修复 `official-sim/raw/shipments` 在“已知订单但无物流事实”时误回默认 shipped fixture 的问题，避免 context 串到别的订单
- [x] K6. 完成唯一 external id、wecom 多平台固定会话、无物流显式 404 的回归测试与 live smoke

### L. 剩余问题盘点与收尾清单（2026-04-04 补记）

- [x] L1. 重新盘点当前“主链已通但尚未完全收口”的问题，不再只沿用 2026-04-02 / 2026-04-03 的修复语境
- [x] L2. 对仓库执行根仓 `pytest -q` 与整仓 `ruff check`，把工程治理问题显式暴露出来
- [x] L3. 新建专门的剩余问题清单文档，按优先级拆成可执行修复组
- [ ] L4. 按新清单继续执行收尾修复，并在每次完成后回写打勾和修改记录

---

## 修改思路与后续计划

### 本次文档纠偏思路

- 不把 `official-sim` 和 Odoo 写成“无关系”，因为 run 里的 `biz_id/order_id` 最终会被中台拿去做 ERP enrichment。
- 也不把它们写成“直接耦合”，因为 `official-sim` 仍然只模拟平台官方接口，Odoo 仍然是下游 ERP provider。
- 因此文档里统一改成：
  - 平台官方事实：`official-sim`
  - 统一聚合入口：`domain-service`
  - ERP 补充事实：Odoo
  - 关系形式：通过 `platform + biz_id/order_id (+ official_run_id)` 在中台汇合

### 后续代码收口计划

1. 已完成：收 `IntegrationService`。`/api/integration/order-audits` 和 `/api/integration/fulfillment` 在传平台订单号时已经复用 `platform` 感知的稳定映射。
2. 已完成代码实现并已在本机 Odoo 落地：`scripts/data_tools/convert_to_odoo.py` 现在会保留 `client_order_ref` 并生成 `platform_order_link_seed.json`；`scripts/data_tools/import_to_odoo.py` 会把 seed 提升为运行态 `data/runtime/odoo_order_links.json`，并可用 `--backfill-existing-orders` 对当前 live Odoo 的既有 `sale.order` / `stock.picking` 做回填。
3. 已完成第一层回归测试，后续仍需继续锁住：
   - `context` 和 `integration` 对同一平台订单号应命中同一 Odoo 单据
   - 导数 / 导入结果必须能保留可追溯的外部订单键
4. 已完成五平台 user fixture 唯一 external id 收口，下一步更适合继续压实：
   - live Odoo 已经完成 54 条新 `external_order_id` 的 backfill，后续重点转为做更多真实会话样本和 user-sim 多平台 run 模板
   - 将 `user-sim` 的固定样本和 run 模板也扩展到 `taobao / douyin_shop / xhs / kuaishou`，不再只让 JD 在会话驱动层拥有最完整样本

---

## 修改记录

### 2026-04-02

- 创建实施清单文档，作为本轮系统级修复的唯一执行跟踪面板。
- 统一事实链打通：
  - `apps/core/domain-service/app/services/official_sim_provider.py`
  - `apps/core/domain-service/app/services/platform_gateway_service.py`
  - `apps/core/domain-service/app/services/order_domain_service.py`
  - `apps/core/domain-service/app/services/shipment_domain_service.py`
  - `apps/core/domain-service/app/services/after_sale_domain_service.py`
  - `apps/core/domain-service/app/api/routes/orders.py`
  - `apps/core/domain-service/app/api/routes/shipments.py`
  - `apps/core/domain-service/app/api/routes/after_sales.py`
  - 目的：让 `official_run_id` 真正进入订单 / 物流 / 售后查询链，并在 raw-query 404 时保留更可读的 detail。
- official-sim run-aware 查询补齐：
  - `apps/sim/official-sim-server/app/api/routes/raw_query.py`
  - `apps/sim/official-sim-server/app/api/routes/runs.py`
  - `apps/sim/user-sim-service/api/routes/conversation_studio.py`
  - `providers/utils/fixture_loader.py`
  - 目的：让 `raw/orders`、`raw/shipments`、`raw/after-sales` 在传入 `run_id` 时围绕 run 当前状态返回数据，并消除 fixture cache 可变对象污染。
- 订单适配与降级修复：
  - `apps/core/domain-service/adapters/platform_adapter.py`
  - `apps/core/domain-service/app/services/order_domain_service.py`
  - 目的：修复 Taobao / JD / Douyin 官方 payload 解析、金额单位、`external_order_id` 类型，以及 adapter 失败后“200 但空数据”的假成功。
- Context / Odoo 收口：
  - `apps/core/domain-service/app/services/business_context_service.py`
  - `providers/odoo/provider.py`
  - 目的：显式记录 `data_sources` / `source_errors`，并用 sync bridge 让 real Odoo 模式可被现有同步服务层消费。
- real Odoo 标准 schema 兼容：
  - `providers/odoo/real/provider.py`
  - `.env`
  - `apps/core/domain-service/tests/test_odoo_provider.py`
  - `apps/core/domain-service/tests/test_integration_analytics.py`
  - 目的：将中台默认 Odoo 模式切到 `real`，并把 provider 从“依赖项目自定义 Odoo 模型”调整为“兼容标准 Odoo 16 schema”，包括：
    - `sale.order` 标准字段映射为 `order-audits`
    - `sale.exception` 缺失时返回空列表而非报错
    - `healthcheck` 和同步桥接补齐
    - 本机连接参数固化为 `olist_db / admin / admin`
- Odoo 平台单号防误判修复：
  - `providers/odoo/real/provider.py`
  - `apps/core/domain-service/tests/test_odoo_provider.py`
  - 目的：避免将超长平台外部订单号误判为 Odoo `id`，导致 `sale.order` / `stock.picking` 查询触发整数越界；修复后无映射时返回空 enrichment，而不是记录 SQL 错误。
- Odoo integration 映射收口：
  - `apps/core/domain-service/app/api/routes/integration.py`
  - `apps/core/domain-service/app/services/integration_service.py`
  - `apps/core/domain-service/tests/test_integration_service_platform.py`
  - `apps/core/domain-service/tests/test_integration_analytics.py`
  - 目的：让 `/api/integration/order-audits` 和 `/api/integration/fulfillment` 也能透传 `platform`，与 `BusinessContextService` 共用同一套平台订单号 -> Odoo 映射语义，并用路由/服务测试锁住行为。
- Odoo 种子映射资产补齐：
  - `scripts/data_tools/odoo_seed_mapping.py`
  - `scripts/data_tools/convert_to_odoo.py`
  - `scripts/data_tools/import_to_odoo.py`
  - `apps/core/domain-service/tests/test_odoo_seed_mapping.py`
  - 目的：让导数阶段显式产出 `platform_order_link_seed.json`，让导入阶段把 seed 提升成运行态 `odoo_order_links.json`，并同时保留 `sale.order.client_order_ref`，避免平台订单号只能靠运行时临时分配。
- real Odoo 既有订单回填：
  - `scripts/data_tools/import_to_odoo.py`
  - `scripts/data_tools/convert_to_odoo.py`
  - `scripts/data_tools/README.md`
  - `providers/odoo/real/provider.py`
  - `apps/core/domain-service/tests/test_odoo_provider.py`
  - `data/runtime/odoo_order_links.json`
  - 目的：让 `python scripts/data_tools/import_to_odoo.py --backfill-existing-orders --sale-order-limit 500` 能直接对当前本机 Odoo 的既有 `sale.order` 回填 `client_order_ref`，并为缺失映射订单补建最小 `stock.picking`，同时让 provider 在命中 `client_order_ref` 时继续返回平台订单号而不是 Odoo 内部 id。
- wecom 会话到电商订单平台桥接：
  - `apps/core/domain-service/app/services/conversation_domain_service.py`
  - `apps/core/domain-service/app/services/business_context_service.py`
  - `apps/core/domain-service/app/services/recommendation_service.py`
  - `apps/core/domain-service/tests/test_conversation_run_chain.py`
  - `apps/core/domain-service/tests/test_context_bridge.py`
  - 目的：让 `wecom_kf + official_run_id + JD_ORDER_*` 在上下文和推荐链中先解析 `biz_platform/biz_id`，再去读真实订单平台；同时补齐 `ask_order_status` 这类 user-sim intent，不再退回通用问候。
- JD shipment 官方 payload 归一化：
  - `apps/core/domain-service/app/services/official_sim_provider.py`
  - `apps/core/domain-service/tests/test_official_run_and_odoo_real.py`
  - 目的：让 `jingdong_order_search_responce` 这类 JD 官方订单查询结构也能被当作 shipment 事实消费，恢复 `/api/shipments/jd/*`、桥接 context 中的 `shipment_snapshot`，以及 `ask_shipment` 推荐对物流单号/承运商的读取。
- user-sim run 业务键稳定性修复：
  - `apps/sim/user-sim-service/nodes/user_simulator.py`
  - `apps/sim/user-sim-service/nodes/conversation_studio.py`
  - `apps/sim/user-sim-service/tests/test_conversation_studio_chain.py`
  - 目的：让同一条 `user-sim` run 一旦绑定到某个 `order_id`，后续 turn 不再重新随机挑单或把 `context.order_id` 覆盖成别的订单，避免 `official-sim` / `domain-service` 看到的 `biz_id` 在多轮会话中漂移。
- 五电商平台生命周期与用户问题审计：
  - `docs/reports/2026-04-03-five-platform-lifecycle-audit.md`
  - 目的：把 `taobao / douyin_shop / jd / xhs / kuaishou` 的订单 / 物流 / 售后生命周期、用户问题类型、统一接口 smoke 和推荐链 smoke 单独盘成报告，明确哪些是素材已具备、哪些是统一链仍未打通。
- 文档纠偏与计划补记：
  - `docs/reports/2026-04-02-sim-chain-assessment.md`
  - `docs/reports/2026-04-02-system-fix-checklist.md`
  - 目的：纠正 `official-sim` / `domain-service` / Odoo 三者关系的表述，明确“非直连、强关联”的边界，并把映射收口的后续代码计划挂入清单。
- 五平台售后主链和 canonical ID 收口：
  - `providers/utils/sim_identity.py`
  - `apps/sim/official-sim-server/app/api/routes/raw_query.py`
  - `apps/sim/official-sim-server/tests/test_raw_query.py`
  - `apps/core/domain-service/app/services/official_sim_provider.py`
  - `apps/core/domain-service/app/services/platform_gateway_service.py`
  - `apps/core/domain-service/app/services/after_sale_domain_service.py`
  - `apps/core/domain-service/app/services/business_context_service.py`
  - `apps/core/domain-service/app/services/recommendation_service.py`
  - `apps/core/domain-service/tests/test_after_sale_chain.py`
  - `apps/core/domain-service/tests/test_official_run_and_odoo_real.py`
  - `docs/reports/2026-04-03-five-platform-lifecycle-audit.md`
  - 目的：把五平台售后统一链从“`order_id` 被误当成 `refund_id`”修成“按订单查售后 -> 返回 canonical `after_sale_id` + 外部 ID 语义”，并让 `wecom_kf -> jd` 退款上下文真正取到售后事实。
- 五平台物流主链与公共订单样本收口：
  - `apps/sim/official-sim-server/app/api/routes/raw_query.py`
  - `apps/sim/official-sim-server/tests/test_raw_query.py`
  - `apps/core/domain-service/app/services/official_sim_provider.py`
  - `apps/core/domain-service/app/services/recommendation_service.py`
  - `apps/core/domain-service/adapters/platform_adapter.py`
  - `apps/core/domain-service/tests/test_official_run_and_odoo_real.py`
  - `apps/core/domain-service/tests/test_context_bridge.py`
  - `apps/core/domain-service/tests/test_adapters.py`
  - `docs/reports/2026-04-03-five-platform-lifecycle-audit.md`
  - 目的：让 `taobao / douyin_shop / jd / xhs / kuaishou` 的公共订单样本在 `orders / shipments / ask_shipment` 上都能走通，避免继续停留在“只有 JD 能查物流”和“shipment intent 串到 after-sale 模板”。
- 五平台 alias / canonical ID 收口：
  - `providers/utils/sim_identity.py`
  - `apps/core/domain-service/app/services/conversation_domain_service.py`
  - `apps/core/domain-service/app/services/order_domain_service.py`
  - `apps/core/domain-service/app/services/shipment_domain_service.py`
  - `apps/core/domain-service/app/services/after_sale_domain_service.py`
  - `apps/core/domain-service/app/services/business_context_service.py`
  - `apps/core/domain-service/app/services/official_sim_provider.py`
  - `apps/sim/official-sim-server/app/api/routes/raw_query.py`
  - `apps/core/domain-service/tests/test_conversation_run_chain.py`
  - `apps/core/domain-service/tests/test_context_bridge.py`
  - `apps/core/domain-service/tests/test_order_identity_fields.py`
  - `apps/core/domain-service/tests/test_official_run_and_odoo_real.py`
  - `apps/sim/official-sim-server/tests/test_raw_query.py`
  - 目的：把“请求 alias / 官方 external order id / canonical 资源 id”三层语义拆开，让五平台直查、`wecom_kf` 桥接和 Odoo enrich 都围绕同一套 order identity 规则运行。
- 五平台 user fixture 唯一 external id 与 wecom 固定会话扩展：
  - `apps/sim/official-sim-server/fixtures/taobao/users/*.json`
  - `apps/sim/official-sim-server/fixtures/douyin_shop/users/*.json`
  - `apps/sim/official-sim-server/fixtures/jd/users/*.json`
  - `apps/sim/official-sim-server/fixtures/xhs/users/*.json`
  - `apps/sim/official-sim-server/fixtures/kuaishou/users/*.json`
  - `apps/sim/official-sim-server/fixtures/wecom_kf/users/*.json`
  - `providers/utils/fixture_loader.py`
  - `providers/utils/sim_identity.py`
  - `scripts/data_tools/odoo_seed_mapping.py`
  - `apps/sim/official-sim-server/app/api/routes/raw_query.py`
  - `apps/core/domain-service/app/services/conversation_domain_service.py`
  - `apps/core/domain-service/tests/test_conversation_run_chain.py`
  - `apps/core/domain-service/tests/test_order_identity_fields.py`
  - `apps/core/domain-service/tests/test_odoo_seed_mapping.py`
  - `apps/sim/official-sim-server/tests/test_raw_query.py`
  - `data/staging/odoo_import/platform_order_link_seed.json`
  - 目的：让每条业务订单拥有自己的 external/public id，让 Odoo seed 跟着 user fixtures 走全集，同时让固定企微会话样本不再只围绕 JD，并修掉“无物流订单误回默认物流样本”的串单风险。
- 新 external id 的 seed / live Odoo 回填：
  - `data/staging/odoo_import/platform_order_link_seed.json`
  - `data/runtime/odoo_order_links.json`
  - `scripts/data_tools/import_to_odoo.py`
  - 目的：把新的 54 条 user fixture `external_order_id` 真正落进 live Odoo 的 `client_order_ref` 和运行态映射，不让“代码和 fixture 已改，但 ERP 侧仍停留旧订单号”的数据面偏差继续存在。
- 回归测试补充：
  - `apps/core/domain-service/tests/test_adapters.py`
  - `apps/core/domain-service/tests/test_official_run_and_odoo_real.py`
  - `apps/sim/official-sim-server/tests/test_raw_query.py`
  - 目的：锁定 run-aware 查询、订单金额/状态语义、Odoo real bridge、404 detail 透传。
- 剩余问题盘点与收尾清单：
  - `docs/reports/2026-04-04-remaining-issues-checklist.md`
  - 目的：把当前仍存在的问题从“未决问题”扩成可执行的详细收尾计划，明确区分：
    - 主链严格性
    - 全生命周期一单到底
    - 用户问题扩样本
    - 中台非主链真实化
    - 测试体系治理
    - 代码质量与旧适配层治理
  - 补充验证：
    - `pytest -q`
    - 结果：`74 errors during collection`
    - `ruff check apps/core/domain-service apps/sim/official-sim-server apps/sim/user-sim-service providers scripts/data_tools`
    - 结果：`602 errors`
  - 第一批收口已开始执行：
    - 已完成 `M1 / M2 / M3 / M4 / M5`
    - 详细记录见 `docs/reports/2026-04-04-remaining-issues-checklist.md`

---

## 验证记录

### 测试

- `PYTHONPATH=/home/kkk/Project/platform-sim/apps/core/domain-service:. pytest apps/core/domain-service/tests/test_official_run_and_odoo_real.py apps/core/domain-service/tests/test_adapters.py apps/core/domain-service/tests/test_unified.py apps/core/domain-service/tests/test_api.py apps/core/domain-service/tests/test_business_context_odoo.py apps/core/domain-service/tests/test_odoo_provider.py apps/core/domain-service/tests/test_integration_analytics.py -q`
  - 结果：`57 passed`
- `PYTHONPATH=/home/kkk/Project/platform-sim/apps/sim/official-sim-server:. pytest apps/sim/official-sim-server/tests/test_raw_query.py apps/sim/official-sim-server/tests/test_runs.py apps/sim/official-sim-server/tests/test_taobao.py -q`
  - 结果：`25 passed`
- 补充回归：
  - `PYTHONPATH=/home/kkk/Project/platform-sim/apps/core/domain-service:. pytest apps/core/domain-service/tests/test_official_run_and_odoo_real.py apps/core/domain-service/tests/test_adapters.py apps/core/domain-service/tests/test_unified.py -q`
  - 结果：`19 passed`
  - `PYTHONPATH=/home/kkk/Project/platform-sim/apps/core/domain-service:. pytest apps/core/domain-service/tests/test_odoo_provider.py apps/core/domain-service/tests/test_business_context_odoo.py apps/core/domain-service/tests/test_integration_analytics.py apps/core/domain-service/tests/test_api.py -q`
  - 结果：`41 passed`
  - `PYTHONPATH=/home/kkk/Project/platform-sim/apps/core/domain-service:. pytest apps/core/domain-service/tests/test_odoo_provider.py apps/core/domain-service/tests/test_business_context_odoo.py -q`
  - 结果：`24 passed`
  - `PYTHONPATH=/home/kkk/Project/platform-sim/apps/core/domain-service:/home/kkk/Project/platform-sim pytest apps/core/domain-service/tests/test_odoo_provider.py apps/core/domain-service/tests/test_business_context_odoo.py apps/core/domain-service/tests/test_integration_service_platform.py apps/core/domain-service/tests/test_integration_analytics.py -q`
  - 结果：`38 passed`
  - `PYTHONPATH=/home/kkk/Project/platform-sim/apps/core/domain-service:/home/kkk/Project/platform-sim pytest apps/core/domain-service/tests/test_odoo_seed_mapping.py apps/core/domain-service/tests/test_odoo_order_link_resolver.py apps/core/domain-service/tests/test_odoo_provider.py apps/core/domain-service/tests/test_integration_service_platform.py apps/core/domain-service/tests/test_integration_analytics.py -q`
  - 结果：`32 passed`
  - `PYTHONPATH=/home/kkk/Project/platform-sim/apps/core/domain-service:/home/kkk/Project/platform-sim pytest apps/core/domain-service/tests/test_odoo_provider.py apps/core/domain-service/tests/test_odoo_seed_mapping.py apps/core/domain-service/tests/test_odoo_order_link_resolver.py -q`
  - 结果：`23 passed`
  - `PYTHONPATH=/home/kkk/Project/platform-sim/apps/core/domain-service:/home/kkk/Project/platform-sim pytest apps/core/domain-service/tests/test_conversation_run_chain.py apps/core/domain-service/tests/test_context_bridge.py -q`
  - 结果：`5 passed`
  - `PYTHONPATH=/home/kkk/Project/platform-sim/apps/core/domain-service:/home/kkk/Project/platform-sim pytest apps/core/domain-service/tests/test_official_run_and_odoo_real.py apps/core/domain-service/tests/test_context_bridge.py -q`
  - 结果：`7 passed`
  - `PYTHONPATH=/home/kkk/Project/platform-sim/apps/sim/official-sim-server:. pytest apps/sim/official-sim-server/tests/test_raw_query.py -q`
  - 结果：`6 passed`
  - `PYTHONPATH=/home/kkk/Project/platform-sim/apps/sim/user-sim-service:/home/kkk/Project/platform-sim pytest apps/sim/user-sim-service/tests/test_conversation_studio_chain.py -q`
  - 结果：`3 passed`
  - `PYTHONPATH=/home/kkk/Project/platform-sim/apps/core/domain-service:/home/kkk/Project/platform-sim pytest apps/core/domain-service/tests/test_after_sale_chain.py apps/core/domain-service/tests/test_official_run_and_odoo_real.py apps/core/domain-service/tests/test_context_bridge.py -q`
  - 结果：`11 passed`
  - `PYTHONPATH=/home/kkk/Project/platform-sim/apps/sim/official-sim-server:/home/kkk/Project/platform-sim pytest apps/sim/official-sim-server/tests/test_raw_query.py -q`
  - 结果：`10 passed`
  - `PYTHONPATH=/home/kkk/Project/platform-sim/apps/core/domain-service:/home/kkk/Project/platform-sim pytest apps/core/domain-service/tests/test_after_sale_chain.py apps/core/domain-service/tests/test_official_run_and_odoo_real.py -q`
  - 结果：`9 passed`
  - `PYTHONPATH=/home/kkk/Project/platform-sim/apps/sim/official-sim-server:/home/kkk/Project/platform-sim pytest apps/sim/official-sim-server/tests/test_raw_query.py -q`
  - 结果：`18 passed`
  - `PYTHONPATH=/home/kkk/Project/platform-sim/apps/core/domain-service:/home/kkk/Project/platform-sim pytest apps/core/domain-service/tests/test_adapters.py apps/core/domain-service/tests/test_official_run_and_odoo_real.py apps/core/domain-service/tests/test_context_bridge.py -q`
  - 结果：`22 passed`
  - Lint：
  - `ruff check apps/core/domain-service/adapters/platform_adapter.py apps/core/domain-service/app/services/official_sim_provider.py apps/core/domain-service/tests/test_adapters.py apps/core/domain-service/tests/test_official_run_and_odoo_real.py`
  - 结果：通过
  - `ruff check --select I,F,F541 apps/sim/official-sim-server/app/api/routes/raw_query.py apps/sim/official-sim-server/tests/test_raw_query.py`
  - 结果：通过
  - `ruff check apps/core/domain-service/app/api/routes/integration.py apps/core/domain-service/app/services/integration_service.py apps/core/domain-service/tests/test_integration_service_platform.py apps/core/domain-service/tests/test_integration_analytics.py`
  - 结果：通过
  - `ruff check scripts/data_tools/odoo_seed_mapping.py scripts/data_tools/convert_to_odoo.py scripts/data_tools/import_to_odoo.py apps/core/domain-service/tests/test_odoo_seed_mapping.py`
  - 结果：通过
  - `ruff check providers/odoo/real/provider.py scripts/data_tools/odoo_seed_mapping.py scripts/data_tools/import_to_odoo.py scripts/data_tools/convert_to_odoo.py apps/core/domain-service/tests/test_odoo_provider.py apps/core/domain-service/tests/test_odoo_seed_mapping.py`
  - 结果：通过
  - `ruff check apps/core/domain-service/app/services/conversation_domain_service.py apps/core/domain-service/app/services/business_context_service.py apps/core/domain-service/app/services/recommendation_service.py apps/core/domain-service/tests/test_conversation_run_chain.py apps/core/domain-service/tests/test_context_bridge.py`
  - 结果：通过
  - `ruff check apps/core/domain-service/app/services/official_sim_provider.py apps/core/domain-service/tests/test_official_run_and_odoo_real.py apps/core/domain-service/tests/test_context_bridge.py`
  - 结果：通过
  - `ruff check --select F401,F821,F841,I001 providers/utils/sim_identity.py apps/sim/official-sim-server/app/api/routes/raw_query.py apps/sim/official-sim-server/tests/test_raw_query.py apps/core/domain-service/app/services/official_sim_provider.py apps/core/domain-service/app/services/platform_gateway_service.py apps/core/domain-service/app/services/after_sale_domain_service.py apps/core/domain-service/app/services/business_context_service.py apps/core/domain-service/app/services/recommendation_service.py apps/core/domain-service/tests/test_after_sale_chain.py apps/core/domain-service/tests/test_official_run_and_odoo_real.py`
  - 结果：通过
  - `ruff check --select F401,F821,F841,I001 apps/sim/official-sim-server/app/api/routes/raw_query.py apps/sim/official-sim-server/tests/test_raw_query.py apps/core/domain-service/app/services/official_sim_provider.py apps/core/domain-service/app/services/recommendation_service.py apps/core/domain-service/adapters/platform_adapter.py apps/core/domain-service/tests/test_official_run_and_odoo_real.py apps/core/domain-service/tests/test_context_bridge.py apps/core/domain-service/tests/test_adapters.py`
  - 结果：通过
  - `python -m compileall apps/sim/official-sim-server/app/api/routes/raw_query.py apps/core/domain-service/app/services/official_sim_provider.py apps/core/domain-service/app/services/recommendation_service.py apps/core/domain-service/adapters/platform_adapter.py`
  - 结果：通过
  - `PYTHONPATH=/home/kkk/Project/platform-sim/apps/core/domain-service:/home/kkk/Project/platform-sim pytest apps/core/domain-service/tests/test_official_run_and_odoo_real.py apps/core/domain-service/tests/test_conversation_run_chain.py apps/core/domain-service/tests/test_context_bridge.py apps/core/domain-service/tests/test_order_identity_fields.py apps/core/domain-service/tests/test_after_sale_chain.py -q`
  - 结果：`36 passed`
  - `PYTHONPATH=/home/kkk/Project/platform-sim/apps/sim/official-sim-server:/home/kkk/Project/platform-sim pytest apps/sim/official-sim-server/tests/test_raw_query.py -q`
  - 结果：`19 passed`
  - `ruff check --select F401,F821,F841,I001 apps/core/domain-service/app/services/official_sim_provider.py apps/core/domain-service/app/services/conversation_domain_service.py apps/core/domain-service/app/services/order_domain_service.py apps/core/domain-service/app/services/shipment_domain_service.py apps/core/domain-service/app/services/after_sale_domain_service.py apps/core/domain-service/app/services/business_context_service.py providers/utils/sim_identity.py apps/sim/official-sim-server/app/api/routes/raw_query.py apps/core/domain-service/tests/test_official_run_and_odoo_real.py apps/core/domain-service/tests/test_conversation_run_chain.py apps/core/domain-service/tests/test_context_bridge.py apps/core/domain-service/tests/test_order_identity_fields.py apps/sim/official-sim-server/tests/test_raw_query.py`
  - 结果：通过
  - `python -m compileall apps/core/domain-service/app/services/official_sim_provider.py apps/core/domain-service/app/services/conversation_domain_service.py apps/core/domain-service/app/services/order_domain_service.py apps/core/domain-service/app/services/shipment_domain_service.py apps/core/domain-service/app/services/after_sale_domain_service.py apps/core/domain-service/app/services/business_context_service.py providers/utils/sim_identity.py apps/sim/official-sim-server/app/api/routes/raw_query.py`
  - 结果：通过
  - `PYTHONPATH=/home/kkk/Project/platform-sim/apps/core/domain-service:/home/kkk/Project/platform-sim pytest apps/core/domain-service/tests/test_conversation_run_chain.py apps/core/domain-service/tests/test_context_bridge.py apps/core/domain-service/tests/test_after_sale_chain.py apps/core/domain-service/tests/test_official_run_and_odoo_real.py apps/core/domain-service/tests/test_order_identity_fields.py apps/core/domain-service/tests/test_odoo_seed_mapping.py -q`
  - 结果：`49 passed`
  - `PYTHONPATH=/home/kkk/Project/platform-sim/apps/sim/official-sim-server:/home/kkk/Project/platform-sim pytest apps/sim/official-sim-server/tests/test_raw_query.py -q`
  - 结果：`31 passed`
  - `ruff check --select F401,F821,F841,I001 apps/core/domain-service/app/services/conversation_domain_service.py apps/sim/official-sim-server/app/api/routes/raw_query.py providers/utils/fixture_loader.py providers/utils/sim_identity.py scripts/data_tools/odoo_seed_mapping.py apps/core/domain-service/tests/test_conversation_run_chain.py apps/core/domain-service/tests/test_order_identity_fields.py apps/core/domain-service/tests/test_odoo_seed_mapping.py apps/sim/official-sim-server/tests/test_raw_query.py`
  - 结果：通过
  - `python -m compileall apps/core/domain-service/app/services/conversation_domain_service.py apps/sim/official-sim-server/app/api/routes/raw_query.py providers/utils/fixture_loader.py providers/utils/sim_identity.py scripts/data_tools/odoo_seed_mapping.py`
  - 结果：通过
  - `python scripts/data_tools/import_to_odoo.py --backfill-existing-orders --sale-order-limit 500`
  - 结果：真实回填 `client_order_ref 54 条`，写入运行态映射 `54 条`

### Smoke

- 订单统一接口：
  - `GET /api/orders/douyin_shop/6912558345648290211` -> `total_amount=199.00`，`pay_amount=0.00`，商品单价 `99.00`
  - `GET /api/orders/jd/98765432101234` -> `total_amount=199.00`，`pay_amount=0.00`，receiver / products 正常
  - `GET /api/orders/taobao/12345678901234` -> 订单正常返回，`external_order_id` 为字符串
  - `GET /api/orders/xhs/XHS12345678901234` -> 订单正常返回
- run-aware 聚合：
  - `GET /api/orders/taobao/12345678901234?official_run_id=<wait_ship_run>` -> `status=wait_ship`
  - `GET /api/context/taobao/12345678901234?official_run_id=<wait_ship_run>` -> `data_sources.order_snapshot=official_sim_run`，且不再伪造 `after_sale_snapshot`，`source_errors.shipment_snapshot=Run shipment state not found`
  - `GET /api/shipments/taobao/12345678901234?official_run_id=<shipped_run>` -> 物流正常返回
  - `GET /api/after-sales/jd/98765432101234?official_run_id=<refund_flow_run>` -> `status=refunding`
- Odoo integration：
  - `GET /api/integration/inventory?product_id=PROD_001` -> 返回库存
  - `GET /api/integration/order-audits?order_id=ORDER_001` -> 返回审核快照
  - `GET /api/integration/order-exceptions?order_id=ORDER_001` -> 返回异常快照
  - `GET /api/integration/fulfillment?order_id=ORDER_001` -> 返回履约快照
- real Odoo smoke：
  - `GET /api/integration/inventory` -> 返回本机 Odoo `stock.quant` 实时数据
  - `GET /api/integration/inventory?product_id=30` -> 精确返回单个产品库存
  - `GET /api/integration/order-audits` -> 返回本机 Odoo `sale.order` 映射出的审核视图
  - `GET /api/integration/order-audits?order_id=24` -> 返回单条审核记录
  - `GET /api/integration/order-exceptions` -> 返回空列表，证明标准 Odoo 无 `sale.exception` 时已兼容
  - `GET /api/integration/fulfillment` -> 返回本机 Odoo `stock.picking` 映射结果
  - `GET /api/integration/fulfillment?order_id=S00024` -> 返回单条履约记录
  - `POST /api/context/build {"platform":"jd","biz_id":"98765432101234","biz_type":"order"}` -> 不再出现 Odoo 整数越界错误；当前仅保留 `shipment not found` 这一条平台侧缺失信号
  - `python scripts/data_tools/import_to_odoo.py --backfill-existing-orders --sale-order-limit 500` -> 本机 `olist_db` 已真实回填 28 条 `client_order_ref`，并为这 28 条映射订单补建最小 `stock.picking`
  - `data/runtime/odoo_order_links.json` -> 当前已清理历史 `unknown:*` 残留键，保留 28 条已知平台映射
  - `GET /api/integration/order-audits?order_id=98765432101234&platform=jd` -> 返回 `order_id=98765432101234`
  - `GET /api/integration/fulfillment?order_id=98765432101234&platform=jd` -> 返回 `picking_id=33`
  - `GET /api/integration/order-audits?order_id=12345678901234&platform=taobao` -> 返回 `order_id=12345678901234`
  - `GET /api/integration/fulfillment?order_id=12345678901234&platform=taobao` -> 返回 `picking_id=45`
  - `GET /api/integration/order-audits?order_id=6912558345648290211&platform=douyin_shop` -> 返回 `order_id=6912558345648290211`
  - `GET /api/integration/fulfillment?order_id=6912558345648290211&platform=douyin_shop` -> 返回 `picking_id=29`
  - 五平台售后 by-order real smoke：
    - `GET /official-sim/raw/after-sales/by-order/TB_ORDER_003?platform=taobao` -> `200`，返回 `after_sale_id=taobao:12345678901234:after_sale`，`status_text=退款中`
    - `GET /official-sim/raw/after-sales/by-order/12345678901234?platform=taobao` -> `200`，与 `TB_ORDER_003` 落到同一 canonical `after_sale_id`
    - `GET /official-sim/raw/after-sales/by-order/DS_ORDER_003?platform=douyin_shop` / `6912558345648290211` -> 都返回 `200`，canonical `after_sale_id=douyin_shop:6912558345648290211:after_sale`
    - `GET /official-sim/raw/after-sales/by-order/JD_ORDER_003?platform=jd` / `98765432101234` -> 都返回 `200`，canonical `after_sale_id=jd:98765432101234:after_sale`
    - `GET /official-sim/raw/after-sales/by-order/XHS_ORDER_003?platform=xhs` / `XHS12345678901234` -> 都返回 `200`
    - `GET /official-sim/raw/after-sales/by-order/KS_ORDER_003?platform=kuaishou` -> `200`
  - 五平台统一售后 / 推荐 real smoke：
    - `GET /api/after-sales/{platform}/by-order/{refund_order}` -> 5 平台都返回真实售后对象，不再是 `No after-sale found for this order`
    - `POST /api/recommendations/reply` with `intent=ask_refund` -> 5 平台都返回 `reply_type=after_sale_status`，文案从 `未知` 变成 `退款中`
  - 五平台订单 / 物流 / shipment 推荐 real smoke：
    - `GET /api/orders/taobao/12345678901234` -> `status=shipped`
    - `GET /api/orders/douyin_shop/6912558345648290211` -> `status=shipped`
    - `GET /api/orders/jd/98765432101234` -> `status=shipped`
    - `GET /api/orders/xhs/XHS12345678901234` -> `status=in_transit`
    - `GET /api/orders/kuaishou/KS12345678901235` -> `status=shipped`
    - `GET /api/shipments/{platform}/{public_order_id}` -> 五平台都返回 `200`，且 `tracking_no=SF1234567890`
    - `POST /api/recommendations/reply` with `intent=ask_shipment` -> 五平台都返回 `reply_type=shipment_info`，不再误落 `after_sale_status`
  - live run：
    - `POST /conversation-studio/runs` with `platform=wecom_kf` -> 创建 `run_id=cs_run_ba1af132`，绑定 `official_run_id=c35f87f1-1931-437a-a406-85d1333e5771`
    - 连续 `POST /conversation-studio/runs/cs_run_ba1af132/next` -> `reply_source=domain-service`，`official_current_step=1/2/3`
    - `GET /official-sim/raw/conversations/conv_live_wecom_001?...` -> 返回 run-aware 会话，`biz_platform=jd`，`message_count=4`
    - `GET /api/conversations/?platform=wecom_kf&status=active&limit=20` -> 返回同一条 `official_run_id`
    - `GET /api/shipments/jd/98765432101234` -> 返回 `status=shipped`，`company=顺丰速运`，`tracking_no=SF1234567890`
    - `GET /api/context/wecom_kf/JD_ORDER_003?official_run_id=<run>` -> 返回 `resolved_biz_reference: wecom_kf/JD_ORDER_003 -> jd/98765432101234`，并补出 `shipment_snapshot`
    - `POST /api/recommendations/reply` with `platform=wecom_kf,biz_id=JD_ORDER_003,intent=ask_order_status,official_run_id=<run>` -> 返回 `reply_type=order_status`，不再是 `general_greeting`
    - `POST /api/recommendations/reply` with `platform=wecom_kf,biz_id=JD_ORDER_003,intent=ask_shipment,official_run_id=<run>` -> 返回 `reply_type=shipment_info`，内容包含 `SF1234567890 / 顺丰速运`
    - 新 live run：
      - `POST /conversation-studio/runs` with `platform=wecom_kf,user_id=wecom_user_001,conversation_id=conv_live_wecom_stable_1775148362` -> 创建 `run_id=cs_run_dc09cd71`，绑定 `official_run_id=f937729e-cd9a-4fbb-ae84-fe65c9e4984b`
      - 连续两次 `POST /conversation-studio/runs/cs_run_dc09cd71/next` -> 两轮都返回 `order_id=JD_ORDER_003`
      - `GET /official-sim/raw/conversations/conv_live_wecom_stable_1775148362?...` -> `biz_id=JD_ORDER_003`，`external_biz_id=JD_ORDER_003`，`message_count=4`
    - `GET /api/context/wecom_kf/JD_ORDER_003?official_run_id=f937729e-cd9a-4fbb-ae84-fe65c9e4984b` -> `external_biz_id` 保持 `JD_ORDER_003`，并继续桥接到 `jd/98765432101234`
  - 五平台 alias / canonical ID live smoke：
  - 订单 alias 直查：
    - `GET /api/orders/taobao/TB_ORDER_003`
    - `GET /api/orders/douyin_shop/DS_ORDER_003`
    - `GET /api/orders/jd/JD_ORDER_003`
    - `GET /api/orders/xhs/XHS_ORDER_003`
    - `GET /api/orders/kuaishou/KS_ORDER_003`
  - 结果：都返回 `requested_order_id + external_order_id + canonical_order_id`
  - 物流 alias 直查：
    - `GET /api/shipments/taobao/TB_ORDER_002`
    - `GET /api/shipments/douyin_shop/DS_ORDER_002`
    - `GET /api/shipments/jd/JD_ORDER_001`
    - `GET /api/shipments/xhs/XHS_ORDER_002`
    - `GET /api/shipments/kuaishou/KS_ORDER_002`
  - 结果：都返回 `canonical_shipment_id`，并保持 `requested_order_id` 与 `external_order_id` 并存
  - `wecom_kf` 桥接：
    - `GET /api/context/wecom_kf/TB_ORDER_003`
    - `GET /api/context/wecom_kf/DS_ORDER_003`
    - `GET /api/context/wecom_kf/JD_ORDER_003`
    - `GET /api/context/wecom_kf/XHS_ORDER_003`
    - `GET /api/context/wecom_kf/KS_ORDER_003`
    - `GET /api/context/wecom_kf/KS_ORDER_002`
  - 结果：全部能解析到目标电商平台的 `effective_platform + effective_biz_id`，并返回统一 `canonical_order_id`；退款单会同步带回 `after_sale_id`
    - 售后桥接复测：
      - `GET /api/context/wecom_kf/JD_ORDER_003?official_run_id=225d176c-b192-40e1-91aa-d9e9c8f36355` -> `after_sale_snapshot.after_sale_id=jd:98765432101234:after_sale`，`status_text=退款中`，`source_errors=[]`
      - `POST /api/recommendations/reply` with `platform=wecom_kf,biz_id=JD_ORDER_003,intent=ask_refund,official_run_id=225d176c-b192-40e1-91aa-d9e9c8f36355` -> 返回 `reply_type=after_sale_status`，内容为 `退款中`
  - user fixture 唯一 external id / wecom 固定会话 live smoke：
    - `GET /api/orders/taobao/TB_ORDER_001` -> 返回 `order_id=12345678901231`，`requested_order_id=TB_ORDER_001`
    - `GET /api/orders/jd/JD_ORDER_001` -> 返回 `order_id=98765432101231`，`requested_order_id=JD_ORDER_001`
    - `GET /api/context/wecom_kf/CONV_WK_006` -> 解析到 `effective_platform=douyin_shop`，`effective_biz_id=6912558345648290202`，并返回对应订单 / 物流上下文
    - `GET /api/context/wecom_kf/CONV_WK_008` -> 解析到 `effective_platform=kuaishou`，`effective_biz_id=KS12345678901234`，`after_sale_snapshot.status_text=退款中`
    - `GET /official-sim/raw/shipments/KS12345678901234?platform=kuaishou` -> 返回 `404`，不再错误回落到另一单的默认 shipped fixture
    - `GET /api/integration/order-audits?order_id=12345678901231&platform=taobao` -> 返回 `order_id=12345678901231`
    - `GET /api/integration/fulfillment?order_id=12345678901231&platform=taobao` -> 返回 `picking_id=61`
    - `data/runtime/odoo_order_links.json` -> 当前已包含 `54` 条新 external id 映射

---

## 未决问题

- `apps/core/domain-service/app/core/config.py` 仍有 Pydantic v2 配置弃用告警，属于仓库既有技术债，不影响本轮系统修复可用性。
- 本轮只对关键修改文件做了 lint；仓库中仍存在较多历史风格告警，未在本轮统一清理。
- 当前本机 Odoo 是标准 Odoo 16 数据，不包含 `sale.exception` 这类项目定制模型；因此 real 模式下 `/api/integration/order-exceptions` 的“正常行为”是空列表，而不是 mock 中的伪造异常样本。
- 当前 real Odoo 的 `fulfillment` 语义来自 `stock.picking`，过滤键更接近拣货单 `id/name/origin`，不直接等价于平台外部订单号；这是现有 ERP 数据建模和平台单号之间的自然差异，不是本轮切换故障。
- 当前已经存在运行态稳定映射层 `providers/odoo/real/link_resolver.py`，所以“平台订单号完全没有稳定映射”这个旧说法已经不准确。
- `IntegrationService` 已经补齐 `platform` 透传，因此 `context` / `integration` 现在共享同一套运行态映射语义。
- Odoo 导数 / 导入链已经补上 `client_order_ref + platform_order_link_seed.json -> data/runtime/odoo_order_links.json` 这条映射资产链。
- 其他环境若已存在旧导入的 Odoo 数据，仍需显式执行 `python scripts/data_tools/import_to_odoo.py --backfill-existing-orders --sale-order-limit 500`；当前这台本机 `olist_db` 已经完成真实回填。
- 当前 user fixture 里的退款对象大多没有平台原生 `refund_id`，因此统一链返回的稳定主键是 canonical `after_sale_id`；`external_after_sale_id` 只有在 fixture / 官方 payload 本身提供真实外部售后号时才会非空。
- 当前公共平台订单号仍然更接近“按 query type 选取的场景样本键”，而不是一条严格单一真实订单的全生命周期主键；因此 `orders / shipments / after-sales` 虽然都已可查，但同一个公共订单号在不同 query type 下仍可能对应不同 fixture slice。
- 当前这轮已把 `requested_order_id + external_order_id + canonical_order_id` 三层语义收清，但 `taobao / douyin_shop / jd / xhs` 仍存在“多个 sim alias 共享同一个 official sample external order id”的历史现实；如果后续要做到真正一单到底，还需要继续扩充 fixture，让 external order id 不再复用。
- 更准确的关系定义应为：
  - `official-sim` 不直接模拟 Odoo API
  - Odoo 不直接生成平台官方 payload
  - 两者通过 `domain-service` 围绕 `platform + biz_id/order_id (+ official_run_id)` 汇合
- 当前剩余问题的详细任务拆分与执行顺序，已转移到：
  - `docs/reports/2026-04-04-remaining-issues-checklist.md`
- 2026-04-04 已完成根仓 pytest 第一轮治理：
  - `pytest.ini` 已限制为本仓测试目录，并显式隔离 `reference/omni-csx-v35/tests`
  - 三组测试已各自绑定 service root，解决多 `conftest.py` 与同名 `app` 包冲突
  - 根仓 `pytest -q` 已可完整执行；最新结果为 `46 failed, 679 passed, 42 warnings`
