# Domain Service - 客服中台统一业务层

## 概述

Domain Service 是客服中台的唯一业务入口层，实现了六平台全覆盖的统一业务能力。

## 架构

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
│  Service Layer (9个核心服务)                                  │
│  ├── PlatformGatewayService    平台网关                       │
│  ├── OrderDomainService        订单领域                       │
│  ├── ShipmentDomainService     物流领域                       │
│  ├── AfterSaleDomainService    售后领域                       │
│  ├── ConversationDomainService 会话领域                       │
│  ├── BusinessContextService    业务上下文                     │
│  ├── RecommendationService     推荐                           │
│  ├── QualityService            质检                           │
│  └── RiskService               风控                           │
├─────────────────────────────────────────────────────────────┤
│  Adapter Layer (六平台适配器)                                 │
│  ├── TaobaoAdapter          淘宝                              │
│  ├── DouyinShopAdapter      抖店                              │
│  ├── JDAdapter              京东                              │
│  ├── XhsAdapter             小红书                            │
│  ├── KuaishouAdapter        快手                              │
│  └── WecomKfAdapter         企微客服                          │
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

## 快速开始

### 安装依赖

```bash
pip install fastapi uvicorn pydantic pydantic-settings
```

### 启动服务

```bash
cd apps/domain-service
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 健康检查

```bash
curl http://localhost:8000/healthz
```

## API 示例

### 获取订单

```bash
curl http://localhost:8000/api/orders/taobao/TB_ORDER_001
```

### 获取物流

```bash
curl http://localhost:8000/api/shipments/taobao/TB_ORDER_001
```

### 构建业务上下文

```bash
curl -X POST http://localhost:8000/api/context/build \
  -H "Content-Type: application/json" \
  -d '{"platform": "taobao", "biz_id": "TB_ORDER_001", "biz_type": "order"}'
```

### 获取回复推荐

```bash
curl -X POST http://localhost:8000/api/recommendations/reply \
  -H "Content-Type: application/json" \
  -d '{"platform": "taobao", "biz_id": "TB_ORDER_001", "biz_type": "order"}'
```

### 质检检查

```bash
curl -X POST http://localhost:8000/api/quality/check-reply \
  -H "Content-Type: application/json" \
  -d '{"reply_content": "您好，请问有什么可以帮您的？"}'
```

### 风控检查

```bash
curl -X POST http://localhost:8000/api/risk/check-order \
  -H "Content-Type: application/json" \
  -d '{"order_data": {"order_id": "001", "status": "wait_ship", "total_amount": "299.00"}}'
```

## 目录结构

```
apps/domain-service/
├── app/
│   ├── main.py              # FastAPI 应用入口
│   ├── core/                # 核心配置
│   │   ├── config.py        # 配置管理
│   │   ├── deps.py          # 依赖注入
│   │   ├── errors.py        # 错误定义
│   │   └── response.py      # 响应格式
│   ├── api/                 # API 路由
│   │   ├── router.py        # 路由聚合
│   │   └── routes/          # 各业务路由
│   ├── schemas/             # Pydantic 模型
│   ├── services/            # 业务服务
│   └── adapters/            # 平台适配器
├── tests/                   # 测试文件
└── README.md
```

## 核心概念

### BusinessContext

业务上下文是中台的核心聚合对象，统一聚合：
- 平台数据：订单、物流、售后、会话
- ERP数据：库存、订单审核、异常
- 风险标记：风险等级、标签、评分
- 质检标记：质量评分、问题、建议
- 候选动作：可执行操作建议
- 回复候选：回复内容建议

### 平台适配器

每个平台适配器负责：
- 将平台原始数据转换为统一模型
- 将统一模型转换回平台格式
- 状态码映射
- 错误码归一化

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| ENVIRONMENT | 运行环境 | development |
| DATABASE_URL | 数据库连接串 | - |
| OFFICIAL_SIM_BASE_URL | sim服务地址 | http://localhost:8001 |
| DEFAULT_PROVIDER_MODE | provider模式 | mock |

## 测试

```bash
cd apps/domain-service
pytest tests/ -v
```

## 相关模块

- [official-sim-server](../official-sim-server) - 官方平台行为仿真层
- [ai-orchestrator](../ai-orchestrator) - AI 编排层
- [providers](../../providers) - 平台供数端
- [Odoo Provider](../../providers/odoo) - ERP 供数端
