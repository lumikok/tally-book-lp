from sqlalchemy import Column,Float,Integer,String,Date

from database import Base

class Expense(Base):
    __tablename__ = "expenses"  # 表名

    id = Column(Integer, primary_key=True, index=True)  # 主键
    amount = Column(Float, nullable=False)  # 金额
    category = Column(String,nullable=False) # 种类
    note = Column(String(100)) # 注释
    date = Column(Date,nullable=False) # 日期
    
