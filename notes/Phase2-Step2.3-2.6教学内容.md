# Phase 2 后续步骤教学（Step 2.3 ~ 2.6）

> 本文档是离线教学材料，照着做即可。遇到问题随时问老师。
> 前置：已完成 Step 2.1（依赖注入）和 Step 2.2（异常/中间件/接口配置）。

---

## 📖 Step 2.3：异步 async/await ⭐ Phase 2 重头戏

### 🎯 目标
理解 **async/await**，这是后面**调用 LLM 的命脉**。不懂异步，写 Agent 时一个慢请求就能卡死整个服务器。

### 📚 读官方文档（必读，建议反复读）
- **Concurrency / Async Await** → https://fastapi.tiangolo.com/zh/async/

---

### 🔑 核心概念 1：同步 vs 异步

#### 同步（sync）：排队干活
```python
import time

def task(name, seconds):
    print(f"{name} 开始")
    time.sleep(seconds)          # 阻塞！干等
    print(f"{name} 结束")

# 顺序执行，总耗时 = 1+2+1 = 4 秒
task("A", 1)
task("B", 2)
task("C", 1)
```

#### 异步（async）：等待时去干别的
```python
import asyncio

async def task(name, seconds):
    print(f"{name} 开始")
    await asyncio.sleep(seconds)  # 非阻塞！等待时让出 CPU
    print(f"{name} 结束")

# 并发执行，总耗时 ≈ max(1,2,1) = 2 秒
asyncio.run(asyncio.gather(task("A", 1), task("B", 2), task("C", 1)))
```

**关键区别**：`time.sleep` 是**干等**（占着 CPU 不放），`await asyncio.sleep` 是**边等边干别的**（等待时让出 CPU 给别的任务）。

### 🔑 核心概念 2：`async def` vs `def` 在 FastAPI 里

FastAPI 对两种函数的处理不同：

| 函数类型 | FastAPI 怎么处理 | 什么时候用 |
|---------|-----------------|-----------|
| `async def` | 直接在事件循环里运行 | 你的代码是异步的（用了 `await`、异步库）|
| `def`（普通）| 扔到线程池里运行，避免阻塞 | 你的代码是同步的（用了 `time.sleep`、同步库）|

**经验法则**：
- 用了 `await`、异步库（`httpx.AsyncClient`、`AsyncOpenAI`）→ **`async def`**
- 用了阻塞库（`requests`、同步 `openai`、`time.sleep`）→ **`def`**（FastAPI 自动放线程池）
- 都没用，纯计算 → **随便**，推荐 `async def`

### 🔑 核心概念 3：⚠️ async def 里千万别写阻塞代码

**这是新手最大的坑**：

```python
@app.get("/bad")
async def bad():
    time.sleep(5)            # ❌ 阻塞！整个服务器卡 5 秒，其他请求全排队
    return {"msg": "done"}

@app.get("/good")
async def good():
    await asyncio.sleep(5)   # ✅ 非阻塞，等待时能处理别的请求
    return {"msg": "done"}
```

> 💡 **为什么这是 Agent 工程师的命脉**：调用 LLM API 要等几秒甚至几十秒。如果你用同步阻塞写法，一个用户调用 LLM，整个服务器就卡住了，其他用户全排队。用异步，等 LLM 的时候还能服务别人。

### ✍️ 动手任务：用 httpx 异步请求一个公开 API

#### Step 2.3.1　安装 httpx
```cmd
uv add httpx
```

#### Step 2.3.2　写一个异步接口测试

在 `main.py` 加一个测试接口（和记账接口并列）：

