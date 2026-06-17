from fastapi import FastAPI
from pydantic import BaseModel
app = FastAPI(
    title="我的记账API",
    description="从零学习FastAPI的记账系统API",
    version="0.1.0",
)

fake_expenses = [
    {"id": 1, "amount": 50.0, "category": "餐饮","note": "午餐", "date": "2024-06-01"},
    {"id": 2, "amount": 20.0, "category": "交通","note": "地铁", "date": "2024-06-02"},
    {"id": 3, "amount": 100.0, "category": "购物","note": "购物", "date": "2024-06-03"},
    {"id": 4, "amount": 30.0, "category": "娱乐","note": "电影", "date": "2024-06-04"},
    {"id": 5, "amount": 80.0, "category": "医疗","note": "体检", "date": "2024-06-05"},
]

class Expense(BaseModel):
    amount: float
    category: str
    note: str | None = None
    date: str # 暂时简化

@app.get("/expenses")
def list_expenses(category: str | None = None, skip: int = 0, limit: int = 10):
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
@app.get("/expenses/{expense_id}")
def get_expense(expense_id: int):
    """
    路径参数说明：
    - expense_id: 开销记录的唯一标识符
    比如：/expenses/3 -> 返回id为3的开销记录
    """
    for expense in fake_expenses:
        if expense["id"] == expense_id:
            return expense
    return {"error": "未找到该开销记录"}

@app.post("/expenses")
def create_expense(expense: Expense):
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

