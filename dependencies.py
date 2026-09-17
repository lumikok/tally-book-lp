# 文件内容：
# 依赖项文件：定义了FastAPI应用程序中使用的依赖项函数

from fastapi import Header,HTTPException
from typing import Annotated
from database import SessionLocal

def get_db():
    """获取数据库会话"""
    db = SessionLocal() # 创建一个数据库会话
    try:
        yield db # 生成器，返回数据库会话给调用者
    finally:
        db.close() # 关闭数据库会话，释放资源

async def verify_token(X_token: Annotated[str,Header(description="请求头中的X-Token，用于身份验证")]):
    """
    鉴权依赖：检查请求头 X-token 是否存在且值为 secret，否则抛出401异常
    """
    if X_token != "secret":
        raise HTTPException(401)
    return X_token