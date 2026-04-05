# 五个电商平台生命周期与用户问题审计（2026-04-03）

## 1. 目标与范围

本报告只盘点 5 个电商平台：

- `taobao`
- `douyin_shop`
- `jd`
- `xhs`
- `kuaishou`

明确排除：

- `wecom_kf`

原因：

- `wecom_kf` 是会话平台，不是电商订单平台
- 它承载的是 `conversation-first` 链路，而不是订单/物流/售后主数据本体

本次审计目标：

1. 盘清 5 个电商平台当前已有的订单 / 物流 / 售后生命周期覆盖面。
2. 盘清平台用户会出现的典型问题类型。
3. 对统一接口和推荐链做一轮真实 smoke，确认哪些链路已经可用，哪些仍然是假通或未打通。

---

## 2. 审计方法

本次审计基于三类输入：

1. 仓库 fixture 目录：
   - `apps/sim/official-sim-server/fixtures/{platform}/success`
   - `apps/sim/official-sim-server/fixtures/{platform}/users`
2. 中台统一能力定义：
   - [Platform_Matrix.md](/home/kkk/Project/platform-sim/docs/specs/Platform_Matrix.md)
   - [domain-service.md](/home/kkk/Project/platform-sim/docs/architecture/domain-service.md)
3. 本机 live 服务 smoke：
   - `domain-service :8000`
   - `official-sim-server :8001`
   - `user-sim-service :8002`

实际执行的检查：

- 扫描 5 平台 `success` fixture 名称
- 扫描 5 平台 `users` fixture 中的订单状态 / 物流状态 / 退款状态
- 调用统一接口：
  - `GET /api/orders/{platform}/{order_id}`
  - `GET /api/shipments/{platform}/{order_id}`
  - `GET /api/after-sales/{platform}/by-order/{order_id}`
  - `GET /api/context/{platform}/{order_id}`
- 调用推荐接口：
  - `ask_order_status`
  - `ask_shipment`
  - `ask_refund`

---

## 3. 平台生命周期矩阵

### 3.1 Taobao

- 订单生命周期：
  - `trade_wait_pay`
  - `trade_wait_ship`
  - `trade_shipped`
  - `trade_buyer_signed`
  - `trade_finished`
  - `trade_closed`
  - `trade_closed_by_taobao`
  - `trade_no_create_pay`
- 售后生命周期：
  - `refund_requested`
  - `refund_wait_seller_confirm`
  - `refund_wait_buyer_return`
  - `refund_seller_refuse`
  - `refund_refunded`
  - `refund_closed`
  - `refund_no_refund`
- 用户订单侧状态样本：
  - `WAIT_SELLER_SEND_GOODS`
  - `WAIT_BUYER_CONFIRM_GOODS`
  - `TRADE_BUYER_SIGNED`
  - `TRADE_FINISHED`
  - `TRADE_CLOSED`
  - `TRADE_REFUNDING`

### 3.2 Douyin Shop

- 订单生命周期：
  - `order_created`
  - `order_paid`
  - `order_shipped`
  - `order_confirmed`
  - `order_fulfilled`
  - `order_completed`
  - `order_cancelling`
  - `order_cancelled`
- 售后生命周期：
  - `refund_applied`
  - `refund_approved`
  - `refund_rejected`
  - `refund_completed`
- 用户订单侧状态样本：
  - `30`
  - `100`
  - `300`
  - `400`
  - `700`

### 3.3 JD

- 订单 / 物流生命周期：
  - `order_wait_pay`
  - `order_pay_confirming`
  - `order_paid`
  - `order_shipped`
  - `order_delivering`
  - `order_station_received`
  - `order_wait_self_pickup`
  - `order_jd_received`
  - `order_seller_received`
  - `order_delivered`
  - `order_finished`
  - `order_created`
- 售后生命周期：
  - `refund_applied`
- 用户订单侧状态样本：
  - `paid`
  - `shipped`
  - `delivered`
  - `completed`
  - `cancelled`
  - `refunding`

