# 三层架构设计文档

**日期**: 2026-03-31

---

## 一、架构总览

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              三层数据流架构                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  上游（平台侧）              中游（中台）                下游（业务系统）          │
│  ─────────────             ─────────────              ─────────────            │
│  platform-sim              Omni-CSX                   Odoo                     │
│                                                                                 │
│  角色：                     角色：                     角色：                    │
│  模拟平台官方API            客服运营中台               真实ERP                   │
│                                                                                 │
│  数据方向：                 数据方向：                 数据方向：                 │
│  向中台供给                 消费平台数据               向中台供给                 │
│  平台数据                   + 消费ERP数据              库存/订单/发货数据          │
│                                                                                 │
│  输出：                     职责：                     输出：                    │
│  官方API格式                统一接待                   ERP数据                   │
│  订单/物流/售后             统一业务上下文                                       │
│  会话数据                   AI辅助                                               │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 二、各层职责边界

| 层级 | 项目 | 职责 | 不做什么 |
|-----|-----|-----|---------|
| **上游** | platform-sim | 模拟淘宝/抖音/京东/小红书/快手/企微等平台官方API，输出官方级完整字段 | 不做业务逻辑，不做数据转换 |
| **中游** | Omni-CSX | 消费平台数据+ERP数据，统一接待、统一业务上下文、AI辅助 | 不模拟平台，不存储真实业务数据 |
| **下游** | Odoo | 供给库存/商品/销售订单/发货履约数据 | 不处理客服逻辑 |

---

## 三、数据流向

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│    platform-sim                    Omni-CSX                      Odoo          │
│    ────────────                   ──────────                    ──────         │
│                                                                                 │
│    fixtures/                      providers/                    providers/     │
│    ├── taobao/                    ├── taobao/                   └── odoo/      │
│    ├── douyin_shop/  ──HTTP──→    ├── douyin_shop/                             │
│    ├── xhs/                       ├── xhs/                      ┌──────────┐   │
│    ├── jd/                        ├── jd/                       │ mock/    │   │
│    ├── kuaishou/                  ├── kuaishou/                 │ real/    │   │
│    └── wecom_kf/                  └── wecom_kf/                 └──────────┘   │
│                                                                                 │
│          │                              │                            │         │
│          │                              │                            │         │
│          ↓                              ↓                            ↓         │
│                                                                                 │
│    /mock/{platform}/              domain-service/              integration/    │
│    ├── /orders/{id}               ├── conversations            ├── inventory   │
│    ├── /shipments/{id}            ├── context                  ├── order-audits│
│    ├── /after-sales/{id}          ├── recommendation           └── order-     │
│    └── /refunds/{id}              ├── analytics                    exceptions │
│                                   ├── quality_*                               │
│                                   ├── risk_*                                  │
│                                   └── integration ◄───────────────────────────┘│
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 四、项目目录结构

### 4.1 platform-sim（上游）

```
platform-sim/
├── apps/
│   └── official-sim-server/
│       ├── app/
│       │   ├── main.py
│       │   ├── api/
│       │   │   ├── router.py
│       │   │   └── routes/
│       │   │       ├── runs.py
│       │   │       ├── mock_compat.py    # /mock/{platform}/ 端点
│       │   │       └── integration.py
│       │   ├── platforms/
│       │   │   ├── taobao/profile.py
│       │   │   ├── douyin_shop/profile.py
│       │   │   ├── xhs/profile.py
│       │   │   ├── jd/profile.py
│       │   │   ├── kuaishou/profile.py
│       │   │   └── wecom_kf/profile.py
│       │   └── domain/
│       │       ├── scenario_engine.py
│       │       └── artifact_builder.py
│       └── fixtures/                       # 官方级完整字段
│           ├── taobao/success/
│           ├── douyin_shop/success/
│           ├── xhs/success/
│           ├── jd/success/
│           ├── kuaishou/success/
│           └── wecom_kf/success/
└── providers/                              # ⚠️ 待清理：硬编码 Provider
```

