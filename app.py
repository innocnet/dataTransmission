#!/usr/bin/env python3
"""
阅后即焚 - 一次性文本分享服务
用户粘贴文本后生成唯一URL，打开一次后自动销毁
"""
from flask import Flask, render_template, request, jsonify, abort, Response
from werkzeug.middleware.proxy_fix import ProxyFix
import secrets
import string
from datetime import datetime, timedelta
from threading import Lock
import logging

app = Flask(__name__)

# 配置代理支持（用于 nginx 反向代理）
app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=1,  # X-Forwarded-For
    x_proto=1,  # X-Forwarded-Proto
    x_host=1,  # X-Forwarded-Host
    x_prefix=1  # X-Forwarded-Prefix
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 固定 key → 内容映射，永不销毁
FIXED_TEXTS = {
    'nasproxy': """port: 7890
socks-port: 7891
allow-lan: true
mode: Direct
log-level: info
proxies:
  - name: nas
    type: http
    server: 192.168.192.31
    port: 7890
    tls: false
    skip-cert-verify: true

proxy-groups:
  - name: 🚀 节点选择
    type: select
    proxies:
      - nas
      - DIRECT

rules:
  - MATCH, nas"""
}

# 内存存储（简单场景，重启后数据丢失）
# 如果需要持久化，可以改用 SQLite 或 Redis
texts = {}
texts_lock = Lock()

# 配置
URL_LENGTH = 12  # 生成的 URL ID 长度
MAX_TEXT_SIZE = 1024 * 1024  # 最大 1MB 文本
EXPIRE_HOURS = 24  # 24小时后自动过期


def generate_id():
    """生成随机 URL ID"""
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(URL_LENGTH))


def cleanup_expired():
    """清理过期的文本"""
    now = datetime.now()
    with texts_lock:
        expired_ids = [
            text_id for text_id, data in texts.items()
            if data['expires_at'] < now
        ]
        for text_id in expired_ids:
            del texts[text_id]


@app.route('/')
def index():
    """首页：提交文本"""
    return render_template('index.html')


@app.route('/api/create', methods=['POST'])
def create_text():
    """创建一次性文本链接"""
    data = request.get_json()

    if not data or 'text' not in data:
        return jsonify({'error': '缺少文本内容'}), 400

    text = data['text']

    if not text.strip():
        return jsonify({'error': '文本不能为空'}), 400

    if len(text.encode('utf-8')) > MAX_TEXT_SIZE:
        return jsonify({'error': f'文本过大，最大支持 {MAX_TEXT_SIZE // 1024}KB'}), 400

    # 清理过期内容
    cleanup_expired()

    # 生成唯一 ID
    text_id = generate_id()
    while text_id in texts:  # 确保唯一性
        text_id = generate_id()

    # 存储文本
    with texts_lock:
        texts[text_id] = {
            'text': text,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(hours=EXPIRE_HOURS)
        }

    # 返回访问 URL
    url = request.host_url + 'view/' + text_id
    logger.info(f"创建文本 ID: {text_id}, URL: {url}, 来源IP: {request.remote_addr}")
    return jsonify({
        'success': True,
        'url': url,
        'id': text_id
    })


@app.route('/view/<text_id>')
def view_text(text_id):
    """查看文本（只能查看一次）"""
    user_agent = request.headers.get('User-Agent', 'Unknown')
    ip = request.remote_addr

    logger.info(f"访问请求 ID: {text_id}, IP: {ip}, User-Agent: {user_agent}")

    # 固定 key，永久返回，不销毁
    if text_id in FIXED_TEXTS:
        return Response(FIXED_TEXTS[text_id], mimetype='text/plain; charset=utf-8')

    cleanup_expired()

    # 获取并删除文本（一次性）
    with texts_lock:
        if text_id not in texts:
            logger.warning(f"文本不存在或已被删除 ID: {text_id}, IP: {ip}")
            abort(404)

        text_data = texts.pop(text_id)  # 取出并删除
        logger.info(f"文本已读取并删除 ID: {text_id}, IP: {ip}")

    # 返回纯文本，方便直接复制
    return Response(text_data['text'], mimetype='text/plain; charset=utf-8')



@app.route('/api/stats')
def stats():
    """当前存储的文本数量（可选的调试接口）"""
    cleanup_expired()
    with texts_lock:
        count = len(texts)
    return jsonify({'count': count})


if __name__ == '__main__':
    # 生产模式：单进程运行
    # 重要：必须使用单进程，因为数据存储在内存中
    # 如果需要多进程，请改用 Redis 等共享存储
    app.run(
        host='0.0.0.0',
        port=8080,
        debug=False,  # 生产环境关闭 debug
        threaded=True,  # 支持多线程处理并发请求
        processes=1  # 强制单进程
    )