### 3.4 XHS

- 订单生命周期：
  - `order_created`
  - `order_paid`
  - `order_partial_shipped`
  - `order_delivering`
  - `order_customs_clearing`
  - `order_completed`
  - `order_closed`
  - `order_cancelled`
  - `order_exchanging`
- 售后生命周期：
  - `refund_applied`
- 用户订单侧状态样本：
  - `paid`
  - `delivering`
  - `completed`
  - `cancelled`
  - `refunding`

### 3.5 Kuaishou

- 订单生命周期：
  - `order_wait_pay`
  - `order_created`
  - `order_paid`
  - `order_confirmed`
  - `order_delivered`
  - `order_cancelled`
- 售后生命周期：
  - `refund_applied`
  - `refund_rejected`
- 用户订单侧状态样本：
  - `paid`
  - `shipped`
  - `delivered`
  - `cancelled`
  - `refunding`

---

## 4. 平台差异结论

### 4.1 生命周期细度差异

- `taobao` 的逆向售后最细，卖家确认、买家退货、拒绝、关闭都已拆开。
- `jd` 的物流链最细，包含站点签收、自提、卖家签收等中间态。
- `xhs` 有明显的平台特有态：`customs_clearing`、`partial_shipped`、`exchanging`。
- `douyin_shop` 订单/退款相对平衡，取消和退款审核链较清楚。
- `kuaishou` 当前覆盖最薄，更像“基础订单 + 基础退款”。

### 4.2 用户问题类型差异

从用户 fixture 和推荐链角度，5 个电商平台当前都至少需要覆盖三类高频问题：

1. 订单状态问题
   - 未付款
   - 待发货
   - 已发货 / 运输中
   - 已完成 / 已取消
2. 物流问题
   - 有没有发货
   - 运单号是多少
   - 当前物流节点是什么
3. 售后问题
   - 已申请退款，当前是否在处理中
   - 是否被拒绝
   - 是否已退款完成

平台专属问题：

- `taobao`：卖家是否同意退款、是否需要买家退货
- `jd`：配送站、京东自提、签收节点
- `xhs`：报关 / 海关清关、换货
- `douyin_shop`：取消中 / 审核中
- `kuaishou`：当前主要还是基础退款 / 拒绝退款

---

## 5. 用户退款素材覆盖情况

从 `users` fixture 统计：

| 平台 | 总订单数 | 带退款订单数 | 退款状态样本 |
|---|---:|---:|---|
| `taobao` | 9 | 3 | `refunding`, `refunded` |
| `douyin_shop` | 9 | 3 | `refunding`, `refunded` |
| `jd` | 9 | 3 | `refunding`, `refunded` |
| `xhs` | 9 | 3 | `refunding`, `refunded` |
| `kuaishou` | 9 | 3 | `refunding`, `refunded` |

结论：

- 这 5 个电商平台的用户退款素材是齐的。
- 也就是说，`user-sim` 侧的“用户问退款”并不是缺样本，而是统一售后链没有完全接上。

对照：

- `wecom_kf/users` 当前没有退款订单素材，它只能通过 `biz_platform + order_id` 桥接到电商平台售后事实。

---

## 6. live smoke 结果

### 6.1 统一接口 smoke

测试日期：

- 2026-04-03

测试样本：

| 平台 | 订单样本 | 退款样本 |
|---|---|---|
| `taobao` | `12345678901234` | `TB_ORDER_003` |
| `douyin_shop` | `6912558345648290211` | `DS_ORDER_003` |
| `jd` | `98765432101234` | `JD_ORDER_003` |
| `xhs` | `XHS12345678901234` | `XHS_ORDER_003` |
| `kuaishou` | `KS_ORDER_003` | `KS_ORDER_003` |

结果：