### 4.2 Omni-CSX（中游）

```
reference/omni-csx-v35/
├── apps/
│   └── domain-service/
│       ├── app/
│       │   ├── main.py
│       │   ├── api/
│       │   │   ├── conversations.py
│       │   │   ├── context.py
│       │   │   ├── recommendation.py
│       │   │   ├── analytics.py
│       │   │   ├── quality_*.py
│       │   │   ├── risk_*.py
│       │   │   └── integration.py         # Odoo 集成
│       │   └── services/
│       │       └── integration_service.py
│       └── tests/
├── providers/                              # 消费 platform-sim
│   ├── taobao/
│   │   ├── mock/
│   │   │   ├── provider.py                # HTTP 调用 platform-sim
│   │   │   └── mapper.py                  # 官方格式 → 统一 DTO
│   │   └── real/
│   ├── douyin_shop/
│   ├── xhs/
│   ├── jd/
│   ├── kuaishou/
│   ├── wecom_kf/
│   └── odoo/                              # 下游 ERP
│       ├── mock/
│       └── real/
└── packages/
    ├── provider-sdk/
    │   ├── dto/                           # 统一数据传输对象
    │   │   ├── order_dto.py
    │   │   ├── shipment_dto.py
    │   │   └── after_sale_dto.py
    │   └── interfaces/                    # Provider 接口定义
    │       ├── order_provider.py
    │       ├── shipment_provider.py
    │       └── after_sale_provider.py
    └── domain-models/
        └── models/                        # 领域模型
```

### 4.3 Odoo（下游）

```
Odoo 集成通过 providers/odoo/ 实现：
├── mock/
│   └── provider.py                        # Mock 数据
└── real/
    ├── client.py                          # Odoo XML-RPC 客户端
    ├── mapper.py                          # Odoo 格式 → 统一格式
    └── provider.py                        # 真实实现
```

---

## 五、核心接口定义

### 5.1 上游输出（platform-sim）

```
# 订单查询
GET /mock/{platform}/orders/{order_id}
返回：官方级完整字段的订单数据

# 物流查询
GET /mock/{platform}/shipments/{order_id}
返回：官方级完整字段的物流数据

# 售后查询
GET /mock/{platform}/after-sales/{after_sale_id}
GET /mock/{platform}/refunds/{refund_id}
返回：官方级完整字段的售后数据
```

### 5.2 中游消费（Omni-CSX Provider）

```python
class OrderProvider(ABC):
    @abstractmethod
    def get_order(self, order_id: str) -> OrderDTO:
        raise NotImplementedError

class ShipmentProvider(ABC):
    @abstractmethod
    def get_shipment(self, order_id: str) -> ShipmentDTO:
        raise NotImplementedError

class AfterSaleProvider(ABC):
    @abstractmethod
    def get_after_sale(self, after_sale_id: str) -> AfterSaleDTO:
        raise NotImplementedError
```

### 5.3 下游供给（Odoo）

```python
class OdooProvider:
    def get_inventory_list(self) -> list[dict]:
        """库存快照"""
        
    def get_order_audit_list(self) -> list[dict]:
        """订单审核快照"""
        
    def get_order_exception_list(self) -> list[dict]:
        """订单异常快照"""
```

---

## 六、统一数据传输对象（DTO）

### 6.1 OrderDTO

```python
@dataclass
class OrderDTO:
    platform: str
    order_id: str
    status: str
    status_name: str
    create_time: str | None
    pay_time: str | None
    total_amount: float
    freight_amount: float
    discount_amount: float
    payment_amount: float
    buyer_nick: str | None
    buyer_phone: str | None
    receiver_name: str | None
    receiver_phone: str | None
    receiver_address: AddressDTO | None
    items: list[OrderItemDTO]
    raw_json: dict[str, Any]  # 保留原始数据
```

### 6.2 ShipmentDTO

