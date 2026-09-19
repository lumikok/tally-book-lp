# 文件内容：
# 路由

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Annotated
from schemas import ExpenseCreate, ExpenseOut, Category
from dependencies import get_db, verify_token
from exceptions import ExpenseNotFound
import models

router = APIRouter(prefix="/expenses", tags=["记账"])

# 接口1：查询开销列表，支持按分类过滤和分页（添加response_model，返回ExpenseOut列表）
@router.get(
        "",
        response_model=list[ExpenseOut],
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
@router.get("/{expense_id}", 
         response_model=ExpenseOut,
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
@router.post("", 
        response_model=ExpenseOut,
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
@router.put("/{expense_id}",
         response_model=ExpenseOut,
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
@router.delete("/{expense_id}",
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