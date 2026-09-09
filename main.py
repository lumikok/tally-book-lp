from fastapi import FastAPI,HTTPException,Depends,Header
from pydantic import BaseModel,Field
from enum import Enum
from typing import Annotated
from datetime import date
from fastapi.responses import JSONResponse
import time,asyncio,httpx
import models
from database import Base,engine,SessionLocal
from sqlalchemy import select # 构造查询语句
from sqlalchemy.orm import Session # 类型标注


# 自定义异常类
# 继承 Exception 表示这是一个异常：让FastAPI识别并处理它
class ExpenseNotFound(Exception):
    """当查不到某笔开销时抛出"""
    def __init__(self,expense_id: int):
        self.expense_id = expense_id

# 创建数据库表
Base.metadata.create_all(bind=engine) # 绑定数据库引擎，创建所有继承自 Base 的数据模型对应的表

# 数据库导入
def get_db():
    """获取数据库会话"""
    db = SessionLocal() # 创建一个数据库会话
    try:
        yield db # 生成器，返回数据库会话给调用者
    finally:
        db.close() # 关闭数据库会话，释放资源

app = FastAPI(
    title="我的记账API",
    description="从零学习FastAPI的记账系统API",
    version="0.1.0",
)

# 注册异常处理器
# 遇到 ExpenseNotFound 异常时，用这个函数处理
@app.exception_handler(ExpenseNotFound)
# 虽然 request 没有用到，主要为了保持统一的函数签名，防止以后用到
# request 是一个 Request 对象，它代表"客户端发来的整个 HTTP 请求"
async def expense_not_found_handler(request,exc: ExpenseNotFound):
    """把 ExpenseNotFound 异常统一转换成 404 响应"""
    return JSONResponse(
        status_code=404,
        content={"detail": f"未找到 id={exc.expense_id} 的开销记录"},
    ) 

# 计时器中间件
# 记录每个请求的耗时
@app.middleware("http") # http中间件
async def log_request_time(request,call_next):
    """每个请求都经过这里：记开始时间 → 放行 → 记结束时间 → 打印耗时"""
    start = time.time()
    response = await call_next(request) # 放行，获取响应进行操作后返回
    duration = time.time() - start
    print(f"[{request.method} {request.url.path}] 耗时 {duration:.3f}s")
    return response

class Category(str, Enum):
    food = "餐饮"
    transportation = "交通"
    shopping = "购物"
    entertainment = "娱乐"
    medical = "医疗"
    study = "学习"
    others = "其他"

async def verify_token(X_token: Annotated[str,Header(description="请求头中的X-Token，用于身份验证")]):
    """
    鉴权依赖：检查请求头 X-token 是否存在且值为 secret，否则抛出401异常
    """
    if X_token != "secret":
        raise HTTPException(401)
    return X_token

class Expense(BaseModel):
    amount: Annotated[float, Field(gt=0, description="支出金额必须大于0")]
    category: Category
    note: Annotated[str | None, Field(default=None,max_length=100,description="备注信息，最多100字符")]
    date: Annotated[date, Field(description="消费日期，格式为YYYY-MM-DD")]

# 入参模型和出参模型分离，方便后续扩展和维护
class ExpenseCreate(Expense):
    pass
class ExpenseOut(Expense):
    id: int


# 异步测试接口
@app.get("/demo/async-vs-sync",
         tags=["演示"],
         summary="对比同步和异步耗时",
         )
async def compare_async_sync():
    """同时请求三个接口，对比同步和异步的总耗时"""
    urls = [
        "https://httpbin.org/delay/2",  # 模拟延迟2秒的接口
        "https://httpbin.org/delay/2",
        "https://httpbin.org/delay/2"
    ]

    # 1. 同步请求，顺序执行，总耗时约6秒
    sync_start = time.time()  # 获取当前时间戳
    with httpx.Client() as client: # 同步客户端
        for url in urls:
            client.get(url)
    sync_duration = time.time() - sync_start

    # 2. 异步请求，使用 asyncio.gather 并发执行，总耗时约2秒
    async_start = time.time()
    async with httpx.AsyncClient() as client: # 异步客户端
        tasks = [client.get(url) for url in urls]
        await asyncio.gather(*tasks) # 并发执行所有任务
    async_dutation = time.time() - async_start

    return {
        "同步请求耗时": round(sync_duration, 3),
        "异步请求耗时": round(async_dutation, 3),
        "提速倍": round(sync_duration / async_dutation, 2)
    } # round 保留两位小数

