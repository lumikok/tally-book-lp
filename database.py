# 导入所需函数
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,declarative_base

# 数据库地址
DATABASE_URL = "sqlite:///./tally.db"

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite 特有参数，允许多线程访问
)

# 创建会话类
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# 创建基类
Base = declarative_base() # 用于创建数据模型