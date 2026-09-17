# 文件内容：
# 放置所有的枚举类 

from enum import Enum
from pydantic import BaseModel,Field
from typing import Annotated
from datetime import date

class Category(str, Enum):
    """
    开销类别枚举类
    """
    food = "餐饮"
    transportation = "交通"
    shopping = "购物"
    entertainment = "娱乐"
    medical = "医疗"
    study = "学习"
    others = "其他"

class Expense(BaseModel):
    """
    开销记录模型
    """
    amount: Annotated[float, Field(gt=0, description="支出金额必须大于0")]
    category: Category
    note: Annotated[str | None, Field(default=None,max_length=100,description="备注信息，最多100字符")]
    date: Annotated[date, Field(description="消费日期，格式为YYYY-MM-DD")]

class ExpenseCreate(Expense):
    """
    创建开销记录的入参模型
    """
    pass

class ExpenseOut(Expense):
    """
    创建开销记录的出参模型
    """
    id: int