```python
import asyncio
import httpx

# ===== 异步测试接口 =====
@app.get("/demo/async-vs-sync", tags=["演示"], summary="对比同步和异步的耗时")
async def compare_async_sync():
    """同时请求 3 个接口，对比同步 vs 异步的总耗时"""
    urls = [
        "https://httpbin.org/delay/1",   # 这个接口会延迟 1 秒返回
        "https://httpbin.org/delay/1",
        "https://httpbin.org/delay/1",
    ]

    # 1. 同步写法：顺序请求，总耗时 ≈ 3 秒
    sync_start = time.time()
    with httpx.Client() as client:
        for url in urls:
            client.get(url)
    sync_duration = time.time() - sync_start

    # 2. 异步写法：并发请求，总耗时 ≈ 1 秒
    async_start = time.time()
    async with httpx.AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        await asyncio.gather(*tasks)      # 并发执行所有请求
    async_duration = time.time() - async_start

    return {
        "同步耗时_秒": round(sync_duration, 2),
        "异步耗时_秒": round(async_duration, 2),
        "提速倍数": round(sync_duration / async_duration, 1),
    }
```

#### Step 2.3.3　测试
访问 `http://127.0.0.1:8000/demo/async-vs-sync`，你会看到类似：
```json
{
  "同步耗时_秒": 3.12,
  "异步耗时_秒": 1.05,
  "提速倍数": 3.0
}
```

**3 倍提速！** 这就是异步的威力。3 个请求同时等，而不是排队等。

### 🧪 Step 2.3 通关检查
- [ ] 能解释 `time.sleep` 和 `await asyncio.sleep` 的区别
- [ ] 能解释为什么 `async def` 里不能写阻塞代码
- [ ] demo 接口返回的异步耗时明显小于同步耗时

### 📝 commit
```cmd
git add .
git commit -m "feat(phase2): Step2.3 异步 async/await，加同步异步对比 demo"
```

---

## 📖 Step 2.4：数据库（SQLite + SQLAlchemy）

### 🎯 目标
把内存 list 换成真数据库，**重启服务器数据不丢**。这是从"玩具"到"产品"的关键一步。

### 📚 读官方文档
- **SQL Databases** → https://fastapi.tiangolo.com/zh/tutorial/sql-databases/
- （注意：官方文档用的是同步 SQLAlchemy，我们用更现代的写法）

---

### 🔑 核心概念

#### 1️⃣ ORM（对象关系映射）
不用写 SQL，用 Python 类操作数据库：
```python
# 传统 SQL
cursor.execute("SELECT * FROM expenses WHERE id = 1")

# ORM（SQLAlchemy）
expense = db.query(Expense).filter(Expense.id == 1).first()
```
**好处**：面向对象、防 SQL 注入、跨数据库。

#### 2️⃣ SQLite
一个文件就是一个数据库，**零配置**。适合学习和中小项目。我们的数据库就是 `tally.db` 一个文件。

#### 3️⃣ Session
数据库连接的"会话"。每个请求开一个 session，用完关掉。用**依赖注入 + yield** 管理（经典模式）。

### ✍️ 动手任务

#### Step 2.4.1　安装 SQLAlchemy
```cmd
uv add sqlalchemy
```

#### Step 2.4.2　新建 `database.py` 文件（注意是新文件，不在 main.py 里）

```python
# database.py —— 数据库连接配置
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite 数据库文件地址（会在项目根目录生成 tally.db）
SQLALCHEMY_DATABASE_URL = "sqlite:///./tally.db"

# 创建引擎（connect_args 是 SQLite 专用配置）
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite 多线程需要
)

# Session 工厂：每个请求创建一个独立 session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ORM 模型的基类，所有表模型都继承它
Base = declarative_base()
```

#### Step 2.4.3　新建 `models.py` 文件（ORM 表定义）

```python
# models.py —— ORM 模型（数据库表结构）
from sqlalchemy import Column, Integer, Float, String, Date
from database import Base


class Expense(Base):
    """expenses 表：对应一笔开销"""
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)   # 主键，自增
    amount = Column(Float, nullable=False)                # 金额，不能为空
    category = Column(String, nullable=False)             # 分类
    note = Column(String, default="")                     # 备注，默认空
    paid_at = Column(Date, nullable=False)                # 消费日期
```

