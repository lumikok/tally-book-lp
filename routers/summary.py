# 文件内容：
# 

from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import Annotated
from dependencies import get_db
import models


router = APIRouter(prefix="/summary", tags=["统计"])

@router.get("/total", summary="查询总支出")
async def get_total(
    db: Annotated[Session, Depends(get_db)],
    start: date | None = None,
    end: date | None = None,
):
    """
    查询总支出，支持按时间范围过滤
    """
    statement = select(func.sum(models.Expense.amount))  # 构造查询语句，计算总支出

    if start:
        statement = statement.where(models.Expense.date >= start)

    if end:
        statement = statement.where(models.Expense.date <= end)

    total = db.scalar(statement) or 0.0  # 执行查询，返回总支出

    return {"total": round(total,2)}  # 返回总支出，保留两位小数

@router.get("/category", summary="按分类统计支出")
async def get_category(
    db: Annotated[Session, Depends(get_db)],
):
    """
    按分类统计支出，返回每个分类的总支出和数量
    """
    statement = (
        select(
            models.Expense.category,
            func.sum(models.Expense.amount).label("amount"),
            func.count(models.Expense.id).label("count"),
        ).group_by(models.Expense.category)  # 按分类分组
    )
    rows = db.execute(statement).all()  # 执行查询，返回所有结果

    result = [
        {
            "category": row.category,
            "amount": round(row.amount, 2),
            "count": row.count,
        }
        for row in rows
    ]
    return result  # 返回按分类统计的结果

@router.get("/daily", summary="按天统计支出")
async def get_daily(
    db: Annotated[Session, Depends(get_db)],
):
    """
    按天统计支出，返回每天的总支出
    """
    statement = (
        select(
            models.Expense.date,
            func.sum(models.Expense.amount).label("amount"),
        ).group_by(models.Expense.date)  # 按日期分组
         .order_by(models.Expense.date)  # 按日期排序
    )
    rows = db.execute(statement).all()  # 执行查询，返回所有结果

    result = [
        {
            "date": row.date,
            "amount": round(row.amount, 2)
        }
        for row in rows
    ]
    return result  # 返回按天统计的结果