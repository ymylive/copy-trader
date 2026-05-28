# 快速开始

## 0 · 前置依赖

- Docker + Docker Compose（最简单的全栈启动）
- 或本地：Python 3.11+ / Node 18+ / Postgres 16（启用 TimescaleDB 扩展）/ Redis 7

## 1 · 一键全栈（推荐）

```bash
cd /Users/cornna/project/copy_trader
cp infra/.env.example infra/.env
docker compose -f infra/docker-compose.yml up -d
docker compose -f infra/docker-compose.yml logs -f backend signal_workers execution_engine
```

服务端口：
- `http://localhost:8000` — Backend FastAPI (含 `/healthz`, `/docs`, `/metrics`)
- `http://localhost:5173` — Frontend Vue SPA
- `localhost:5432` — Postgres + TimescaleDB
- `localhost:6379` — Redis
- `http://localhost:9090` — Prometheus
- `http://localhost:3000` — Grafana (admin/admin)

## 2 · 灌种子数据

```bash
docker compose -f infra/docker-compose.yml exec backend \
  python -m infra.scripts.seed_demo_data
```

或本地：

```bash
cd backend
DATABASE_URL=sqlite+aiosqlite:///./demo.db \
  python -m infra.scripts.seed_demo_data
```

默认账号：`demo` / `demo123`，含：
- 4 个绑定交易所子账户（账户1-4 已激活 3 个）
- 10 个 listed 交易员（含截图里的茂茂大魔王、风火山林Trader、MaximizeSR、KNOTMAIN 等真实数据）
- 3 个永久跟单名额 + 1 个 220 天下单名额
- 钱包余额 $500 USDT

## 3 · 本地分模块开发

### Backend

```bash
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests -v          # 11 测试通过
DATABASE_URL=sqlite+aiosqlite:///./dev.db \
  JWT_SECRET=dev AES_KEY=dev-32-byte-key-xxxxxxxxxxxxxx \
  python -m app.main     # http://localhost:8000
```

API 文档：`http://localhost:8000/docs` (FastAPI Swagger)

### Signal Workers

```bash
cd signal_workers
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e . fakeredis
pytest tests -v          # 38 测试通过

REDIS_URL=redis://localhost:6379/0 \
  python -m signal_workers --worker hyperliquid_ws
# 其他: okx_public / evm_smart_money / binance_lead / bicoin_scraper
```

### Execution Engine

```bash
cd execution_engine
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests -v          # 52 测试通过

DATABASE_URL=sqlite+aiosqlite:///../backend/demo.db \
  REDIS_URL=redis://localhost:6379/0 \
  AES_KEY=dev-32-byte-key-xxxxxxxxxxxxxx \
  python main.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev              # http://localhost:5173
# 默认走 mock 数据；要接真后端：
VITE_USE_MOCK=false VITE_API_BASE=http://localhost:8000/api/v1 npm run dev
```

## 4 · 端到端 demo 流程

1. 浏览器打开 `http://localhost:5173`
2. 登录 `demo` / `demo123`
3. 进入「控制台 → 交易员广场」选 1 个交易员，点「启动跟单」
4. 在配置弹窗里设置：
   - 资金模式：固定金额 100 USDT
   - 倍率：1
   - 启动策略：不复制
   - 触发：市价
   - 持仓止损：-10%
   - 安全垫亏损值：50 USDT
5. 保存 → 跳转「持仓详情」观察
6. 在另一终端：
   ```bash
   redis-cli XADD stream:signals:hyperliquid:0x31ca... '*' \
     payload '{"schema":"signal.v1","event_id":"test1","kind":"order_open",...}'
   ```
   或者用 signal_workers 真实订阅 Hyperliquid 链上数据
7. Execution Engine 接收 → 计算 intent → 调 CCXT 下单（testnet 才会真的发单；prod 模式需要真实 API key）
8. 「持仓详情」实时看到新增持仓

## 5 · 测试矩阵

```bash
# 全部测试
cd backend && pytest -q                 # 11/11
cd signal_workers && pytest -q          # 38/38
cd execution_engine && pytest -q        # 52/52
cd frontend && npm run build            # vue-tsc 零错误
```

总计：**101/101 测试通过**。

## 6 · 部署到生产

参考 `docs/dev_plan.md` 的「Phase 2 阶段二」清单：

1. 替换 `infra/.env` 里 `AES_KEY` / `JWT_SECRET` / `ALCHEMY_*` 为真实值
2. 用 K8s + Helm（待添加 `infra/k8s/`）或直接 docker compose + Traefik
3. 出口 IP 池：Tailscale exit node 或 Cloudflare Tunnel
4. Postgres + Redis 走托管服务（Supabase / Upstash）
5. 配置 Prometheus alertmanager + Grafana dashboard
6. Telegram bot：环境变量 `TELEGRAM_BOT_TOKEN`，bot username 配在 backend `notify-channels` 接口

## 7 · 安全提醒

- ❗ API Key 全部 AES-256-GCM 加密，密钥 `AES_KEY` 必须 32 字节且**不要进 git**
- ❗ JWT_SECRET 同上
- ❗ 用户密码 bcrypt
- ❗ 生产环境必须开 HTTPS（Traefik/nginx 反代）
- ❗ Cookie 池（Binance/币Coin）走独立加密存储 + 自动轮换
