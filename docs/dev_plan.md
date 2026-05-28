# 开发执行计划

## 并发实施（已启动）

5 个工作流并行：

| # | 子目录 | Agent 角色 | 输出 |
|---|---|---|---|
| 0 | `docs/` `infra/` | （已完成） | 架构文档、数据库 schema、Docker Compose、Prometheus |
| 1 | `backend/` | Backend Architect | FastAPI 全部业务 API + Alembic + JWT + AES-GCM |
| 2 | `signal_workers/` | AI Engineer | Hyperliquid WS / OKX public / EVM 聪明钱 worker + Redis Stream |
| 3 | `execution_engine/` | Backend Architect | 跟单引擎 + 风控 + 5 交易所适配器 + APScheduler |
| 4 | `frontend/` | Frontend Developer | Vue 3 SPA 全部页面 + 跟单配置弹窗 |

## 协作契约（agent 间共享）

- **数据库 schema 唯一源**：`infra/migrations/0001_init.sql`
- **事件 schema 唯一源**：`docs/event_schema.md` 的 `SignalEvent v1`
- **加密协议**：AES-256-GCM；key 从 env `AES_KEY` 读，32 bytes base64；backend 与 execution_engine 必须使用相同实现
- **服务发现**：local 用 docker-compose service name；prod 走 K8s Service
- **API URL 规范**：`/api/v1/<resource>`；分页 `?page=1&size=20`

## 合并验收清单

- [ ] backend 路由全部 200/201 响应
- [ ] backend pytest 全过
- [ ] signal_workers 三大 P0 worker 在 fakeredis 下完成端到端 test
- [ ] execution_engine position_mapper / risk / 5 adapter 单测过
- [ ] frontend `npm run build` 通过、`npm run dev` 起得来
- [ ] docker compose up -d 全栈起得来
- [ ] 端到端跑：注册 → 绑定 testnet API → 创建 copy_config → 模拟 signal 写入 Redis Stream → 看到 copy_orders + WS push 到前端

## 阶段二（agent 完成后我自己接手）

1. 编写 `infra/scripts/seed_demo_data.py` — 灌入演示交易员 + 配置
2. 跑通端到端 demo（testnet）
3. 出口 IP 池设计：每账户 4 个独立 IP（可用 Tailscale exit node 或 cloudflared tunnels）
4. 监控 Dashboard 模板（Grafana）
5. Telegram bot 通知集成
6. README 写完"快速开始"