| 平台 | `/api/orders` | `/api/shipments` | `/api/after-sales/by-order` | `/api/context` |
|---|---:|---:|---:|---:|
| `taobao` | `200` | `404` | `200` 但返回错误对象 | `200` |
| `douyin_shop` | `200` | `404` | `200` 但返回错误对象 | `200` |
| `jd` | `200` | `200` | `200` 但返回错误对象 | `200` |
| `xhs` | `200` | `404` | `200` 但返回错误对象 | `200` |
| `kuaishou` | `404` | `404` | `200` 但返回错误对象 | `200` |

结论：

1. `jd` 是目前唯一在本轮样本里“订单 + 物流”都真正通的电商平台。
2. `taobao / douyin_shop / xhs` 的订单统一接口能通，但物流统一接口仍未通。
3. `kuaishou` 当前连订单样本也没有稳定打通，属于五个平台里最薄的一条。
4. 五个平台的 `/api/after-sales/{platform}/by-order/{order_id}` 目前都没有真正按订单查出退款事实。

### 6.2 修复后复测（2026-04-03 晚）

修复内容：

- `official-sim` 增加 `/official-sim/raw/after-sales/by-order/{order_id}`
- `domain-service` 改为真正走 `order_id -> after_sale fact` 查询，不再把 `order_id` 当 `refund_id`
- 引入 canonical `after_sale_id` + `external_order_id` 语义
- 让 user fixture 订单号和公共平台订单号都能落到同一条售后事实

复测样本：

| 平台 | 业务订单号 | 公共平台订单号 |
|---|---|---|
| `taobao` | `TB_ORDER_003` | `12345678901234` |
| `douyin_shop` | `DS_ORDER_003` | `6912558345648290211` |
| `jd` | `JD_ORDER_003` | `98765432101234` |
| `xhs` | `XHS_ORDER_003` | `XHS12345678901234` |
| `kuaishou` | `KS_ORDER_003` | `KS_ORDER_003` |

复测结果：

| 平台 | `/official-sim/raw/after-sales/by-order` | `/api/after-sales/by-order` | `ask_refund` |
|---|---:|---:|---|
| `taobao` | `200` | `200` | `after_sale_status`，状态=`退款中` |
| `douyin_shop` | `200` | `200` | `after_sale_status`，状态=`退款中` |
| `jd` | `200` | `200` | `after_sale_status`，状态=`退款中` |
| `xhs` | `200` | `200` | `after_sale_status`，状态=`退款中` |
| `kuaishou` | `200` | `200` | `after_sale_status`，状态=`退款中` |

关键现象：

- `TB_ORDER_003` 和 `12345678901234` 现在都会落到同一 canonical `after_sale_id=taobao:12345678901234:after_sale`
- `JD_ORDER_003` 和 `98765432101234` 现在都会落到同一 canonical `after_sale_id=jd:98765432101234:after_sale`
- 统一售后接口不再返回 `No after-sale found for this order`
- 推荐链里的退款回答不再是 `未知`

### 6.3 物流与公共订单样本修复后复测（2026-04-03 深夜）

修复内容：

- `official-sim` 的 `/raw/orders` / `/raw/shipments` 在公共订单样本上改为优先命中 shipped / delivering fixture
- `OfficialSimProxyProvider` 开始归一化 `taobao / douyin_shop / xhs / kuaishou` 官方 shipment payload
- `JDAdapter` 补齐官方 `33xxx / 34xxx / 90000` 订单状态码到统一状态的映射
- `RecommendationService` 的 `ask_shipment` 不再误回售后模板

复测样本：

| 平台 | 公共平台订单号 |
|---|---|
| `taobao` | `12345678901234` |
| `douyin_shop` | `6912558345648290211` |
| `jd` | `98765432101234` |
| `xhs` | `XHS12345678901234` |
| `kuaishou` | `KS12345678901235` |

复测结果：

| 平台 | `/api/orders` | `/api/shipments` | `shipment status` |
|---|---|---|---|
| `taobao` | `200` | `200` | `shipped` |
| `douyin_shop` | `200` | `200` | `delivered` |
| `jd` | `200` | `200` | `shipped` |
| `xhs` | `200` | `200` | `in_transit` |
| `kuaishou` | `200` | `200` | `in_transit` |

