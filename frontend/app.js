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
