const statusText = document.querySelector("#status");
// document：代表当前的HTML页面；querySelector：从页面中寻找一个元素；"#status"-CSS选择器，#表示按id查找

// 选择加载按钮元素
const loadButton = document.querySelector("#load-button");

// 选择开销列表元素
const expenseList = document.querySelector("#expense-list");

// 筛选相关元素
const filterCategory = document.querySelector("#filter-category");
const filterButton = document.querySelector("#filter-button");

// 分页相关元素
const previousButton = document.querySelector("#previous-button");
const nextButton = document.querySelector("#next-button");
const pageInfo = document.querySelector("#page-info");
let currentPage = 1;
const pageSize = 2;

// 图表相关元素
const categoryChartContainer = document.querySelector("#category-chart");
const categoryChart = echarts.init(categoryChartContainer); // 初始化图表实例

const dailyChartContainer = document.querySelector("#daily-chart");
const dailyChart = echarts.init(dailyChartContainer); // 初始化图表实例

async function loadCategoryChart() {
  const response = await fetch("http://127.0.0.1:8000/summary/category");

  const categoryRows = await response.json();

  const pieData = categoryRows.map((row) => {
    return {
      name: row.category,
      value: row.amount,
    };
  });
  const option = {
    title: {
      text: "各类支出占比",
      left: "center",
    },
    tooltip: {
      trigger: "item",
    },
    series: [
      {
        name: "分类支出",
        type: "pie",
        radius: "60%",
        data: pieData,
      },
    ],
  };
  categoryChart.setOption(option);
}

async function loadDailyChart() {
  const response = await fetch("http://127.0.0.1:8000/summary/daily");

  const dailyRows = await response.json();

  const dates = dailyRows.map((row) => {
    return row.date;
  });

  const amounts = dailyRows.map((row) => {
    return row.amount;
  });

  const option = {
    title: {
      text: "每日支出趋势",
      left: "center",
    },
    tooltip: {
      trigger: "axis",
    },
    xAxis: {
      type: "category",
      data: dates,
    },
    yAxis: {
      type: "value",
    },
    series: [
      {
        name: "每日支出",
        type: "line",
        data: amounts,
      },
    ],
  };
  dailyChart.setOption(option);
}

// 加载图表数据
loadCategoryChart();
loadDailyChart();

let editingExpenseId = null; // 用于存储当前正在编辑的开销ID，初始值为null，表示没有正在编辑的开销

async function deleteExpense(expenseId) {
  statusText.textContent = "正在删除开销数据...";

  const response = await fetch(`http://127.0.0.1:8000/expenses/${expenseId}`, {
    method: "DELETE", // 请求方法为DELETE，表示删除资源
    headers: {
      "X-token": "secret",
    },
  });

  if (response.ok) {
    await loadExpenses(); // 重新加载开销数据
    await loadCategoryChart(); // 重新加载图表数据
    await loadDailyChart();
    statusText.textContent = "删除成功，开销数据已刷新";
  } else {
    const error = await response.json();
    console.log(error);
    statusText.textContent = "删除失败";
  }
}

function startEdit(expense) {
  editingExpenseId = expense.id;

  document.querySelector("#amount").value = expense.amount;
  document.querySelector("#category").value = expense.category;
  document.querySelector("#note").value = expense.note || "";
  document.querySelector("#date").value = expense.date;

  statusText.textContent = `正在编辑 id=${expense.id} 的开销数据`;
}

// 渲染开销列表
function renderExpenses(expenses) {
  expenseList.innerHTML = ""; // 清空列表

  for (const expense of expenses) {
    const row = document.createElement("tr"); // 创建一个表格行元素

    row.innerHTML = `
      <td>${expense.amount}</td>
      <td>${expense.category}</td>
      <td>${expense.note || "-"}</td>
      <td>${expense.date}</td>
      <td>
      <button type="button" class="delete-button">删除</button>
      <button type="button" class="edit-button">编辑</button>
      </td>
    `;

    const editButton = row.querySelector(".edit-button"); // 获取编辑按钮元素

    editButton.addEventListener("click", () => {
      startEdit(expense); // 调用开始编辑函数，传入开销对象
    });

    const deleteButton = row.querySelector(".delete-button"); // 获取删除按钮元素

    deleteButton.addEventListener("click", () => {
      deleteExpense(expense.id); // 调用删除开销函数，传入开销ID，箭头函数：简化函数写法
    });
    expenseList.appendChild(row);
  }
}

