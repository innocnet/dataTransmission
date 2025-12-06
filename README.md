# 阅后即焚 - 一次性文本分享服务

一个简单的"阅后即焚"文本分享工具，用户可以粘贴文本生成唯一URL，**打开一次后内容自动销毁**。

## 功能特点

- **一次性访问**：生成的链接只能访问一次，打开后内容立即从服务器删除
- **自动过期**：未访问的链接 24 小时后自动过期
- **简洁安全**：无需登录，无需数据库，使用内存存储
- **界面友好**：现代化的响应式设计，支持一键复制
- **轻量级**：纯 Python Flask 实现，资源占用少

## 快速开始

### 方式 1：直接运行（Python）

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动服务
python app.py

# 3. 打开浏览器访问
# http://localhost:5000
```

### 方式 2：Docker 运行

```bash
# 使用 docker-compose（推荐）
docker-compose up -d

# 或使用 docker 命令
docker build -t burntext .
docker run -d -p 5000:5000 --name burntext burntext
```

### 方式 3：生产环境部署

```bash
# 安装 gunicorn
pip install gunicorn

# 启动生产服务器
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
```

## 使用方法

1. **创建链接**：
   - 在首页粘贴你的文本内容
   - 点击"生成一次性链接"
   - 复制生成的 URL

2. **分享链接**：
   - 将链接发送给接收者
   - ⚠️ 注意：链接只能访问一次！

3. **查看内容**：
   - 接收者打开链接查看内容
   - 内容查看后立即销毁，无法再次访问

## 配置说明

可以在 `app.py` 中修改以下配置：

```python
URL_LENGTH = 12          # URL ID 长度（默认 12 个字符）
MAX_TEXT_SIZE = 1024 * 1024  # 最大文本大小（默认 1MB）
EXPIRE_HOURS = 24        # 自动过期时间（默认 24 小时）
```

## API 接口

### 创建文本

```http
POST /api/create
Content-Type: application/json

{
  "text": "你的文本内容"
}
```

响应：
```json
{
  "success": true,
  "url": "http://localhost:5000/view/abc123xyz",
  "id": "abc123xyz"
}
```

### 查看文本

```http
GET /view/<text_id>
```

## 安全说明

- **内存存储**：默认使用内存存储，服务重启后数据丢失（更安全）
- **一次性读取**：读取后立即删除，无法恢复
- **自动过期**：24 小时后自动清理未读取的内容
- **无日志记录**：不记录文本内容和访问日志

⚠️ **警告**：此工具适合临时分享，不建议用于存储重要数据。

## 持久化存储（可选）

如果需要服务重启后保留数据，可以改用 SQLite：

```python
# 在 app.py 中替换内存存储为 SQLite
import sqlite3

# 初始化数据库
conn = sqlite3.connect('burntext.db', check_same_thread=False)
# ... 实现数据库存储逻辑
```

或使用 Redis：

```bash
pip install redis
```

```python
import redis
r = redis.Redis(host='localhost', port=6379, db=0)
```

## 技术栈

- **后端**：Python 3.11 + Flask 3.0
- **前端**：原生 HTML/CSS/JavaScript
- **部署**：Docker + Gunicorn
- **存储**：内存（可选 SQLite/Redis）

## 目录结构

```
caddy/
├── app.py                 # Flask 应用主文件
├── templates/
│   ├── index.html        # 创建页面
│   └── view.html         # 查看页面
├── requirements.txt      # Python 依赖
├── Dockerfile           # Docker 镜像
├── docker-compose.yml   # Docker Compose 配置
└── README.md           # 使用说明
```

## 许可证

MIT License

## 常见问题

**Q: 链接能访问多少次？**
A: 只能访问一次，打开后内容立即销毁。

**Q: 未访问的链接会保留多久？**
A: 24 小时后自动过期删除。

**Q: 服务器会记录我的内容吗？**
A: 不会，内容读取后立即删除，不保留任何日志。

**Q: 可以修改过期时间吗？**
A: 可以，修改 `app.py` 中的 `EXPIRE_HOURS` 配置。

**Q: 支持多大的文本？**
A: 默认最大 1MB，可通过 `MAX_TEXT_SIZE` 配置修改。
