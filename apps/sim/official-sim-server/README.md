# Official Sim Server

多平台官方行为仿真层 - 模拟平台 API / callback / webhook 的行为。

> **注意**: 本服务只负责仿真，不是业务入口。所有业务查询请通过 `domain-service` 访问。

## 功能特性

- 支持六平台仿真: taobao, douyin_shop, jd, xhs, kuaishou, wecom_kf
- Run 生命周期管理
- 状态机场景编排
- Artifact / Push Event / Snapshot 管理
- 错误注入 (12 类常见错误)
- Evaluation Report 生成
- Raw Query (直接访问 fixtures)

## 职责边界

**本服务只负责：**
- 仿真 Run 管理 (`/official-sim/runs/*`)
- Raw 数据查询 (`/official-sim/raw/*`)
- 六平台兼容层 (`/mock/{platform}/*`)

**业务查询请使用：**
- `domain-service` - 唯一业务入口
  - 订单查询: `/api/orders/*`
  - 物流查询: `/api/shipments/*`
  - 售后查询: `/api/after-sales/*`
  - 会话查询: `/api/conversations/*`
  - 业务上下文: `/api/context/*`

## 快速开始

### 1. 安装依赖

```bash
cd apps/sim/official-sim-server
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
# 使用 SQLite (默认)
export DATABASE_URL="sqlite:///./official_sim.db"
alembic upgrade head

# 或使用 PostgreSQL
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/official_sim"
alembic upgrade head
```

### 3. 启动服务

```bash
uvicorn app.main:app --reload --port 8000
```

### 4. 运行测试

```bash
python -m pytest tests/ -v
```

## API 示例

### 创建 Run

```bash
# 淘宝 - 待发货场景
curl -X POST http://localhost:8000/official-sim/runs \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "taobao",
    "scenario_name": "wait_ship_basic"
  }'

# 抖店 - 完整流程
curl -X POST http://localhost:8000/official-sim/runs \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "douyin_shop",
    "scenario_name": "full_flow"
  }'

# 企微 - 会话场景
curl -X POST http://localhost:8000/official-sim/runs \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "wecom_kf",
    "scenario_name": "full_session"
  }'

# 京东 - 订单场景
curl -X POST http://localhost:8000/official-sim/runs \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "jd",
    "scenario_name": "wait_ship_basic"
  }'

# 小红书 - 订单场景
curl -X POST http://localhost:8000/official-sim/runs \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "xhs",
    "scenario_name": "wait_ship_basic"
  }'

# 快手 - 订单场景
curl -X POST http://localhost:8000/official-sim/runs \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "kuaishou",
    "scenario_name": "wait_ship_basic"
  }'
```

### 推进 Run

```bash
RUN_ID="your-run-id"

curl -X POST "http://localhost:8000/official-sim/runs/${RUN_ID}/advance" \
  -H "Content-Type: application/json" \
  -d '{"event_type": "step_advance"}'
```

### 查询 Run

```bash
RUN_ID="your-run-id"

curl http://localhost:8000/official-sim/runs/${RUN_ID}
```

### 查询 Artifacts

```bash
RUN_ID="your-run-id"

# 所有 artifacts
curl http://localhost:8000/official-sim/runs/${RUN_ID}/artifacts

# 指定 step
curl "http://localhost:8000/official-sim/runs/${RUN_ID}/artifacts?step_no=1"
```

### 注入错误

```bash
RUN_ID="your-run-id"

# Token 过期
curl -X POST "http://localhost:8000/official-sim/runs/${RUN_ID}/inject-error" \
  -H "Content-Type: application/json" \
  -d '{"error_code": "token_expired"}'

# 签名无效
curl -X POST "http://localhost:8000/official-sim/runs/${RUN_ID}/inject-error" \
  -H "Content-Type: application/json" \
  -d '{"error_code": "invalid_signature"}'

# 权限拒绝
curl -X POST "http://localhost:8000/official-sim/runs/${RUN_ID}/inject-error" \
  -H "Content-Type: application/json" \
  -d '{"error_code": "permission_denied"}'
```

### 生成 Report

```bash
RUN_ID="your-run-id"

curl http://localhost:8000/official-sim/runs/${RUN_ID}/report
```