# 接口1：查询开销列表，支持按分类过滤和分页（添加response_model，返回ExpenseOut列表）
@app.get(
        "/expenses",
        response_model=list[ExpenseOut],
        tags=["记账"],
        summary="查询开销列表",
        description="支持按分类筛选和分页",
    )
async def list_expenses(db: Annotated[Session, Depends(get_db)],category: Category | None = None, skip: int = 0, limit: int = 10):
    """
    查询参数说明：
    - category: 可选参数，按类别过滤支出
    - skip: 可选参数，跳过前n条记录
    - limit: 可选参数，返回每页记录数，默认10条
    """

    # 构造查询语句
    statement = select(models.Expense) # 构造查询语句

    if category:
        statement = statement.where(models.Expense.category == category.value) # 按类别过滤
    statement = statement.offset(skip).limit(limit) # 分页
    return db.scalars(statement).all() # 执行查询，返回所有结果

# 接口2：查询单笔开销
@app.get("/expenses/{expense_id}", 
         response_model=ExpenseOut,
         tags=["记账"],
         summary="查询单笔开销",
    )
async def get_expense(db: Annotated[Session, Depends(get_db)], expense_id: int):
    """
    路径参数说明：
    - expense_id: 开销记录的唯一标识符
    比如：/expenses/3 -> 返回id为3的开销记录
    """
    # 主键查询
    db_expense = db.get(models.Expense, expense_id) # 根据主键查询
    if not db_expense:
        raise ExpenseNotFound(expense_id) # 未找到
    return db_expense # 返回查询结果

# 接口3：创建开销记录
@app.post("/expenses", 
        response_model=ExpenseOut,
          tags=["记账"],
          summary="记一笔新开销",
          status_code=201  # 创建成功是201
    )
async def create_expense(db: Annotated[Session, Depends(get_db)], expense: ExpenseCreate, token: Annotated[str, Depends(verify_token)]):
    """
    请求体说明：
    - amount: 支出金额，必填
    - category: 支出类别，必填
    - note: 备注信息，选填
    - date: 支出日期，必填
    """
    db_expense = models.Expense(**expense.model_dump()) # 创建数据库模型对象
    db.add(db_expense) # 添加到会话
    db.commit() # 提交事务
    db.refresh(db_expense) # 刷新对象，获取数据库生成的id等信息
    return db_expense # 返回创建的开销记录

# 接口4：修改开销记录
@app.put("/expenses/{expense_id}",
         response_model=ExpenseOut,
        tags=["记账"],
        summary="修改一笔开销",
    )
async def update_expense(db: Annotated[Session, Depends(get_db)], expense_id: int, expense: ExpenseCreate, token: Annotated[str, Depends(verify_token)]):
    """
    路径参数说明：
    - expense_id: 开销记录的唯一标识符
    api说明：
    修改指定 id 的开销记录（整体更新）
    - expense: 请求体，包含新的开销信息
    """

    db_expense = db.get(models.Expense, expense_id) # 根据主键查询
    if not db_expense:
        raise ExpenseNotFound(expense_id) # 未找到
    for field, value in expense.model_dump().items(): # 遍历请求体的字段和值
        setattr(db_expense, field, value) # 更新数据库对象的属性
    db.commit() # 提交事务
    db.refresh(db_expense) # 刷新对象，获取数据库最新信息
    return db_expense # 返回更新后的开销记录

# 接口5：删除开销记录
@app.delete("/expenses/{expense_id}",
            tags=["记账"],
            summary="删除一笔开销",
    )
async def delete_expense(db: Annotated[Session, Depends(get_db)], expense_id: int, token: Annotated[str, Depends(verify_token)]):
    """
    路径参数说明：
    - expense_id: 开销记录的唯一标识符
    api说明：
    删除指定 id 的开销记录
    """
    db_expense = db.get(models.Expense, expense_id) # 根据主键查询
    if not db_expense:
        raise ExpenseNotFound(expense_id) # 未找到
    db.delete(db_expense) # 从会话中删除对象
    db.commit() # 提交事务
    return {"message": f"已删除开销记录，id={expense_id}", "deleted": db_expense} # 返回删除结果