```python
@dataclass
class ShipmentDTO:
    platform: str
    order_id: str
    shipments: list[ShipmentItemDTO]
    raw_json: dict[str, Any]
```

### 6.3 AfterSaleDTO

```python
@dataclass
class AfterSaleDTO:
    platform: str
    after_sale_id: str
    order_id: str
    type: str
    type_name: str
    status: str
    status_name: str
    apply_time: str | None
    handle_time: str | None
    apply_amount: float
    approve_amount: float
    reason: str
    reason_detail: str
    raw_json: dict[str, Any]
```

---

## 七、当前实现成熟度

| 层级 | 项目 | 成熟度 | 说明 |
|-----|-----|-------|-----|
| **上游** | platform-sim | **80%** | fixtures 完整，mock_compat 配置需修复 |
| **中游** | Omni-CSX | **MVP (60%)** | 基础功能完整，AI 辅助待完善 |
| **下游** | Odoo 集成 | **Mock (40%)** | 有 mock provider，真实集成待完善 |

### 7.1 中游已实现功能

- ✅ 订单/物流/售后查询
- ✅ 会话管理
- ✅ 业务上下文
- ✅ 推荐系统
- ✅ 分析统计
- ✅ 质检相关
- ✅ 风控相关
- ✅ Odoo 集成
- ⚠️ AI 辅助（骨架已有，待完善）

### 7.2 中游待完善功能

- 多轮对话状态机
- 情绪识别与升级
- 知识库 RAG 集成
- 自动回复建议

---

## 八、已知问题与修复方案

### 8.1 FIXTURE_ALIAS 配置错误

**问题**：抖店订单默认映射到 `order_paid.json`（无物流），而非 `order_shipped.json`

**位置**：`apps/sim/official-sim-server/app/api/routes/mock_compat.py`

**修复方案**：
```python
"douyin_shop": {
    "order_sample.json": "order_shipped.json",  # 改为有物流的订单
    "refund_sample.json": "refund_applied.json",
    "product_sample.json": "order_paid.json",
},
```

### 8.2 platform-sim 内部有两套 Provider

**问题**：
- `platform-sim/providers/` - 硬编码数据
- `reference/omni-csx-v35/providers/` - 消费 platform-sim

**建议**：
- `platform-sim/providers/` 仅用于内部测试
- Omni-CSX 使用 `reference/omni-csx-v35/providers/`

### 8.3 Omni-CSX fixtures 优先级问题

**问题**：`_load_fixture_file` 优先加载 Omni-CSX 简化数据

**建议**：确保 platform-sim fixtures 优先级高于 Omni-CSX fixtures

---

## 九、验证命令

### 9.1 上游验证

```bash
# 启动 platform-sim
cd apps/sim/official-sim-server
uvicorn app.main:app --port 8200

# 测试订单接口
curl http://localhost:8200/mock/douyin-shop/orders/10001

# 测试物流接口
curl http://localhost:8200/mock/douyin-shop/orders/10002
```

### 9.2 中游验证

```bash
# 启动 Omni-CSX domain-service
cd reference/omni-csx-v35/apps/core/domain-service
uvicorn app.main:app --port 8101

# 测试 Odoo 集成
curl -X POST http://localhost:8101/api/integration/refresh

# 查看库存
curl http://localhost:8101/api/integration/inventory
```

---

## 十、下一步计划

1. **修复 FIXTURE_ALIAS 配置**
2. **清理 platform-sim/providers/ 目录**
3. **完善 AI 辅助功能**
4. **补充端到端测试**
5. **更新 AGENTS.md 文档**

---

## 十一、总结

三层架构设计合理，职责边界清晰：

- **上游 platform-sim**：只负责输出官方 API 格式数据，不做业务逻辑
- **中游 Omni-CSX**：消费两侧数据，提供统一服务，当前为 MVP 层面
- **下游 Odoo**：供给库存/发货等 ERP 数据

数据流已打通，可正常开发测试客服中台系统。
