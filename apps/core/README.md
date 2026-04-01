# apps/core

中台主业务运行区。

当前主服务：
- `domain-service`：统一业务入口（聚合平台事实 + ERP 事实）。

约束：
- 对外业务 API 统一从 `apps/core/*` 暴露。
- 不在此目录混入仿真运行时代码。
