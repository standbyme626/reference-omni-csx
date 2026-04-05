# 剩余问题与收尾修复清单（2026-04-04）

## 目标

本清单用于把当前仓库里“主链已通但尚未完全收口”的问题集中整理出来，并作为后续逐项修复的跟踪文档。

范围包括：

- `user-sim-service`
- `official-sim-server`
- `domain-service`
- `providers/*`
- `scripts/data_tools/*`
- 根仓测试 / lint / 打包治理

不包括：

- `reference/omni-csx-v35/` 的代码重构或补依赖
- 与本仓当前主链无关的历史 demo / legacy 代码清理

---

## 当前总体判断

当前不是“主链没通”，而是“主链已通，但工程治理、样本厚度、严格性和默认配置还没完全收口”。

已经打通：

- 五电商平台 `orders / shipments / after-sales`
- `wecom_kf -> biz_platform` 会话桥接
- `user-sim -> official-sim -> domain-service` 运行态事实链
- live Odoo `client_order_ref + runtime links` 回填

还没完全收口：

- 默认配置和兜底策略仍允许退回 `mock / stub`
- fixture 还没做到严格一单到底
- `quality / risk / analytics / operations` 仍大量使用规则或兼容样本
- 根仓 `pytest -q` 已可完整执行，但仍有真实失败未清零
- 整仓 `ruff check` 还不能直接绿

---

## 执行方式

本轮开始采用两条执行约束：

1. `bd` 任务跟踪
   - 已在当前仓库初始化独立 beads 库：`.beads/`
   - 总控 epic：`platform-sim-1ir`
   - 顶层任务：
     - `platform-sim-1ir.1` `M组：主链严格性与默认配置收口`
     - `platform-sim-1ir.2` `N组：五平台全生命周期一单到底`
     - `platform-sim-1ir.3` `O组：用户问题类型扩样本`
     - `platform-sim-1ir.4` `P组：中台非主链模块真实化`
     - `platform-sim-1ir.5` `Q组：测试体系与打包治理`
     - `platform-sim-1ir.6` `R-S组：代码质量、旧适配层与历史技术债治理`
   - 当前已认领首个执行任务：
     - `platform-sim-1ir.1.1` `M1：禁止 user-sim 默认联调模式静默回退 stub`
2. MCP-first 代码阅读
   - 当前仓库可用的 MCP 以 `loco_explorer` 为主：
     - `list_project_files`
     - `search_code`
     - `read_file_excerpt`
     - `summarize_for_change`
   - 当前未发现额外可直接读取项目数据的通用 MCP resource server，因此后续主要使用 `loco_explorer` 做局部检索和验证

---

## 任务清单

### L. 剩余问题盘点与文档化

- [x] L1. 重新盘点当前已通主链与未通项，避免把已修复问题重复计入待办
- [x] L2. 扫描仓库中的 `NotImplementedError / fallback / stub / compat_data`，识别非主链但仍未完成的模块
- [x] L3. 运行根仓 `pytest -q`，确认当前是否存在测试收集级别问题
- [x] L4. 运行整仓 `ruff check`，确认当前代码质量债规模
- [x] L5. 新建本清单文档，并把当前问题按优先级分类

### M. 主链严格性与默认配置收口

- [x] M1. 禁止 `user-sim` 在默认联调模式下静默回退到 `stub`
- [x] M2. 明确区分“显式允许 fallback 的 demo 模式”和“严格验链模式”
- [x] M3. 将 `domain-service` 默认 Odoo 模式从 `mock` 调整为显式配置或 `real`
- [x] M4. 对 `official_sim_enable_mock_fallback` 增加更严格的环境约束与文档说明
- [x] M5. 为“严格模式下失败必须显式报错”补集成测试

### N. 五平台全生命周期一单到底

- [ ] N1. 清理公共平台订单号仍按 query type 选样本的问题，建立“一条公共订单号对应一条完整生命周期”
- [ ] N2. 消除 `taobao / douyin_shop / jd / xhs` 中多个 alias 共享同一 external order id 的历史复用
- [ ] N3. 为每个平台补齐从订单到物流到售后的统一主键贯通测试
- [ ] N4. 为 `wecom_kf` 固定会话补齐到五平台的“一单到底”桥接回归
- [ ] N5. 对 Odoo seed / runtime link 做一次与完整 fixture 集的重新校验