> ⚠️ 注意：`models.py`（ORM 表）和 `schemas.py`（pydantic 校验）**是两个东西**，别搞混：
> - `models.py` 定义**数据库表长什么样**
> - `schemas.py` 定义 **API 收发数据长什么样**（你 Phase 1 的 ExpenseCreate/ExpenseOut）
> - Phase 2.5 会把 schemas 拆出去，现在先放 main.py

#### Step 2.4.4　在 `main.py` 顶部接入数据库

```python
import time
from datetime import date
from enum import Enum
from typing import Annotated

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import engine, Base, SessionLocal
import models

# 启动时创建所有表（如果不存在）
models.Base.metadata.create_all(bind=engine)   # ← 注意，models.py 里如果 Base 是从 database 导入的，就用 Base.metadata.create_all
# 更稳妥的写法：在 database.py 里定义 Base，models.py 里 from database import Base
# 然后 main.py 里：Base.metadata.create_all(bind=engine)
```

> 💡 建议把 `Base` 定义在 `database.py`，`models.py` 里 `from database import Base`，这样 `main.py` 直接 `Base.metadata.create_all(bind=engine)` 就行。上面 `models.py` 已经这么写了。

#### Step 2.4.5　加一个"获取数据库 session"的依赖

在 `main.py` 加：

```python
# ===== 数据库依赖 =====
# yield 模式：请求开始时 yield 一个 session，请求结束后自动关闭
def get_db():
    db = SessionLocal()
    try:
        yield db            # 把 session 给接口用
    finally:
        db.close()          # 无论成功失败都关闭
```

**`yield` 依赖的工作原理**：
- 请求来 → 执行到 `yield`，把 db 给接口
- 接口执行完 → 执行 `finally` 里的 `db.close()`
- **FastAPI 自动管理这个生命周期**

#### Step 2.4.6　把 CRUD 接口改成用数据库

这是改动最大的一步。现在每个接口要：
1. 加一个 `db: Session = Depends(get_db)` 参数
2. 用 ORM 操作数据库代替 list 操作

以几个接口为例：

```python
# 列表（带筛选分页）
@app.get(
    "/expenses",
    response_model=list[ExpenseOut],
    tags=["记账"],
    summary="查询开销列表",
)
def list_expenses(
    category: Category | None = None,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    query = db.query(models.Expense)
    if category:
        query = query.filter(models.Expense.category == category.value)
    return query.offset(skip).limit(limit).all()


# 单个查询
@app.get("/expenses/{expense_id}", response_model=ExpenseOut, tags=["记账"], summary="查询单笔")
def get_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not expense:
        raise ExpenseNotFound(expense_id)
    return expense


# 创建
@app.post("/expenses", response_model=ExpenseOut, tags=["记账"], summary="记一笔", status_code=201)
def create_expense(
    expense: ExpenseCreate,
    token: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    # 用 expense.model_dump() 拿到字典，创建 ORM 对象
    db_expense = models.Expense(**expense.model_dump())
    db.add(db_expense)          # 添加到 session
    db.commit()                 # 提交到数据库
    db.refresh(db_expense)      # 刷新，拿到数据库生成的 id
    return db_expense


# 修改
@app.put("/expenses/{expense_id}", response_model=ExpenseOut, tags=["记账"], summary="修改")
def update_expense(
    expense_id: int,
    expense: ExpenseCreate,
    token: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    db_expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not db_expense:
        raise ExpenseNotFound(expense_id)
    # 把新数据写到 ORM 对象上
    for field, value in expense.model_dump().items():
        setattr(db_expense, field, value)
    db.commit()
    db.refresh(db_expense)
    return db_expense


# 删除
@app.delete("/expenses/{expense_id}", tags=["记账"], summary="删除")
def delete_expense(
    expense_id: int,
    token: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    db_expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not db_expense:
        raise ExpenseNotFound(expense_id)
    db.delete(db_expense)
    db.commit()
    return {"message": f"已删除 id={expense_id}"}
```

