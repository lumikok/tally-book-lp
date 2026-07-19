from fastapi import FastAPI,HTTPException,Depends,Header
from pydantic import BaseModel,Field
from enum import Enum
from typing import Annotated
from datetime import date
from fastapi.responses import JSONResponse
import time,asyncio,httpx


# 自定义异常类
# 继承 Exception 表示这是一个异常：让FastAPI识别并处理它
class ExpenseNotFound(Exception):
    """当查不到某笔开销时抛出"""
    def __init__(self,expense_id: int):
        self.expense_id = expense_id

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
    
fake_expenses = [
    {"id": 1, "amount": 50.0, "category": Category.food,"note": "午餐", "date": "2024-06-01"},
    {"id": 2, "amount": 20.0, "category": Category.transportation,"note": "地铁", "date": "2024-06-02"},
    {"id": 3, "amount": 100.0, "category": Category.shopping,"note": "购物", "date": "2024-06-03"},
    {"id": 4, "amount": 30.0, "category": Category.entertainment,"note": "电影", "date": "2024-06-04"},
    {"id": 5, "amount": 80.0, "category": Category.medical,"note": "体检", "date": "2024-06-05"},
]

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
    date: Annotated[str, Field(description="消费日期，格式为YYYY-MM-DD")]

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
async def list_expenses(category: Category | None = None, skip: int = 0, limit: int = 10):
    """
    查询参数说明：
    - category: 可选参数，按类别过滤支出
    - skip: 可选参数，跳过前n条记录
    - limit: 可选参数，返回每页记录数，默认10条
    """
    # 1. 先按分类过滤（如果有）
    result = fake_expenses
    if category:
        result = [expense for expense in result if expense["category"] == category]
    
    # 2. 再进行分页
    return result[skip : skip + limit]

# 接口2：查询单笔开销
@app.get("/expenses/{expense_id}", 
         response_model=ExpenseOut,
         tags=["记账"],
         summary="查询单笔开销",
    )
async def get_expense(expense_id: int):
    """
    路径参数说明：
    - expense_id: 开销记录的唯一标识符
    比如：/expenses/3 -> 返回id为3的开销记录
    """
    for expense in fake_expenses:
        if expense["id"] == expense_id:
            return expense
    # return {"error": "未找到该开销记录"}  不太对：pydantic校验会失败或返回奇怪的错误信息
    raise ExpenseNotFound(expense_id) # 使用统一异常处理器，抛出异常

# 接口3：创建开销记录
@app.post("/expenses", 
        response_model=ExpenseOut,
          tags=["记账"],
          summary="记一笔新开销",
          status_code=201  # 创建成功是201
    )
async def create_expense(expense: ExpenseCreate,token: Annotated[str,Depends(verify_token)]):
    """
    请求体说明：
    - amount: 支出金额，必填
    - category: 支出类别，必填
    - note: 备注信息，选填
    - date: 支出日期，必填（简化为字符串）
    """
    new_id = max(expense["id"] for expense in fake_expenses) + 1
    new_expense = {"id": new_id, **expense.model_dump()} # 将Pydantic模型转换为字典，并添加id字段
    fake_expenses.append(new_expense) # 模拟数据库存储
    return new_expense # 返回创建的开销记录

# 接口4：修改开销记录
@app.put("/expenses/{expense_id}",
         response_model=ExpenseOut,
        tags=["记账"],
        summary="修改一笔开销",
    )
async def update_expense(expense_id: int, expense: ExpenseCreate,token: Annotated[str,Depends(verify_token)]):
    """
    路径参数说明：
    - expense_id: 开销记录的唯一标识符
    api说明：
    修改指定 id 的开销记录（整体更新）
    - expense: 请求体，包含新的开销信息
    """

    for i,e in enumerate(fake_expenses):
        if e["id"] == expense_id:
            updated_expense = {"id": expense_id, **expense.model_dump()}
            fake_expenses[i] = updated_expense
            return updated_expense
    raise ExpenseNotFound(expense_id) # 未找到

# 接口5：删除开销记录
@app.delete("/expenses/{expense_id}",
            tags=["记账"],
            summary="删除一笔开销",
    )
async def delete_expense(expense_id: int,token: Annotated[str,Depends(verify_token)]):
    """
    路径参数说明：
    - expense_id: 开销记录的唯一标识符
    api说明：
    删除指定 id 的开销记录
    """
    for i,e in enumerate(fake_expenses):
        if e["id"] == expense_id:
            deleted_expense = fake_expenses.pop(i)
            return {"message": f"已删除开销记录，id={expense_id}", "deleted": deleted_expense}
    raise ExpenseNotFound(expense_id) # 未找到
    

