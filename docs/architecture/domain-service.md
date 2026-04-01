# Domain Service 架构文档

## 概述

Domain Service 是客服中台的统一业务入口层，负责：
- 六平台统一 provider 调度
- 统一模型映射
- 统一上下文聚合
- 统一规则判断
- 统一推荐生成
- 质检与风控

## 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      Domain Service                          │
│                    (唯一业务入口层)                           │
├─────────────────────────────────────────────────────────────┤
│  API Layer                                                   │
│  ├── /api/orders          订单统一查询                        │
│  ├── /api/shipments       物流统一查询                        │
│  ├── /api/after-sales     售后统一查询                        │
│  ├── /api/conversations   会话统一查询                        │
│  ├── /api/context         业务上下文聚合                      │
│  ├── /api/recommendations 推荐生成                            │
│  ├── /api/quality         质检                                │
│  └── /api/risk            风控                                │
├─────────────────────────────────────────────────────────────┤
│  Service Layer                                               │
│  ├── PlatformGatewayService    平台网关服务                   │
│  ├── OrderDomainService        订单领域服务                   │
│  ├── ShipmentDomainService     物流领域服务                   │
│  ├── AfterSaleDomainService    售后领域服务                   │
│  ├── ConversationDomainService 会话领域服务                   │
│  ├── BusinessContextService    业务上下文服务                 │
│  ├── RecommendationService     推荐服务                       │
│  ├── QualityService            质检服务                       │
│  └── RiskService               风控服务                       │
├─────────────────────────────────────────────────────────────┤
│  Adapter Layer                                               │
│  ├── TaobaoAdapter          淘宝适配器                        │
│  ├── DouyinShopAdapter      抖店适配器                        │
│  ├── JDAdapter              京东适配器                        │
│  ├── XhsAdapter             小红书适配器                      │
│  ├── KuaishouAdapter        快手适配器                        │
│  └── WecomKfAdapter         企微客服适配器                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Providers                               │
│  taobao / douyin_shop / jd / xhs / kuaishou / wecom_kf      │
│  odoo (ERP)                                                  │
└─────────────────────────────────────────────────────────────┘
```

## 六平台能力矩阵

| 平台 | 订单 | 物流 | 售后 | 会话 |
|------|------|------|------|------|
| taobao | ✓ | ✓ | ✓ | ✗ |
| douyin_shop | ✓ | ✓ | ✓ | ✗ |
| jd | ✓ | ✓ | ✓ | ✗ |
| xhs | ✓ | ✓ | ✓ | ✗ |
| kuaishou | ✓ | ✓ | ✓ | ✗ |
| wecom_kf | ✗ | ✗ | ✗ | ✓ |

## API 规范

### 统一响应格式

```json
{
  "code": "0",
  "message": "success",
  "data": { ... },
  "request_id": "req_xxx"
}
```

### 错误响应格式

```json
{
  "code": "order_not_found",
  "message": "Order not found",
  "request_id": "req_xxx",
  "details": { ... }
}
```

## 核心对象

### BusinessContext

业务上下文是中台的核心聚合对象，包含：

```python
class BusinessContext:
    context_id: str
    platform: str
    biz_id: str
    biz_type: str
    
    customer_profile: CustomerProfileSnapshot
    order_snapshot: OrderSnapshot
    shipment_snapshot: ShipmentSnapshot
    after_sale_snapshot: AfterSaleSnapshot
    inventory_snapshot: InventorySnapshot
    
    risk_flags: RiskFlags
    quality_flags: QualityFlags
    
    action_candidates: List[ActionCandidate]
    reply_candidates: List[ReplyCandidate]
    
    knowledge_refs: List[Dict]
```

## 部署说明

### 启动服务

```bash
cd apps/core/domain-service
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 环境变量

- `ENVIRONMENT`: 运行环境 (development/staging/production)
- `DATABASE_URL`: 数据库连接串
- `OFFICIAL_SIM_BASE_URL`: official-sim-server 地址
- `DEFAULT_PROVIDER_MODE`: 默认 provider 模式 (mock/real)
- `ODOO_PROVIDER_MODE`: Odoo provider 模式 (`mock`/`real`)
- `ODOO_BASE_URL`: Odoo 服务地址（`real` 模式使用）
- `ODOO_DB`: Odoo 数据库名（`real` 模式使用）
- `ODOO_USERNAME`: Odoo 用户名（`real` 模式使用）
- `ODOO_API_KEY`: Odoo API Key（`real` 模式使用）
