# tally-book

这是一个教学项目（个人使用），主要用于学习和检验FastAPI框架以及基础前端知识。实现了一个简单的记账本业务逻辑。

## 已实现功能

- 开销的新增、查询、修改和删除
- 分类筛选与分页
- 分类支出占比图
- 每日支出趋势图
- 响应式页面
- FastAPI 单端口访问

## 技术栈

```text
backend: FastAPI, SQLAlchemy, Pydantic, SQLite
frontend: HTML,CSS,JavaScript, ECharts
```

## 启动方式

### 1. 克隆项目到本地

```bash
git clone https://github.com/lumikok/tally-book-lp.git
cd tally-book-lp
```

### 2. 准备 Python 和 uv

项目需要 Python 3.14 或更高版本，并使用 uv 管理虚拟环境和依赖。

如果尚未安装 uv，可在 Windows PowerShell 中运行：

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

其他系统请参考 [uv 官方安装文档](https://docs.astral.sh/uv/getting-started/installation/)。

### 3. 安装项目依赖

```bash
uv sync
```

`uv sync` 会根据 `pyproject.toml` 和 `uv.lock` 创建虚拟环境并安装项目所需依赖。

### 4. 启动服务

```bash
uv run fastapi dev main.py
```

### 访问方式

```text
页面：http://127.0.0.1:8000/
API文档：http://127.0.0.1:8000/docs
```

## 项目结构

```text
tally-book
├─ main.py
├─ models.py
├─ schemas.py
├─ exceptions.py
├─ dependencies.py
├─ database.py
├─ routers
│  ├─ __init__.py
│  ├─ expenses.py
│  └─ summary.py
├─ frontend
│  ├─ index.html
│  ├─ style.css
│  └─ app.js
└─ pyproject.toml
```

### 说明

- `main.py`：FastAPI应用的入口文件，包含路由注册和中间件配置。
- `models.py`：定义数据库模型。
- `schemas.py`：定义数据验证和序列化的Pydantic模型。
- `exceptions.py`：自定义异常处理。
- `dependencies.py`：定义依赖项，如数据库会话。
- `database.py`：定义数据库连接和操作。
- `routers/expenses.py`：处理开销相关的API路由。
- `routers/summary.py`：处理统计相关的API路由。
- `frontend/`：包含前端页面和静态资源。
- `index.html`：前端页面的主入口。
- `style.css`：前端页面的样式文件。
- `app.js`：前端页面的JavaScript逻辑文件。
- `pyproject.toml`：项目的配置文件，包含依赖项和构建配置。
