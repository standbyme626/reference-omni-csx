# apps/sim

仿真运行区（支持中台研发联调，不承担主业务入口）。

服务分工：
- `official-sim-server`：模拟官方 API / callback / webhook。
- `user-sim-service`：模拟用户行为与对话推进。

约束：
- 仿真服务必须可独立启动。
- 上层中台通过 provider/adapter 接入，避免业务层直接耦合。