关键现象：

- `GET /api/shipments/{platform}/{public_order_id}` 现在五平台都返回 `tracking_no=SF1234567890`
- `GET /api/orders/jd/98765432101234` 不再掉回 `wait_pay`，而是按官方 shipped fixture 归一化
- `GET /api/orders/kuaishou/KS12345678901235` 不再 `404`
- 五平台公共订单样本现在都能形成 `order -> shipment` 的可用主链

### 6.4 alias / canonical ID 与 user fixture 唯一 external id 收口后复测（2026-04-03 深夜）

修复内容：

- 五平台 order alias 规则统一下沉到 `providers/utils/sim_identity.py`
- 五平台 `users` fixture 中的业务订单补齐唯一 `external_order_id`
- `ConversationDomainService` 不再只写 JD 特例，而是统一将 `*_ORDER_* -> public external order id`
- `orders / shipments / after-sales / context` 统一补出 `requested_order_id / external_order_id / canonical_order_id`
- `OfficialSimProxyProvider` 接受 alias 与 public order id 的等价匹配
- `kuaishou` 退款中订单在 `/official-sim/raw/orders` 上不再误回 refund payload

复测样本：

| 平台 | 订单 alias | 物流 alias |
|---|---|---|
| `taobao` | `TB_ORDER_003` | `TB_ORDER_002` |
| `douyin_shop` | `DS_ORDER_003` | `DS_ORDER_002` |
| `jd` | `JD_ORDER_003` | `JD_ORDER_001` |
| `xhs` | `XHS_ORDER_003` | `XHS_ORDER_002` |
| `kuaishou` | `KS_ORDER_003` | `KS_ORDER_002` |

复测结果：

- `GET /api/orders/{platform}/{alias}` 现在五平台都返回：
  - `requested_order_id`
  - `external_order_id`
  - `canonical_order_id`
- `GET /api/orders/taobao/TB_ORDER_001` 现在返回 `order_id=12345678901231`
- `GET /api/orders/jd/JD_ORDER_001` 现在返回 `order_id=98765432101231`
- `GET /api/shipments/{platform}/{alias}` 现在五平台都返回：
  - `requested_order_id`
  - `external_order_id`
  - `canonical_order_id`
  - `canonical_shipment_id`
- `GET /api/context/wecom_kf/{alias}` 现在能把：
  - `TB_ORDER_003 -> taobao/12345678901234`
  - `DS_ORDER_003 -> douyin_shop/6912558345648290211`
  - `JD_ORDER_003 -> jd/98765432101234`
  - `XHS_ORDER_003 -> xhs/XHS12345678901234`
  - `KS_ORDER_003 -> kuaishou/KS12345678901234`
  - `KS_ORDER_002 -> kuaishou/KS12345678901235`
- `wecom_kf` 上下文里现在能显式看到：
  - `effective_platform`
  - `effective_biz_id`
  - `external_biz_id`
  - `canonical_order_id`

结论：

- 五平台 alias 直查现在已经可用，不再是“只有公共平台订单号能查”
- `wecom_kf -> 五电商平台` 的桥接也已经从 JD 扩到了 5 平台
- 五平台 user fixture 业务订单现在已经做到“一单一 external id”
- 新 external id 已经真实回填进 live Odoo，`client_order_ref / runtime link` 当前都已与这批 user fixture 订单对齐

---

### 6.5 `wecom_kf` 固定会话扩充后复测（2026-04-03 深夜）

修复内容：

- `wecom_kf/users` 不再只保留 JD 固定会话
- 新增固定会话：
  - `CONV_WK_005 -> TB_ORDER_003`
  - `CONV_WK_006 -> DS_ORDER_002`
  - `CONV_WK_007 -> XHS_ORDER_002`
  - `CONV_WK_008 -> KS_ORDER_003`
