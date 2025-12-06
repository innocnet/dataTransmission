FROM python:3.11-slim

WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app.py .
COPY templates/ templates/

# 暴露端口
EXPOSE 5000

# 使用生产级 WSGI 服务器
RUN pip install gunicorn

# 启动应用
# 重要：必须使用 workers=1 因为数据存储在内存中
# 多进程会导致数据不同步，造成"第一次404，第二次才能访问"的问题
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "--timeout", "120", "app:app"]
