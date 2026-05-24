# 工具增强使用指南

## 📋 新增工具总览

本次更新新增了 **24 个工具**，分为 5 大类别：

| 类别 | 工具数 | 功能描述 |
|------|--------|----------|
| 📄 文件处理 | 7 | 读写 PDF、Excel、Word、文本文件 |
| 🗄️ 数据库 | 4 | SQL 查询、数据导出、表结构查看 |
| 🌐 API 调用 | 5 | 通用 HTTP 请求（GET/POST/PUT/DELETE） |
| 📊 数据可视化 | 3 | 生成折线图、柱状图、饼图、散点图 |
| 🔔 通知工具 | 5 | 企业微信、钉钉、飞书消息推送 |

---

## 📄 文件处理工具

### 1. 读取文本文件
```python
read_text_file(file_path="data.txt")
```
**支持格式**：.txt, .csv, .md, .json

### 2. 写入文本文件
```python
write_text_file(file_path="output.txt", content="Hello World")
```

### 3. 读取 Excel
```python
read_excel(file_path="data.xlsx", sheet_name="Sheet1")
```
**返回**：CSV 格式数据

### 4. 写入 Excel
```python
write_excel(
    file_path="output.xlsx",
    data='[{"name": "张三", "age": 25}, {"name": "李四", "age": 30}]',
    sheet_name="员工列表"
)
```

### 5. 读取 Word
```python
read_word(file_path="document.docx")
```

### 6. 写入 Word
```python
write_word(file_path="report.docx", content="第一段\n第二段\n第三段")
```

### 7. 读取 PDF
```python
read_pdf(file_path="manual.pdf")
```
**返回**：带页码的文本内容

---

## 🗄️ 数据库工具

### 1. 执行 SQL 查询
```python
# SQLite
execute_query(
    query="SELECT * FROM users WHERE age > 18",
    db_type="sqlite",
    db_path="database.db"
)

# MySQL
execute_query(
    query="SELECT * FROM products",
    db_type="mysql",
    host="localhost",
    port=3306,
    database="shop",
    user="root",
    password="123456"
)

# PostgreSQL
execute_query(
    query="SELECT * FROM orders",
    db_type="postgresql",
    host="localhost",
    port=5432,
    database="mydb",
    user="postgres",
    password="123456"
)
```

### 2. 导出查询结果
```python
export_to_file(
    query="SELECT * FROM users",
    output_file="users.csv",  # 支持 .csv, .xlsx, .json
    db_type="sqlite",
    db_path="database.db"
)
```

### 3. 列出所有表
```python
list_tables(
    db_type="mysql",
    host="localhost",
    database="shop",
    user="root",
    password="123456"
)
```

### 4. 获取表结构
```python
get_table_schema(
    table_name="users",
    db_type="sqlite",
    db_path="database.db"
)
```

---

## 🌐 API 调用工具

### 1. 通用 HTTP 请求
```python
http_request(
    url="https://api.example.com/data",
    method="POST",
    headers={"Content-Type": "application/json"},
    body={"key": "value"},
    timeout=30
)
```

### 2. GET 请求
```python
get_request(
    url="https://api.github.com/users/octocat",
    params={"sort": "created"}
)
```

### 3. POST 请求
```python
post_request(
    url="https://api.example.com/users",
    body={"name": "张三", "email": "zhangsan@example.com"}
)
```

### 4. PUT 请求
```python
put_request(
    url="https://api.example.com/users/123",
    body={"name": "新名字"}
)
```

### 5. DELETE 请求
```python
delete_request(
    url="https://api.example.com/users/123"
)
```

---

## 📊 数据可视化工具

### 1. 创建图表
```python
# 柱状图
create_chart(
    data='{"一月": 120, "二月": 200, "三月": 150, "四月": 80}',
    chart_type="bar",
    title="月度销售统计",
    x_label="月份",
    y_label="销售额",
    output_file="sales_bar.png"
)

# 折线图
create_chart(
    data='[10, 15, 20, 25, 30, 35]',
    chart_type="line",
    title="温度变化趋势",
    output_file="temperature_line.png"
)

# 饼图
create_chart(
    data='{"产品 A": 45, "产品 B": 30, "产品 C": 15, "产品 D": 10}',
    chart_type="pie",
    title="产品销售占比",
    output_file="sales_pie.png"
)

# 散点图
create_chart(
    data='[{"x": 1, "y": 2}, {"x": 2, "y": 4}, {"x": 3, "y": 6}]',
    chart_type="scatter",
    title="数据点分布",
    output_file="scatter.png"
)
```

### 2. 多系列图表
```python
create_multi_series_chart(
    data='{"2023 年": [120, 200, 150, 80], "2024 年": [150, 230, 180, 100]}',
    chart_type="line",
    title="两年销售对比",
    x_label="季度",
    y_label="销售额",
    output_file="comparison.png"
)
```

### 3. 横向对比图
```python
create_comparison_chart(
    data='{"北京": 2154, "上海": 2428, "广州": 1530, "深圳": 1343}',
    title="一线城市人口对比",
    output_file="city_population.png"
)
```

---

## 🔔 通知工具