### O. 用户问题类型扩样本

- [ ] O1. 在现有 `ask_order_status / ask_shipment / ask_refund` 之外，补充投诉类问题
- [ ] O2. 补充改地址 / 催发货 / 拒收 / 部分退款 / 换货 / 审核进度等问题类型
- [ ] O3. 为五平台分别补齐至少一组“平台特有问题”固定会话样本
- [ ] O4. 让 `user-sim` 多平台 run 模板覆盖这些问题类型，而不是只靠固定 fixture 会话
- [ ] O5. 再做一次“五平台 x 多问题类型”的真实联调 smoke

### P. 中台非主链模块真实化

- [ ] P1. 让 `analytics` 从运行态事实和聚合结果出数，不再主要依赖场景枚举推导
- [ ] P2. 让 `quality` 结果列表和告警列表脱离 `compat_data` 静态样本
- [ ] P3. 让 `risk` 案例、黑名单、规则命中结果逐步脱离 `compat_data`
- [ ] P4. 让 `operations` 的风险旗标、审计日志、跟进任务脱离内存常量
- [ ] P5. 评估 `customers / kb / management` 路由哪些继续保留兼容样本，哪些需要接真实运行态

### Q. 测试体系与打包治理

- [x] Q1. 收口根仓 `pytest` 配置，避免默认收集到 `reference/omni-csx-v35/tests`
- [x] Q2. 为根仓测试补统一 `pythonpath / testpaths` 策略，消除 `ModuleNotFoundError: app/providers/scripts`
- [x] Q3. 解决 `official-sim` 与 `user-sim` 双 `conftest.py` 引发的 pytest plugin 冲突
- [ ] Q4. 让 `official-sim` 测试不强依赖本地 Postgres `official_sim`
- [x] Q5. 定义并固化“根仓可执行的标准测试命令”
- [x] Q6. 对 `reference/omni-csx-v35` 的测试做显式隔离或独立运行说明

### R. 代码质量与历史技术债

- [ ] R1. 清理根仓 `ruff check` 当前暴露的 600+ 问题
- [ ] R2. 修复 `apps/sim/user-sim-service/setup.py` 文件内容实际为 TOML 的错误
- [ ] R3. 修复 `scripts/data_tools/convert_to_chinese.py` 中重复字典键的静默覆盖风险
- [ ] R4. 逐步清理 `E402 / F401 / F841 / I001` 等广泛存在的历史风格问题
- [ ] R5. 修复 `apps/core/domain-service/app/core/config.py` 的 Pydantic v2 弃用配置写法

### S. 旧适配层与未实现接口治理

- [ ] S1. 评估 `app/adapters/platform_adapters.py` 是否仍为有效主链，避免保留大量半实现旧路径
- [ ] S2. 若保留旧适配层，则补齐 `shipment / refund / conversation` 的适配实现
- [ ] S3. 若旧适配层不再作为主链，则在文档和代码结构上明确降级或清理
- [ ] S4. 复核 `providers/*/provider.py` 中的 `NotImplementedError` 是否都符合平台能力边界

---

## 问题明细

### 1. 主链严格性问题

1. `user-sim` 仍会在 `official-sim` 失败或缺少订单时回退到 `stub`。
   - 证据：
     - `apps/sim/user-sim-service/nodes/reply/unified.py`
     - `apps/sim/user-sim-service/nodes/reply/official_sim.py`
2. `domain-service` 默认 Odoo 模式仍是 `mock`。
   - 证据：
     - `apps/core/domain-service/app/core/config.py`
3. `official_sim_enable_mock_fallback` 仍是可配置 fallback 开关，环境默认行为还需要进一步收紧。
   - 证据：
     - `apps/core/domain-service/app/services/platform_gateway_service.py`

### 2. 全生命周期一致性问题

1. 公共平台订单号仍更接近“场景样本键”，不是严格唯一的全生命周期订单主键。
2. `taobao / douyin_shop / jd / xhs` 仍存在 alias 共享 official sample external order id 的历史现实。
3. 五平台虽然已经能查 `orders / shipments / after-sales`，但 fixture 仍需继续扩成严格的一单到底样本。

对应背景已记录在：