#### Step 2.4.7　删掉 `fake_expenses` 假数据
现在用数据库了，把 `fake_expenses = [...]` 整个删掉。

#### Step 2.4.8　把 `tally.db` 加进 `.gitignore`
数据库文件不该提交到 Git：
```
# 数据库
*.db
```

#### Step 2.4.9　更新 `Expense` 模型里的 `category`
因为现在 `models.py` 里 category 存的是字符串，你的 `Category` 枚举值要匹配。查询时用 `category.value`（枚举的字符串值）。

### 🧪 Step 2.4 通关检查
- [ ] 重启服务器，数据还在（关键！）
- [ ] CRUD 都正常
- [ ] 项目目录下生成了 `tally.db` 文件
- [ ] `tally.db` 没被提交到 Git

### 📝 commit
```cmd
git add .
git commit -m "feat(phase2): Step2.4 接入 SQLite + SQLAlchemy，数据持久化"
```

---

## 📖 Step 2.5：项目结构拆分 + APIRouter

### 🎯 目标
随着代码变多，全堆在 `main.py` 里会很乱。拆成多个文件，用 **APIRouter** 组织路由。

### 📚 读官方文档
- **Bigger Applications** → https://fastapi.tiangolo.com/zh/tutorial/bigger-applications/
- **CORS** → https://fastapi.tiangolo.com/zh/tutorial/cors/

---

### 🔑 核心概念

#### APIRouter
类似"小号的 app"，把一组相关路由打包到一个文件，最后在 main.py 里"挂载"。

#### 目标项目结构
```
02_test/
├── main.py              # 入口：创建 app，挂载 router，配 CORS
├── database.py          # 数据库连接
├── models.py            # ORM 表
├── schemas.py           # pydantic 模型（从 main.py 搬过来）
├── crud.py              # 数据库操作函数（可选，让接口更瘦）
├── dependencies.py      # 公共依赖（verify_token 等）
├── routers/
│   ├── __init__.py
│   ├── expenses.py      # 记账路由
│   └── summary.py       # 统计路由（Step 2.6 用）
└── notes/               # 学习笔记
```

### ✍️ 动手任务

#### Step 2.5.1　拆 schemas
新建 `schemas.py`，把 `Expense`、`ExpenseCreate`、`ExpenseOut` 从 main.py 搬过来：

```python
# schemas.py —— pydantic 模型（API 数据结构）
from datetime import date
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field


class Category(str, Enum):
    餐饮 = "餐饮"
    交通 = "交通"
    购物 = "购物"
    娱乐 = "娱乐"
    学习 = "学习"
    医疗 = "医疗"
    其他 = "其他"


class Expense(BaseModel):
    amount: Annotated[float, Field(gt=0, description="金额，必须大于 0")]
    category: Category
    note: Annotated[str, Field(default="", max_length=100)]
    paid_at: Annotated[date, Field(description="消费日期")]


class ExpenseCreate(Expense):
    pass


class ExpenseOut(Expense):
    id: int
```

#### Step 2.5.2　拆 dependencies
新建 `dependencies.py`：

```python
# dependencies.py —— 公共依赖
from fastapi import Header, HTTPException


def verify_token(x_token: str = Header(...)):
    if x_token != "secret":
        raise HTTPException(status_code=401, detail="Token 无效")
    return x_token


def get_db():
    from database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### Step 2.5.3　建 routers 文件夹
新建 `routers/__init__.py`（空文件）和 `routers/expenses.py`：

```python
# routers/expenses.py —— 记账路由
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import schemas
from dependencies import verify_token, get_db
from main import ExpenseNotFound   # ⚠️ 循环导入警告！见下方说明

router = APIRouter(prefix="/expenses", tags=["记账"])