### 1. 企业微信消息
```python
# 文本消息
send_wecom_message(
    webhook_url="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx",
    content="【系统通知】服务器 CPU 使用率超过 90%",
    mentioned_list=["zhangsan", "lisi"]  # 可选：@特定成员
)

# Markdown 消息
send_wecom_markdown(
    webhook_url="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx",
    title="服务器告警",
    markdown_content="## 服务器告警\n- **主机**: server-01\n- **CPU**: 95%\n- **时间**: 2024-01-01 12:00"
)
```

### 2. 钉钉消息
```python
# 文本消息
send_dingtalk_message(
    webhook_url="https://oapi.dingtalk.com/robot/send?access_token=xxx",
    content="【系统通知】数据库备份完成",
    at_mobiles=["13800138000"],  # 可选：@手机联系人
    is_atall=False  # 可选：@所有人
)

# Markdown 消息
send_dingtalk_markdown(
    webhook_url="https://oapi.dingtalk.com/robot/send?access_token=xxx",
    title="项目进度更新",
    markdown_content="## 项目进度更新\n- 前端：80%\n- 后端：60%\n- 测试：30%"
)
```

### 3. 飞书消息
```python
send_feishu_message(
    webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/xxx",
    content="【会议通知】明天上午 10 点召开项目评审会"
)
```

---

## 🔧 使用示例

### 示例 1：数据分析报告自动生成

```python
# 1. 从数据库查询销售数据
sales_data = execute_query(
    query="SELECT month, revenue FROM sales WHERE year=2024",
    db_type="mysql",
    host="localhost",
    database="shop",
    user="root",
    password="123456"
)

# 2. 生成销售图表
create_chart(
    data=sales_data,
    chart_type="bar",
    title="2024 年销售统计",
    output_file="sales_2024.png"
)

# 3. 导出 Excel 报表
export_to_file(
    query="SELECT * FROM sales WHERE year=2024",
    output_file="sales_report.xlsx",
    db_type="mysql",
    host="localhost",
    database="shop",
    user="root",
    password="123456"
)

# 4. 发送钉钉通知
send_dingtalk_message(
    webhook_url="https://oapi.dingtalk.com/robot/send?access_token=xxx",
    content="✓ 2024 年销售报告已生成，请查收邮件"
)
```

### 示例 2：API 数据同步

```python
# 1. 从外部 API 获取数据
api_response = get_request(
    url="https://api.example.com/products",
    params={"page": 1, "limit": 100}
)

# 2. 解析并写入 Excel
write_excel(
    file_path="products.xlsx",
    data=api_response,
    sheet_name="产品列表"
)

# 3. 发送企业微信通知
send_wecom_markdown(
    webhook_url="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx",
    title="数据同步完成",
    markdown_content="## 数据同步完成\n- 同步产品数：100\n- 导出文件：products.xlsx\n- 时间：2024-01-01"
)
```

### 示例 3：定时监控告警

```python
# 1. 检查数据库连接
health_query = execute_query(
    query="SELECT COUNT(*) FROM users",
    db_type="mysql",
    host="db.example.com",
    database="production",
    user="monitor",
    password="xxx"
)

# 2. 如果异常，发送多条告警
if "错误" in health_query:
    # 企业微信
    send_wecom_message(
        webhook_url="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx",
        content="🚨 数据库连接失败！请立即处理",
        mentioned_list=["admin"]
    )
    
    # 钉钉
    send_dingtalk_message(
        webhook_url="https://oapi.dingtalk.com/robot/send?access_token=xxx",
        content="🚨 数据库连接失败！请立即处理",
        is_atall=True
    )
    
    # 飞书
    send_feishu_message(
        webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/xxx",
        content="🚨 数据库连接失败！请立即处理"
    )
```

---

## 📦 依赖安装

运行以下命令安装所有新增依赖：

```bash
pip install pandas openpyxl pymysql psycopg2-binary python-docx PyPDF2 matplotlib
```

或使用 requirements.txt：

```bash
pip install -r requirements.txt
```

---

## ⚠️ 注意事项

### 文件处理工具
- PDF 读取需要文件有文本层（扫描件无法读取）
- Word 仅支持 .docx 格式（不支持 .doc）
- Excel 读取大文件时注意内存限制

### 数据库工具
- 默认只允许 SELECT 查询（安全保护）
- 生产环境建议使用只读账号
- 大数据量导出时注意超时设置

### API 调用工具
- 默认超时 30 秒，可根据需要调整
- 注意 API 频率限制
- 敏感信息不要放在 URL 中

### 可视化工具
- 中文显示需要系统有对应字体
- 大数据量图表生成较慢
- 输出文件路径确保有写权限

### 通知工具
- Webhook URL 请妥善保管
- 消息内容注意长度限制
- 频繁发送可能被限流

---

## 🎯 最佳实践

1. **工具组合使用**：多个工具配合实现自动化流程
2. **错误处理**：检查工具返回，失败时重试或告警
3. **日志记录**：重要操作记录日志便于追踪
4. **安全存储**：密码、密钥等敏感信息使用环境变量
5. **性能优化**：大数据操作时分页处理，避免一次性加载

---

## 📚 更多信息

- 查看工具源码：`tools/` 目录
- 工具注册：`tools/__init__.py`
- 使用示例：参考本文档