## 端到端场景示例

### 淘宝完整流程

```bash
# 1. 创建 run
RUN_RESPONSE=$(curl -s -X POST http://localhost:8000/official-sim/runs \
  -H "Content-Type: application/json" \
  -d '{"platform": "taobao", "scenario_name": "full_flow"}')
RUN_ID=$(echo $RUN_RESPONSE | jq -r '.run_id')
echo "Created run: $RUN_ID"

# 2. 推进 3 步完成流程
for step in 1 2 3; do
  curl -s -X POST "http://localhost:8000/official-sim/runs/${RUN_ID}/advance" \
    -H "Content-Type: application/json" \
    -d '{"event_type": "step_advance"}' > /dev/null
  echo "Advanced to step $step"
done

# 3. 查看 report
curl -s http://localhost:8000/official-sim/runs/${RUN_ID}/report | jq .
```

## 支持的错误码

| 错误码 | HTTP 状态 | 可重试 | 说明 |
|--------|-----------|--------|------|
| token_expired | 401 | ✅ | Access token 过期 |
| invalid_signature | 403 | ❌ | 签名验证失败 |
| timestamp_out_of_window | 400 | ❌ | 时间戳超出窗口 |
| permission_denied | 403 | ❌ | 权限不足 |
| resource_not_found | 404 | ❌ | 资源不存在 |
| rate_limited | 429 | ✅ | 请求限流 |
| duplicate_push | 409 | ❌ | 重复推送 |
| out_of_order_push | 400 | ✅ | 乱序推送 |
| callback_ack_invalid | 400 | ❌ | callback 确认无效 |
| conversation_closed | 410 | ❌ | 会话已关闭 |
| msg_code_expired | 400 | ✅ | 消息码过期 |
| internal_error | 500 | ✅ | 内部错误 |

## 六平台场景

### Taobao (淘宝)

- `wait_ship_basic` - 待发货基础流程
- `wait_ship_to_shipped` - 待发货→已发货
- `shipped_to_finished` - 已发货→已完成
- `full_flow` - 完整流程 (支付→发货→确认收货)

### Douyin Shop (抖店)

- `basic_paid_to_shipped` - 付款→发货
- `basic_shipped_to_confirmed` - 发货→确认收货
- `basic_confirmed_to_completed` - 确认收货→完成
- `full_flow` - 完整流程
- `refund_flow` - 退款流程

### JD (京东)

- `wait_ship_basic` - 待发货基础流程
- `full_flow` - 完整流程

### XHS (小红书)

- `wait_ship_basic` - 待发货基础流程
- `full_flow` - 完整流程

### Kuaishou (快手)

- `wait_ship_basic` - 待发货基础流程
- `full_flow` - 完整流程

### Wecom KF (企微客服)

- `basic_session` - 基础会话
- `full_session` - 完整会话 (开始→关闭)
- `session_expired` - 会话过期

## 数据库迁移

```bash
# 创建新迁移
alembic revision --autogenerate -m "description"

# 升级
alembic upgrade head

# 回滚
alembic downgrade -1
```

## 已知限制

1. P0 阶段主要验证 taobao, douyin_shop, wecom_kf 三个平台
2. jd, xhs, kuaishou 平台场景正在扩展中
3. 不支持真实 provider 接入
4. 不支持 MQ / Kafka 等重型基础设施
5. 不支持复杂 RAG

## 项目结构

```
apps/sim/official-sim-server/
├── app/
│   ├── api/
│   │   ├── router.py
│   │   └── routes/
│   │       ├── runs.py
│   │       └── raw_query.py
│   ├── core/
│   │   ├── config.py
│   │   ├── errors.py
│   │   └── database.py
│   ├── domain/
│   │   ├── scenario_engine.py
│   │   └── artifact_builder.py
│   ├── models/
│   │   └── models.py
│   ├── platforms/
│   │   ├── taobao/
│   │   ├── douyin_shop/
│   │   ├── jd/
│   │   ├── xhs/
│   │   ├── kuaishou/
│   │   └── wecom_kf/
│   └── repositories/
├── tests/
├── alembic/
│   └── versions/
└── README.md
```

## License

MIT
