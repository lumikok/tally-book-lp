from fastapi import FastAPI

app = FastAPI(
    title="我的记账API",
    description="从零学习FastAPI的记账系统API",
    version="0.1.0",
)

@app.get("/")
def root():
    return {"message": "欢迎来到我的记账API！"}

@app.get("/users/{user_name}")
def greet(user_name: str):
    return {"message": f"你好，{user_name}！欢迎使用我的记账API！"}