async function loadExpenses() {
  statusText.textContent = "正在加载开销数据...";

  const params = new URLSearchParams({
    skip: (currentPage - 1) * pageSize,
    limit: pageSize + 1, // 请求多一条数据，用于判断是否有下一页
  });

  if (filterCategory.value) {
    params.set("category", filterCategory.value); // 如果选择了类别，则添加类别参数
  }

  const requestUrl = `http://127.0.0.1:8000/expenses?${params.toString()}`;

  const response = await fetch(requestUrl);
  const expenses = await response.json();

  const visibleExpenses = expenses.slice(0, pageSize); // 只显示前 pageSize 条数据
  // slice() 截取数组，返回一个新数组，不会修改原数组（结束位置不包含在内）

  renderExpenses(visibleExpenses);

  previousButton.disabled = currentPage === 1;
  nextButton.disabled = expenses.length <= pageSize;
  pageInfo.textContent = `第 ${currentPage} 页`;

  statusText.textContent = `加载完成，本页共 ${visibleExpenses.length} 条开销数据`;
}

filterButton.addEventListener("click", () => {
  currentPage = 1;
  loadExpenses();
});

loadButton.addEventListener("click", () => {
  filterCategory.value = ""; // 清空类别筛选
  currentPage = 1;
  loadExpenses();
});

previousButton.addEventListener("click", () => {
  if (currentPage > 1) {
    currentPage--;
    loadExpenses();
  }
});

nextButton.addEventListener("click", () => {
  currentPage++;
  loadExpenses();
});

const expenseForm = document.querySelector("#expense-form");

async function saveExpense(event) {
  event.preventDefault(); // 阻止表单默认提交行为（刷新)

  const formData = new FormData(expenseForm); // 创建一个 FormData 对象，获取表单数据

  const expense = {
    amount: Number(formData.get("amount")), // 获取金额并转换为数字
    category: formData.get("category"), // 获取类别
    note: formData.get("note") || null, // 获取描述
    date: formData.get("date"), // 获取日期
  };

  console.log(expense);

  const isEditing = editingExpenseId !== null; // 判断是否正在编辑开销数据

  let requestUrl = "http://127.0.0.1:8000/expenses";
  let requestMethod = "POST"; // 默认请求方法为POST，表示创建新资源

  if (isEditing) {
    requestUrl = `http://127.0.0.1:8000/expenses/${editingExpenseId}`;
    requestMethod = "PUT"; // 如果是编辑，则使用PUT方法，表示更新资源
  }

  const response = await fetch(requestUrl, {
    method: requestMethod, // 请求方法为POST，表示创建新资源
    headers: {
      "Content-Type": "application/json", // 告诉后端，请求体是JSON格式
      "X-token": "secret",
    },
    body: JSON.stringify(expense), // HTTP请求体，发送给后端的数据，必须是字符串，所以用JSON.stringify()转换
  });

  const result = await response.json(); // 解析响应体为JSON对象

  console.log(response.status, result); // 打印响应状态码和响应体

  if (response.ok) {
    editingExpenseId = null; // 重置编辑状态
    expenseForm.reset(); // 重置表单
    await loadExpenses(); // 重新加载开销数据
    await loadCategoryChart(); // 重新加载图表数据
    await loadDailyChart();
    if (isEditing) {
      statusText.textContent = `编辑成功，开销列表已刷新`;
    } else {
      statusText.textContent = `保存成功，开销列表已刷新`;
    }
  } else {
    statusText.textContent = isEditing ? "修改失败" : "保存失败";
  }
}

expenseForm.addEventListener("submit", saveExpense);
