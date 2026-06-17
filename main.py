from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field
from enum import Enum
from typing import Annotated
from datetime import date

app = FastAPI(
    title="我的记账API",
    description="从零学习FastAPI的记账系统API",
    version="0.1.0",
)

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

# 接口1：查询开销列表，支持按分类过滤和分页（添加response_model，返回ExpenseOut列表）
@app.get("/expenses", response_model=list[ExpenseOut])
def list_expenses(category: Category | None = None, skip: int = 0, limit: int = 10):
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
@app.get("/expenses/{expense_id}", response_model=ExpenseOut)
def get_expense(expense_id: int):
    """
    路径参数说明：
    - expense_id: 开销记录的唯一标识符
    比如：/expenses/3 -> 返回id为3的开销记录
    """
    for expense in fake_expenses:
        if expense["id"] == expense_id:
            return expense
    # return {"error": "未找到该开销记录"}  不太对：pydantic校验会失败或返回奇怪的错误信息
    raise HTTPException(status_code=404, detail="未找到该开销记录") # 手动抛出404异常，触发FastAPI的异常处理

# 接口3：创建开销记录
@app.post("/expenses", response_model=ExpenseOut)
def create_expense(expense: ExpenseCreate):
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
@app.put("/expenses/{expense_id}", response_model=ExpenseOut)
def update_expense(expense_id: int, expense: ExpenseCreate):
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
    raise HTTPException(status_code=404, detail="未找到该开销记录") 

# 接口5：删除开销记录
@app.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: int):
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
    raise HTTPException(status_code=404, detail="未找到该开销记录")
    