- `docs/reports/2026-04-02-system-fix-checklist.md`
- `docs/reports/2026-04-03-five-platform-lifecycle-audit.md`

### 3. 问题类型覆盖不足

当前稳定跑通的问题类型主要是：

- `ask_order_status`
- `ask_shipment`
- `ask_refund`

尚未系统补齐：

- 投诉
- 改地址
- 催发货
- 拒收
- 部分退款
- 换货
- 平台审核 / 平台特有异常

### 4. 中台非主链模块仍偏样本化

1. `analytics` 仍大量依赖场景枚举推导。
   - 证据：`apps/core/domain-service/app/services/analytics_service.py`
2. `quality / risk` 目前是规则引擎 + 样本列表，不是 run-aware 历史沉淀。
   - 证据：
     - `apps/core/domain-service/app/services/quality_service.py`
     - `apps/core/domain-service/app/services/risk_service.py`
3. `operations` 路由中的风险旗标 / 审计日志 / 跟进任务仍是内存常量。
   - 证据：`apps/core/domain-service/app/api/routes/operations.py`
4. `customers / kb / management` 多处仍依赖 `compat_data`。
   - 证据：`apps/core/domain-service/app/services/compat_data.py`

### 5. 测试体系问题

2026-04-04 已完成两轮实测：

- 首轮命令：`pytest -q`
- 首轮结果：`74 errors during collection`
- 二轮命令：`pytest -q`
- 二轮结果：`46 failed, 679 passed, 42 warnings in 64.62s`

已收口：

1. 根仓 `pytest.ini` 已补 `testpaths`，并用 `norecursedirs = reference` 隔离参考项目测试。
2. `apps/core/domain-service/tests/conftest.py` 已新增服务级导入激活逻辑，消除根仓级 `app / providers / scripts` 收集报错。
3. `apps/sim/official-sim-server/tests/conftest.py` 与 `apps/sim/user-sim-service/tests/conftest.py` 已改成各自 service root 激活，并删除空 `tests/__init__.py`，解决 plugin 冲突。
4. 需要顶层懒加载 `app` / dependency symbol 的测试文件已调整，避免多服务同名 `app` 包在根仓执行时互相污染。

当前剩余失败已从“测试治理问题”收敛成“真实测试失败”，主要分三簇：

1. `official-sim` 用户 fixture 缺少 `fixture_type / metadata.version` 等 schema 字段。
2. `official-sim` 中仍有一批历史测试假设 `/official-sim/unified/*` 和“禁用 `/official-sim/query/*`”路由，这与当前实现不一致。
3. `user-sim` 还剩少量真实行为断言不匹配，例如快手物流意图识别与绑定订单文案。

### 6. 代码质量与打包问题

2026-04-04 实测根仓：

- 命令：`ruff check apps/core/domain-service apps/sim/official-sim-server apps/sim/user-sim-service providers scripts/data_tools`
- 结果：`Found 602 errors`

代表性问题：

1. 大量未使用 import / 变量、E402、I001。
2. `apps/sim/user-sim-service/setup.py` 实际是 TOML 内容，文件命名错误。
3. `scripts/data_tools/convert_to_chinese.py` 存在大量重复字典键，带来静默覆盖风险。
4. `apps/core/domain-service/app/core/config.py` 仍有 Pydantic v2 弃用告警。

### 7. 旧适配层半实现问题

`apps/core/domain-service/app/adapters/platform_adapters.py` 中多个平台的：

- `to_unified_shipment`
- `to_unified_refund`
- `to_unified_conversation`

仍是 `NotImplementedError`。

当前主链多数通过新的统一服务层和 provider 归一化路径绕开了这层，所以不构成立刻断链；但它仍然是明确的历史半实现代码。

---

## 已完成的本轮记录

- [x] 完成代码扫描：
  - `NotImplementedError / fallback / compat_data / stub`
- [x] 完成根仓测试收集检查：
  - `pytest -q`
- [x] 完成整仓 lint 债扫描：
  - `ruff check apps/core/domain-service apps/sim/official-sim-server apps/sim/user-sim-service providers scripts/data_tools`
