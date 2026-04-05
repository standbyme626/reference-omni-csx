# 中台-模拟层全链路改造完成后预期

## 1. 文档目的

定义本次“中台为主、模拟层支撑”的改造完成态，明确：

- 全链路数据流应如何工作
- 各服务边界与职责
- 前后端接口契约一致性要求
- 什么状态算“真正接上”，什么不算

---

## 2. 目标完成态（一句话）

`user-sim` 只负责编排对话与驱动场景，`official-sim` 只负责官方事实与状态推进，`domain-service` 负责统一业务上下文与推荐；三者通过 `run_id` 贯穿并可回放、可审计、可评估。

---

## 3. 全链路目标数据流（改好后）

### 阶段 1：初始化

1. `user-sim -> official-sim`：`POST /official-sim/runs`
2. `official-sim -> user-sim`：返回 `official_run_id`
3. `user-sim` 本地创建 `user_sim_run_id`，并保存映射关系：
   - `user_sim_run_id`
   - `official_run_id`
   - `platform`
   - `scenario_name`

### 阶段 2：用户消息生成

1. `user-sim` 生成用户消息（每条消息必须带 `official_run_id` 和 `turn_no`）
2. `user-sim -> official-sim`：写入用户消息 artifact（`user_message_payload`）

### 阶段 3：业务处理

1. `user-sim -> domain-service`：传入 `platform + biz_id(order_id/conv_id) + official_run_id`
2. `domain-service -> official-sim`：查询订单/物流/售后/会话事实
3. `domain-service` 构建 `BusinessContext`
4. `domain-service` 生成回复建议/动作建议
5. `domain-service -> user-sim`：返回候选回复（含来源、置信度、上下文ID）

### 阶段 4：记录

1. `user-sim -> official-sim`：写入对话轮次 artifact（`conversation_turn`）
2. `user-sim -> official-sim`：写入推荐结果 artifact（`reply_recommendation_payload`）

### 阶段 5：状态推进

1. `user-sim -> official-sim`：`POST /official-sim/runs/{run_id}/advance`
2. `official-sim` 落库：
   - `simulation_events`
   - `state_snapshots`
   - `push_events`
3. `domain-service` 对新状态可见（P0 可先拉取，P1 再做主动通知）

### 阶段 6：评估

1. `user-sim -> official-sim`：`GET /official-sim/runs/{run_id}/report`
2. 合并输出：
   - 仿真状态报告（steps/artifacts/push/errors）
   - 对话质量报告（满意度、升级率、失败原因）

---

## 4. 服务边界（必须遵守）

- `official-sim-server`
  - 负责：run 生命周期、状态机、fixtures 真相、artifact/push/snapshot/report
  - 不负责：业务推荐策略
- `domain-service`
  - 负责：统一领域模型、上下文聚合、推荐与风控质检
  - 不负责：伪造平台官方事实
- `user-sim-service`
  - 负责：对话编排、用户行为模拟、调用中台与仿真层
  - 不负责：持有官方真相

---

## 5. 接口契约预期（改好后）

## 5.1 domain-service 对前端统一返回

所有 `/api/*` 统一 envelope：

```json
{
  "code": "0",
  "message": "success",
  "data": {},
  "request_id": "..."
}
```

## 5.2 run 贯穿字段（新增约定）

- 请求头或请求体必须可携带：`official_run_id`
- `domain-service` 在日志中记录：`official_run_id`、`platform`、`biz_id`
- `user-sim` 对每轮消息记录：`run_id + turn_no + intent + emotion`

## 5.3 错误语义

- 资源不存在必须返回 `404`（不能静默回退为伪数据）
- `official_sim` 模式默认严格，不可达时直接报错
- 回退到本地 mock 仅允许在显式开关开启时生效

---

## 6. 完成后“可观察结果”（你可以直接验）

1. 创建一次会话后，能拿到 `official_run_id`
2. 同一 run 每推进一步，`events/snapshots/artifacts/pushes` 数量增长
3. 对不存在的订单/售后/物流查询，稳定返回 `404`
4. 前端调用 `context/recommendations` 响应结构一致（统一 envelope）
5. 能从 run 维度导出完整报告，且可定位每一轮对话和对应建议

---

## 7. P0 验收清单（当前状态）

- [x] `user-sim` 创建 run 时真实调用 `official-sim /runs`
- [x] `official_run_id` 从 user-sim 传到 domain-service 并进入日志
- [x] `user_message`、`conversation_turn`、`reply_recommendation` 三类 artifact 可查询
- [x] `advance` 后 `snapshot` 与 `push_event` 可查询
- [x] `report` 可输出 `total_steps/total_artifacts/total_pushes/total_errors`
- [x] domain-service 在严格模式下不存在资源返回 `404`
- [x] `apps/core/domain-service/tests` 全通过（80 passed）

---

## 7.5 P1 验收清单（主动通知）

- [x] official-sim 新增 push 配置：`PUSH_DOMAIN_SERVICE_URL` / `PUSH_TIMEOUT_S` / `PUSH_MAX_RETRIES`
- [x] `PushNotifier` 类：同步 httpx 分发 + 内联重试
- [x] `/advance` 在产生 push 事件时自动向 domain-service 推送
- [x] push 发送成功时状态更新为 `ACKED`，失败时为 `FAILED`
- [x] domain-service 新增 `POST /api/push-events` 接收推送，返回 `{"status": "ack"}`
- [x] domain-service 新增 `GET /api/push-events` 查询收到的推送
- [x] domain-service 新增 `PushEventTracker`（线程安全内存存储）
- [x] push_notifier 测试 7 passed, push_events 测试 10 passed
- [x] 所有原有测试未退化

---

## 7.6 P2 验收清单（完善闭环）

- [x] 六平台 `scenario_engine` 全覆盖：jd/xhs/kuaishou push 接入 `_handle_order_step`
- [x] `PLATFORM_PUSH_EVENT_TYPES` 统一映射表：定义五个电商平台的 action→event_type
- [x] `push_enabled` 字段落实：advance 时读取 `run.push_enabled`，为 `"0"` 时跳过 push 创建和分发
- [x] domain-service `get_context` 消费推送：`_get_push_events()` + `_apply_push_state()` 将推送数据融入上下文
- [x] order_snapshot / shipment_snapshot 被推送数据动态更新（status、物流信息）
- [x] push-based refund detection: `push_refund_detected` 字段标记退款推送
- [x] BusinessContextService 新增 `push_event_tracker` 依赖，由 DI 注入
- [x] 所有原有测试未退化（domain-service 80 passed, official-sim 26 passed）

---

## 8. 非目标（本阶段不做）

- 不做真实平台 API 对接
- 不做 MQ/Kafka 重基础设施
- 不做主动 webhook 分发的生产级重试机制（P1 再做）
- 不做全平台 100% 字段拟真

---

## 9. 风险与回滚策略

- 风险：服务未按顺序启动导致“看似无数据”
  - 规避：先启 official-sim，再启 domain-service，再启 user-sim
- 风险：接口变更导致前端读取失败
  - 规避：保持 envelope 不变，新增字段只加不删
- 回滚：通过环境变量切回 `mock` 或开启 fallback（仅临时）