- `ConversationDomainService.resolve_business_reference(...)` 在没有 provider/run 时也会回退到 fixture 会话本身做桥接
- `official-sim/raw/shipments` 在“已知订单但没有物流事实”时返回 `404`，避免把别的公共样本物流串进当前会话

复测结果：

- `GET /api/context/wecom_kf/CONV_WK_006`
  - `effective_platform=douyin_shop`
  - `effective_biz_id=6912558345648290202`
  - 返回 `shipment_snapshot.tracking_no=DY1234567890`
- `GET /api/context/wecom_kf/CONV_WK_008`
  - `effective_platform=kuaishou`
  - `effective_biz_id=KS12345678901234`
  - `after_sale_snapshot.status_text=退款中`
  - `source_errors` 明确记录 `shipment_snapshot: No shipment fixture found for order KS12345678901234`
- `GET /official-sim/raw/shipments/KS12345678901234?platform=kuaishou`
  - 返回 `404`
  - 不再误回 `KS12345678901235` 的默认物流样本

## 7. 推荐链 smoke

测试问题类型：

- `ask_order_status`
- `ask_shipment`
- `ask_refund`

结果摘要：

| 平台 | 订单状态问题 | 物流问题 | 退款问题 |
|---|---|---|---|
| `taobao` | `order_status` 正常 | 回退 `general_greeting` | `after_sale_status` 但状态为 `未知` |
| `douyin_shop` | `order_status` 正常 | 回退 `general_greeting` | `after_sale_status` 但状态为 `未知` |
| `jd` | `order_status` 正常 | `shipment_info` 正常 | `after_sale_status` 但状态为 `未知` |
| `xhs` | `order_status` 但状态为 `未知` | 回退 `general_greeting` | `after_sale_status` 但状态为 `未知` |
| `kuaishou` | `order_status` 但状态为 `未知` | 回退 `general_greeting` | `after_sale_status` 但状态为 `未知` |

关键样例：

- `taobao / ask_order_status / TB_ORDER_001`
  - 返回：`reply_type=order_status`
  - 内容：`wait_ship`
- `jd / ask_shipment / JD_ORDER_001`
  - 返回：`reply_type=shipment_info`
  - 内容包含：`SF1234567890 / 顺丰速运`
- `5 平台 / ask_refund / *_ORDER_003`
  - 都返回：`reply_type=after_sale_status`
  - 但状态文案都为：`未知`

结论：

1. “用户问订单状态”这条链在 5 个电商平台都至少有基础响应。
2. “用户问物流”目前只有 `jd` 真正有可用答案；其余平台仍会退回泛化问候。
3. “用户问退款”虽然会走到 `after_sale_status` 模板，但统一售后事实没接上，所以只能回答 `未知`。

### 7.2 修复后复测（2026-04-03 晚）

退款问题复测结果：

| 平台 | 输入订单号 | 输出 |
|---|---|---|
| `taobao` | `TB_ORDER_003` / `12345678901234` | `after_sale_status`，文案=`退款中` |
| `douyin_shop` | `DS_ORDER_003` / `6912558345648290211` | `after_sale_status`，文案=`退款中` |
| `jd` | `JD_ORDER_003` / `98765432101234` | `after_sale_status`，文案=`退款中` |
| `xhs` | `XHS_ORDER_003` / `XHS12345678901234` | `after_sale_status`，文案=`退款中` |
| `kuaishou` | `KS_ORDER_003` | `after_sale_status`，文案=`退款中` |

额外桥接验证：

- `GET /api/context/wecom_kf/JD_ORDER_003?official_run_id=225d176c-b192-40e1-91aa-d9e9c8f36355`
  - 返回 `after_sale_snapshot.after_sale_id=jd:98765432101234:after_sale`
  - 返回 `status_text=退款中`
  - `source_errors=[]`