@router.get("", response_model=list[schemas.ExpenseOut], summary="查询开销列表")
def list_expenses(
    category: schemas.Category | None = None,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    query = db.query(models.Expense)
    if category:
        query = query.filter(models.Expense.category == category.value)
    return query.offset(skip).limit(limit).all()


@router.get("/{expense_id}", response_model=schemas.ExpenseOut, summary="查询单笔")
def get_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not expense:
        raise ExpenseNotFound(expense_id)
    return expense


@router.post("", response_model=schemas.ExpenseOut, summary="记一笔", status_code=201)
def create_expense(
    expense: schemas.ExpenseCreate,
    token: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    db_expense = models.Expense(**expense.model_dump())
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense


@router.put("/{expense_id}", response_model=schemas.ExpenseOut, summary="修改")
def update_expense(
    expense_id: int,
    expense: schemas.ExpenseCreate,
    token: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    db_expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not db_expense:
        raise ExpenseNotFound(expense_id)
    for field, value in expense.model_dump().items():
        setattr(db_expense, field, value)
    db.commit()
    db.refresh(db_expense)
    return db_expense


@router.delete("/{expense_id}", summary="删除")
def delete_expense(
    expense_id: int,
    token: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    db_expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not db_expense:
        raise ExpenseNotFound(expense_id)
    db.delete(db_expense)
    db.commit()
    return {"message": f"已删除 id={expense_id}"}
```

> ⚠️ **循环导入问题**：`routers/expenses.py` 里 `from main import ExpenseNotFound`，而 `main.py` 里又要 `from routers.expenses import router`。这会循环。**解决办法**：把 `ExpenseNotFound` 异常类放到 `dependencies.py` 或单独的 `exceptions.py`。

#### Step 2.5.4　把异常类抽出来
新建 `exceptions.py`：

```python
# exceptions.py —— 自定义异常
class ExpenseNotFound(Exception):
    def __init__(self, expense_id: int):
        self.expense_id = expense_id
```

然后 `routers/expenses.py` 改成 `from exceptions import ExpenseNotFound`。

#### Step 2.5.5　精简 main.py
现在的 `main.py` 应该很短：

```python
# main.py —— 应用入口
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from database import engine, Base
from routers import expenses
from exceptions import ExpenseNotFound

# 创建表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="我的记账API",
    description="从零学习FastAPI的记账系统API",
    version="0.1.0",
)


# ===== CORS 配置（Phase 3 接前端必备！）=====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # 开发阶段允许所有来源（生产环境要改成具体域名）
    allow_credentials=True,
    allow_methods=["*"],          # 允许所有 HTTP 方法
    allow_headers=["*"],          # 允许所有请求头
)


# ===== 异常处理器 =====
@app.exception_handler(ExpenseNotFound)
async def expense_not_found_handler(request: Request, exc: ExpenseNotFound):
    return JSONResponse(
        status_code=404,
        content={"detail": f"未找到 id={exc.expense_id} 的开销记录"},
    )


# ===== 中间件：记录耗时 =====
@app.middleware("http")
async def log_request_time(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    print(f"[{request.method} {request.url.path}] 耗时 {duration:.3f}s")
    return response


# ===== 挂载路由 =====
app.include_router(expenses.router)
```

### 🧪 Step 2.5 通关检查
- [ ] 所有接口还正常工作
- [ ] `/docs` 里接口还归在"记账"组
- [ ] main.py 变得很短，只剩配置
- [ ] CORS 配置生效（前端能调通，Step 2.3 的 demo 也能调）

### 📝 commit
```cmd
git add .
git commit -m "feat(phase2): Step2.5 拆分项目结构，用 APIRouter 组织路由，配 CORS"
```

---

## 📖 Step 2.6：⭐ 统计接口（记账 API 的灵魂，也是 Phase 3 图表数据源）

### 🎯 目标
做 3 个统计接口，让记账 API 从"CRUD 练习"变成"有点意思的小产品"，**同时为 Phase 3 的图表准备数据**。

### 📚 学习资料
- SQL 聚合：`GROUP BY` / `SUM` / `COUNT`
- SQLAlchemy 聚合查询写法

---

### 🔑 核心概念：聚合查询

把多行数据"汇总"成统计结果。比如：
- **求和**：所有开销加起来多少？
- **分组**：每个分类加起来多少？
- **计数**：每个分类有几笔？

SQL 写法：
```sql
SELECT category, SUM(amount) FROM expenses GROUP BY category;
```

SQLAlchemy 写法：
```python
from sqlalchemy import func

db.query(
    models.Expense.category,
    func.sum(models.Expense.amount)
).group_by(models.Expense.category).all()
```

### ✍️ 动手任务

新建 `routers/summary.py`：

```python
# routers/summary.py —— 统计接口
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import schemas
from dependencies import get_db

router = APIRouter(prefix="/summary", tags=["统计"])


@router.get("/total", summary="总支出")
def get_total(
    start: date | None = None,
    end: date | None = None,
    db: Session = Depends(get_db),
):
    """总支出，可选按时间段筛选"""
    query = db.query(func.sum(models.Expense.amount))
    if start:
        query = query.filter(models.Expense.paid_at >= start)
    if end:
        query = query.filter(models.Expense.paid_at <= end)
    total = query.scalar() or 0.0       # scalar() 取单个值，None 兜底成 0
    return {"total": round(total, 2)}


@router.get("/category", summary="分类汇总（饼图数据）")
def get_category_summary(db: Session = Depends(get_db)):
    """各分类支出占比，返回适合画饼图的格式"""
    results = (
        db.query(
            models.Expense.category,
            func.sum(models.Expense.amount).label("amount"),
            func.count(models.Expense.id).label("count"),
        )
        .group_by(models.Expense.category)
        .all()
    )
    return [
        {"category": cat, "amount": round(amt, 2), "count": cnt}
        for cat, amt, cnt in results
    ]


@router.get("/daily", summary="每日趋势（折线图数据）")
def get_daily_summary(db: Session = Depends(get_db)):
    """按天汇总支出，返回适合画折线图的格式"""
    results = (
        db.query(
            models.Expense.paid_at,
            func.sum(models.Expense.amount).label("amount"),
        )
        .group_by(models.Expense.paid_at)
        .order_by(models.Expense.paid_at)
        .all()
    )
    return [
        {"date": day.isoformat(), "amount": round(amt, 2)}
        for day, amt in results
    ]
```

然后 `main.py` 里挂载：
```python
from routers import expenses, summary

app.include_router(expenses.router)
app.include_router(summary.router)
```

### 🧪 Step 2.6 通关检查
- [ ] `GET /summary/total` 返回总支出
- [ ] `GET /summary/total?start=2024-06-01&end=2024-06-30` 按时间段筛选
- [ ] `GET /summary/category` 返回各分类占比（Phase 3 饼图用这个）
- [ ] `GET /summary/daily` 返回每日趋势（Phase 3 折线图用这个）
- [ ] `/docs` 里多了"统计"分组

### 📝 commit
```cmd
git add .
git commit -m "feat(phase2): Step2.6 统计接口（总额/分类汇总/每日趋势）"
git tag phase2-done
```

🎉 **Phase 2 全部完成！** 现在你有了一个：
- 数据持久化的记账 API
- 用依赖注入做鉴权
- 异步处理（为 LLM 准备）
- 项目结构清晰
- 带统计接口（为前端图表准备）

下一步就可以进 **Phase 3 前端可视化** 了。

---

## 💡 自学小贴士

1. **每做完一个 Step 先测通再 commit**，别攒一堆改动一起提交。
2. **遇到报错先读错误信息**，FastAPI 的报错通常很清楚。
3. **拆分文件后注意循环导入**，这是这阶段最常见的坑。
4. **数据库操作记得 `commit()`**，否则数据没真存进去。
5. **CORS 的 `allow_origins=["*"]` 只是开发用**，上线要改。

---

**遇到任何问题，把报错或现象贴给老师，随时问。** 💪
