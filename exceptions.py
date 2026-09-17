# 文件内容：
# 异常类

# 开销记录不存在时抛出的业务异常
class ExpenseNotFound(Exception):
    """
    当查不到某笔开销时抛出的业务异常
    """
    def __init__(self, expense_id: int):
        self.expense_id = expense_id