- `POST /api/recommendations/reply` with `platform=wecom_kf,biz_id=JD_ORDER_003,intent=ask_refund,official_run_id=225d176c-b192-40e1-91aa-d9e9c8f36355`
  - 返回 `reply_type=after_sale_status`
  - 文案：`您好，您的售后申请状态为：退款中，我们正在处理中。`

### 7.3 物流问题复测（2026-04-03 深夜）

物流问题复测结果：

| 平台 | 输入订单号 | 输出 |
|---|---|---|
| `taobao` | `12345678901234` | `shipment_info`，文案含 `SF1234567890 / 顺丰速运` |
| `douyin_shop` | `6912558345648290211` | `shipment_info`，文案含 `SF1234567890 / 顺丰速运` |
| `jd` | `98765432101234` | `shipment_info`，文案含 `SF1234567890 / 顺丰速运` |
| `xhs` | `XHS12345678901234` | `shipment_info`，文案含 `SF1234567890 / 顺丰速运` |
| `kuaishou` | `KS12345678901235` | `shipment_info`，文案含 `SF1234567890 / 顺丰速运` |

补充说明：

- `ask_shipment` 现在五个平台都不再退回 `general_greeting`
- 也不再因为 `after_sale_snapshot` 存在而误回 `after_sale_status`

---

## 8. 历史断点与当前状态

### 8.1 `/by-order` 售后查询实现不对（修复前基线）

