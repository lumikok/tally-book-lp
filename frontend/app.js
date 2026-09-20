const statusText = document.querySelector("#status");
// document：代表当前的HTML页面；querySelector：从页面中寻找一个元素；"#status"-CSS选择器，#表示按id查找

const loadButton = document.querySelector("#load-button");

async function loadExpenses() {
  statusText.textContent = "正在加载开销数据...";

  const response = await fetch("http://127.0.0.1:8000/expenses");

  const expenses = await response.json();

  console.log(expenses);
  statusText.textContent = "开销数据加载完成";
}

loadButton.addEventListener("click", loadExpenses);

const expenseForm = document.querySelector("#expense-form");

async function createExpense(event) {
  event.preventDefault(); // 阻止表单默认提交行为（刷新)

  const formData = new FormData(expenseForm); // 创建一个 FormData 对象，获取表单数据

  const expense = {
    amount: Number(formData.get("amount")), // 获取金额并转换为数字
    category: formData.get("category"), // 获取类别
    note: formData.get("note") || null, // 获取描述
    date: formData.get("date"), // 获取日期
  };

  console.log(expense);

  const response = await fetch("http://127.0.0.1:8000/expenses", {
    method: "POST", // 请求方法为POST，表示创建新资源
    headers: {
      "Content-Type": "application/json", // 告诉后端，请求体是JSON格式
      "X-token": "secret",
    },
    body: JSON.stringify(expense), // HTTP请求体，发送给后端的数据，必须是字符串，所以用JSON.stringify()转换
  });

  const result = await response.json(); // 解析响应体为JSON对象

  console.log(response.status, result); // 打印响应状态码和响应体

  if (response.ok) {
    expenseForm.reset(); // 重置表单
    await loadExpenses(); // 重新加载开销数据
    statusText.textContent = "保存成功，开销数据已刷新";
  } else {
    statusText.textContent = "保存失败";
  }
}

expenseForm.addEventListener("submit", createExpense);