- [x] 将剩余问题整理成按优先级可执行清单
- [x] 在当前仓库初始化 `bd`，并创建与 `M-S` 分组对齐的顶层任务与首个执行子任务
- [x] 完成 `M1 / M2 / M5` 第一轮收口：
  - 默认严格模式不再静默回退 `stub`
  - 显式 `allow_stub_fallback=true` 才允许 demo/兼容模式
  - 严格模式失败现在返回显式 `502`
- [x] 完成 `M3`：
  - `domain-service` 默认 Odoo 模式改为 `real`
  - `get_odoo_provider()` 不再错误回退到 `default_provider_mode`
- [x] 完成 `M4`：
  - `OFFICIAL_SIM_ENABLE_MOCK_FALLBACK` 现在仅 `development` 环境有效
  - `staging / production` 下即使显式打开也不会注入本地 mock fallback

---

## 修改记录

- 2026-04-04：
  - 新建本清单 `docs/reports/2026-04-04-remaining-issues-checklist.md`
  - 汇总当前剩余问题，拆成 `M-S` 六组任务：
    - 主链严格性
    - 全生命周期一致性
    - 用户问题扩样本
    - 中台非主链真实化
    - 测试体系治理
    - 代码质量与旧适配层治理
  - 记录本轮真实扫描结果：
    - 根仓 `pytest -q` -> `74 errors during collection`
    - 整仓 `ruff check ...` -> `602 errors`
  - 初始化 `bd`：
    - `bd init`
    - 创建总控 epic：`platform-sim-1ir`
    - 创建顶层任务：`platform-sim-1ir.1` ~ `platform-sim-1ir.6`
    - 认领首个任务：`platform-sim-1ir.1.1`
  - 明确后续采用 `loco_explorer` 的 MCP-first 代码阅读方式
  - 完成 `M1 / M2 / M5` 第一轮实现：
    - 修改文件：
      - `apps/sim/user-sim-service/nodes/reply/base.py`
      - `apps/sim/user-sim-service/nodes/reply/unified.py`
      - `apps/sim/user-sim-service/nodes/conversation_studio.py`
      - `apps/sim/user-sim-service/api/routes/conversation_studio.py`
      - `apps/sim/user-sim-service/tests/test_official_sim_reply_adapter.py`
      - `apps/sim/user-sim-service/tests/test_conversation_studio_chain.py`
    - 修改目的：
      - 默认联调模式下禁止 `official-sim` 失败后静默回退 `stub`
      - 新增显式兼容开关 `allow_stub_fallback`
      - 将严格模式下的回复失败统一抛成 `ReplyAdapterError -> HTTP 502`
      - 在 debug 接口中把模式区分为 `official-sim-strict` 和 `official-sim+stub-fallback`
    - 验证命令：
      - `PYTHONPATH=/home/kkk/Project/platform-sim/apps/sim/user-sim-service:/home/kkk/Project/platform-sim pytest apps/sim/user-sim-service/tests/test_official_sim_reply_adapter.py apps/sim/user-sim-service/tests/test_conversation_studio_chain.py -q`
      - `ruff check --select F401,F821,F841,I001 apps/sim/user-sim-service/nodes/reply/base.py apps/sim/user-sim-service/nodes/reply/unified.py apps/sim/user-sim-service/nodes/conversation_studio.py apps/sim/user-sim-service/api/routes/conversation_studio.py apps/sim/user-sim-service/tests/test_official_sim_reply_adapter.py apps/sim/user-sim-service/tests/test_conversation_studio_chain.py`
      - `python -m compileall apps/sim/user-sim-service/nodes/reply/base.py apps/sim/user-sim-service/nodes/reply/unified.py apps/sim/user-sim-service/nodes/conversation_studio.py apps/sim/user-sim-service/api/routes/conversation_studio.py`
    - 验证结果：
      - `10 passed`
      - `All checks passed!`
      - `compileall` 通过
  - 完成 `M3`：
    - 修改文件：
      - `apps/core/domain-service/app/core/config.py`
      - `apps/core/domain-service/app/dependencies.py`
      - `apps/core/domain-service/README.md`
      - `apps/core/domain-service/tests/test_dependencies_odoo_mode.py`
    - 修改目的：
      - 将 `domain-service` 的 Odoo 默认模式从 `mock` 改为 `real`
      - 取消 `get_odoo_provider()` 对 `default_provider_mode` 的错误耦合
      - 用测试锁定“未显式配置时默认 real、显式 mock 时仍可切 mock”
    - 验证命令：
      - `PYTHONPATH=/home/kkk/Project/platform-sim/apps/core/domain-service:/home/kkk/Project/platform-sim pytest apps/core/domain-service/tests/test_dependencies_odoo_mode.py apps/core/domain-service/tests/test_integration_analytics.py -q`
      - `ruff check --select F401,F821,F841,I001 apps/core/domain-service/app/core/config.py apps/core/domain-service/app/dependencies.py apps/core/domain-service/tests/test_dependencies_odoo_mode.py`
      - `python -m compileall apps/core/domain-service/app/core/config.py apps/core/domain-service/app/dependencies.py`
    - 验证结果：
      - `13 passed, 1 warning`
      - `All checks passed!`
      - `compileall` 通过
  - 完成 `M4`：
    - 修改文件：
      - `apps/core/domain-service/app/services/platform_gateway_service.py`
      - `apps/core/domain-service/README.md`
      - `apps/core/domain-service/tests/test_registry_gateway.py`
    - 修改目的：
      - 收紧 `official_sim_enable_mock_fallback` 的生效范围
      - 明确只有 `development` 环境允许 official-sim 不可达时注入本地 mock provider
      - 用测试锁定开发环境开启、非开发环境禁用的行为
    - 验证命令：
      - `PYTHONPATH=/home/kkk/Project/platform-sim/apps/core/domain-service:/home/kkk/Project/platform-sim pytest apps/core/domain-service/tests/test_registry_gateway.py -q`
      - `ruff check --select F401,F821,F841,I001 apps/core/domain-service/app/services/platform_gateway_service.py apps/core/domain-service/tests/test_registry_gateway.py`
      - `python -m compileall apps/core/domain-service/app/services/platform_gateway_service.py`
    - 验证结果：
      - `15 passed, 1 warning`
      - `All checks passed!`
      - `compileall` 通过
  - 完成 `Q1 / Q2 / Q3 / Q5 / Q6`：
    - 修改文件：
      - `pytest.ini`
      - `apps/core/domain-service/tests/conftest.py`
      - `apps/sim/official-sim-server/tests/conftest.py`
      - `apps/sim/user-sim-service/tests/conftest.py`
      - `apps/core/domain-service/tests/test_api.py`
      - `apps/core/domain-service/tests/test_push_events.py`
      - `apps/core/domain-service/tests/test_after_sale_chain.py`
      - `apps/core/domain-service/tests/test_integration_analytics.py`
      - `apps/sim/official-sim-server/tests/test_router.py`
    - 删除文件：
      - `apps/core/domain-service/tests/__init__.py`
      - `apps/sim/official-sim-server/tests/__init__.py`
      - `apps/sim/user-sim-service/tests/__init__.py`
    - 修改目的：
      - 限定根仓默认测试收集边界，显式隔离 `reference/omni-csx-v35/tests`
      - 为三组测试绑定各自 service root，解决多 `conftest.py` 与同名 `app` 包冲突
      - 把根仓标准测试命令收口为 `pytest -q`
    - 验证命令：
      - `pytest apps/core/domain-service/tests/test_registry_gateway.py apps/sim/official-sim-server/tests/test_router.py apps/core/domain-service/tests/test_api.py apps/core/domain-service/tests/test_push_events.py apps/core/domain-service/tests/test_after_sale_chain.py apps/core/domain-service/tests/test_integration_analytics.py -q`
      - `pytest -q`
    - 验证结果：
      - 混合集 smoke：仅剩 `official-sim` 两条过期路由断言失败，不再有导入/收集级错误
      - 根仓：`46 failed, 679 passed, 42 warnings in 64.62s`
      - 剩余失败已确认不是测试治理问题，主要落在 fixture schema、过期路由断言和少量 user-sim 行为断言

---

## 后续执行规则

1. 后续每完成一项，直接在本清单打勾。
2. 每次打勾必须同时补：
   - 修改文件
   - 修改目的
   - 验证命令
   - 验证结果
3. 不允许只勾选、不记录证据。
4. 优先顺序固定为：
   - `M 主链严格性`
   - `Q 测试体系`
   - `N 全生命周期一单到底`
   - `O 用户问题扩样本`
   - `P 中台非主链真实化`
   - `R / S 技术债与旧路径治理`