[after_sale_domain_service.py](/home/kkk/Project/platform-sim/apps/core/domain-service/app/services/after_sale_domain_service.py#L28) 当前逻辑是：

- 直接把 `order_id` 传给 `gateway.get_refund(...)`

这意味着它实际在做：

- `get_refund(order_id)`

而不是：

- `order_id -> refund_id / after_sale_id`
- 再查对应售后单

结果就是：

- user fixture 明明有退款订单
- 统一售后接口却按订单查不出来

### 8.2 订单 ID 空间不统一（修复前基线）

当前仓库里存在两套 ID 空间：

1. 中台公共样本接口可用的外部订单号
   - 例如 `12345678901234`、`6912558345648290211`、`98765432101234`
2. user fixture / 会话 / 仿真 run 使用的业务订单号
   - 例如 `TB_ORDER_001`、`DS_ORDER_001`、`JD_ORDER_001`

这会导致：

- 某些平台 `recommendation/context` 能吃 `*_ORDER_*`
- 但 `/api/orders/{platform}/{id}` 只对另一套 id 生效

这也是为什么这次生命周期测试里：

- `taobao / douyin_shop / xhs` 的公共订单样本能查
- 但 user fixture 订单样本不一定能直接打通统一订单接口

### 8.2 修复后状态

这条现在已经不是“完全未解决”，而是进入了可控状态：

- 统一售后链新增了 canonical `after_sale_id`
- 统一订单 / 物流 / 售后 / context 现在都会显式保留：
  - `requested_order_id`
  - `external_order_id`
  - `canonical_order_id`
- 当 user fixture 订单号和公共平台订单号属于同一逻辑订单时，二者现在会落到同一 canonical `after_sale_id`
- `wecom_kf` 会话桥现在也不再只偏向 JD，而是能解析五电商平台 alias

当前仓库采用的规则是：

1. `after_sale_id` 作为稳定主键，优先用 canonical id。
2. `external_after_sale_id` 只有在官方 fixture / payload 自身提供真实外部售后号时才填。
3. `requested_order_id`、`external_order_id` 与 `canonical_order_id` 分离，避免再把一条 ID 同时充当业务订单号、平台订单号、售后单号。

### 8.3 主链已打通，user fixture external id 与 live Odoo 已同步

从当前 live 结果看：

- 五个平台的 alias 订单和公共平台订单样本现在都能打通 `orders / shipments / after-sales`
- `wecom_kf` 到五电商平台的桥接也已经可用
- 五个平台 `users` fixture 里的业务订单现在都已经有独立 `external_order_id`
- live Odoo 已经完成 `client_order_ref 54 条` 回填，并写入 `data/runtime/odoo_order_links.json 54 条`
- 所以当前 remaining risk 不再是 ID 主链错位，而是“多平台 user-sim run 模板和固定会话样本还可以继续扩厚”

---

## 9. 结论

截至 2026-04-03，本仓库五个电商平台的真实状态是：

1. 生命周期素材层：
   - 5 个平台都有订单生命周期
   - 5 个平台都有退款用户素材
   - 各平台差异已经足够体现真实业务差别
2. 中台统一链层：
   - 订单链：5 平台公共订单样本都可用
   - alias 订单链：5 平台 alias 直查也已可用
   - 物流链：5 平台公共订单样本都已打通
   - alias 物流链：5 平台 alias 也已补齐 canonical ID 语义
   - 售后链：5 个平台已经按订单打通，且 `ask_refund` 能拿到真实状态
   - 会话桥：`wecom_kf -> taobao / douyin_shop / jd / xhs / kuaishou` 已可用
3. 用户问题响应层：
   - `ask_order_status`：5 平台有基础回答
   - `ask_shipment`：5 平台都已返回真实物流信息
   - `ask_refund`：5 平台已经能回答到真实售后状态

所以现在不能说：

- “五个平台还只是零散 mock 样本”

更准确的说法现在变成：

- “五个平台的订单 / 物流 / 售后统一查询链和 `wecom_kf` 桥接链都已经能跑通；user fixture 订单已经是一单一 external id，并且 live Odoo 已同步到这批新 external id。当前剩余重点是继续扩展 user-sim 的多平台固定会话样本和更多真实问题类型。”

---

## 10. 下一步修复优先级

1. 继续压实 canonical ID 语义：
   - 这一步已完成：seed、runtime link、live `client_order_ref` 已同步
   - 下一步更适合加针对 `integration/context` 的更大批量回归，而不是继续做 ID 本体修补
2. 扩多平台 `wecom_kf` 固定会话 fixture：
   - 这一步已完成第一批 `taobao / douyin_shop / xhs / kuaishou` 会话
   - 下一步可以继续补更多“订单状态 / 物流 / 退款 / 投诉”类型，而不是只留一条代表性会话
3. 再做一次“五平台三类用户问题”的全回归：
   - `ask_order_status`
   - `ask_shipment`
   - `ask_refund`

---

## 11. 同类产品的 ID 方案参考

本轮额外查了几类同类产品 / 平台文档，结论比较一致：

1. Zendesk 这类客服系统会同时保留内部 profile id 和外部标识。
   - 官方文档在 profile `identifiers` 里明确列出 `external_id`
   - 这意味着外部系统主键不应该直接覆盖平台内部主键
2. Shopify 明确区分 GraphQL 全局 `id` 和 REST 侧 `legacyResourceId`。
   - 这本质上就是“canonical id + legacy external id”并存
3. Salesforce 的集成模式长期强调 External ID / Upsert Key。
   - 也就是：内部记录可以稳定，外部系统来的主键用单独字段承接和匹配

因此当前仓库的售后 ID 方案定成：

- `after_sale_id`
  - 统一稳定主键，走 canonical 规则
- `external_after_sale_id`
  - 只在官方 payload 自带外部售后号时返回
- `order_id`
  - 当前命中的业务订单号
- `external_order_id`
  - 平台公共订单号 / 对外订单号
- `requested_order_id`
  - 调用方最初拿来查询的订单号

这样做的目的就是避免再出现：

- `order_id == refund_id`
- `业务订单号 == 平台公共订单号 == 售后单号`
- 中台无法判断“当前看到的是哪一层 ID”

参考来源：

- Zendesk Developer Docs: https://developer.zendesk.com/documentation/ticketing/profiles/anatomy-of-a-profile/
- Shopify Admin GraphQL API: https://shopify.dev/docs/api/admin-graphql
- Salesforce Developers / Integration Patterns: https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns
