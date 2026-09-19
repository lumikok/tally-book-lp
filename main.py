from fastapi import FastAPI
from fastapi.responses import JSONResponse
import time,asyncio,httpx
from database import Base,engine
from exceptions import ExpenseNotFound # 自定义异常类
from routers import expenses # 导入路由模块
from fastapi.middleware.cors import CORSMiddleware # 允许跨域请求

# 创建数据库表
Base.metadata.create_all(bind=engine) # 绑定数据库引擎，创建所有继承自 Base 的数据模型对应的表

app = FastAPI(
    title="我的记账API",
    description="从零学习FastAPI的记账系统API",
    version="0.1.0",
)

# 允许跨域请求
# 开发期配置：允许任意来源访问，但不启用cookie和认证信息
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 允许所有来源
    allow_credentials=False, # 不允许携带cookie
    allow_methods=["*"], # 允许所有方法
    allow_headers=["*"], # 允许所有请求头
)

app.include_router(expenses.router) # 注册路由模块

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
