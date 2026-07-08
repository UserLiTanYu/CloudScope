# CloudScope

CloudScope 是一个基于监控采集数据的可视化大屏项目。当前采用方案 1：

```text
Vue 3 + TypeScript + Vite + ECharts
FastAPI + SQLAlchemy + Python ETL
MySQL 8
pytest + Vitest
ruff + ESLint + Prettier
```

## 数据来源

默认读取目录：

```text
C:\Users\litan\Desktop\code\可视化大屏\数据
```

包含：

- `host_detail.dat`：主机维表
- `mod_detail.dat`：指标字典维表
- `disk_tsar.dat`：磁盘采集明细
- `pref_tsar.dat`：性能采集明细

## 项目结构

```text
CloudScope/
├─ backend/
│  ├─ app/                  # FastAPI 应用
│  │  ├─ api/               # HTTP 接口
│  │  ├─ core/              # 配置、数据库、日志
│  │  ├─ models/            # SQLAlchemy 模型
│  │  ├─ repositories/      # 数据访问层
│  │  ├─ schemas/           # Pydantic 响应模型
│  │  └─ services/          # 业务服务层
│  ├─ etl/                  # 数据加工入库
│  │  ├─ readers/           # 文件读取
│  │  ├─ transformers/      # 数据清洗转换
│  │  ├─ loaders/           # MySQL 写入
│  │  └─ jobs/              # 导入任务入口
│  └─ tests/                # 后端测试
├─ frontend/
│  ├─ src/
│  │  ├─ api/
│  │  ├─ charts/
│  │  ├─ components/
│  │  ├─ stores/
│  │  ├─ styles/
│  │  └─ views/
│  └─ tests/
├─ database/
│  ├─ schema.sql
│  └─ migrations/
├─ logs/
└─ docker-compose.yml
```

## 启动 MySQL

```bash
docker compose up -d mysql
```

如果不使用 Docker，也可以手动执行：

```bash
mysql -uroot -p < database/schema.sql
```

## 后端开发

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

健康检查：

```text
http://127.0.0.1:8000/api/health
```

## 导入数据

```bash
cd backend
python -m etl.jobs.import_data
```

也可以指定数据目录：

```bash
python -m etl.jobs.import_data --data-dir "C:\Users\litan\Desktop\code\可视化大屏\数据"
```

## 前端开发

```bash
cd frontend
npm install
npm run dev
```

默认访问：

```text
http://127.0.0.1:5173
```

## 测试与代码质量

后端：

```bash
cd backend
pytest
pytest --cov=app --cov=etl --cov-report=term-missing
ruff check .
mypy .
```

前端：

```bash
cd frontend
npm run test
npm run lint
npm run build
```

日志默认写入：

```text
logs/cloudscope.log
```

本项目 Docker MySQL 默认发布到宿主机：

```text
127.0.0.1:3307
```
