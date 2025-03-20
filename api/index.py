from flask import Flask, request, jsonify, Response
from datetime import datetime, timedelta
import uuid
import json
import os
import requests
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import time

app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 固定API设置
API_SETTINGS = {
    'apiKey': 'sk-3e540bcf8e464c198891ab55b0cdc8b2',
    'apiUrl': 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
    'apiModel': 'qwq-plus'
}

# 固定邮箱设置
EMAIL_SENDER = 'lanh_1jiu@icloud.com'
EMAIL_PASSWORD = 'qxwp-eqqw-enuu-bhqe'

# 内存中存储任务 (注意: Vercel Serverless函数是无状态的，每次调用都会重置)
tasks = {}

# 生成提示词
def generate_prompt(prompt_type, data):
    try:
        if prompt_type == 'future-self':
            gender = data.get('gender', '男')
            age = data.get('age', '35')
            occupation = data.get('occupation', '程序员')
            other = data.get('other', '')
            
            prompt = f"""
            请你扮演10年后的我，是一位{gender}性，今年{age}岁，职业是{occupation}。{other}
            给现在的我写一封信，鼓励现在的我。内容要充满希望和生活智慧，语言要生动有画面感，让人感到温暖和力量。
            不要写"亲爱的XXX"之类的开头，直接开始正文。
            要有深度，不要太过表面。
            """
            
        elif prompt_type == 'family':
            relative = data.get('relative', '奶奶')
            gender = data.get('gender', '女')
            age = data.get('age', '17')
            occupation = data.get('occupation', '学生')
            other = data.get('other', '')
            
            prompt = f"""
            请你扮演我的{relative}，是一位{gender}性，今年{age}岁，职业是{occupation}。{other}
            给我写一封信，表达对我的关爱和鼓励。内容要充满家人的温暖和智慧，语言要生动有画面感。
            不要写"亲爱的XXX"之类的开头，直接开始正文。
            要有深度，不要太过表面。
            """
            
        elif prompt_type == 'idol':
            idol = data.get('idol', '华语歌坛创作型歌手周杰伦')
            gender = data.get('gender', '男')
            age = data.get('age', '16')
            occupation = data.get('occupation', '学生')
            other = data.get('other', '')
            
            prompt = f"""
            请你扮演{idol}，写一封信给我，我是一位{gender}性，今年{age}岁，职业是{occupation}。{other}
            内容要鼓励我追求梦想，充满积极向上的能量，语言风格要符合{idol}的特点。
            不要写"亲爱的XXX"之类的开头，直接开始正文。
            要有深度，不要太过表面。
            """
        else:
            prompt = """
            请写一封鼓励的信，内容要充满希望和正能量，鼓励收信人勇敢面对生活的挑战。
            不要写"亲爱的XXX"之类的开头，直接开始正文。
            要有深度，不要太过表面。
            """
            
        return prompt
    except Exception as e:
        logger.error(f"生成提示词出错: {str(e)}")
        return "请写一封鼓励的信，内容要充满希望和正能量。"

# 使用AI生成邮件内容
def generate_email_content(prompt_type, data):
    try:
        prompt = generate_prompt(prompt_type, data)
        
        headers = {
            'Authorization': f'Bearer {API_SETTINGS["apiKey"]}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': API_SETTINGS['apiModel'],
            'messages': [
                {'role': 'system', 'content': '你是一个善于写信的AI助手，可以写出温暖、治愈、富有哲理的信件。'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 1000
        }
        
        response = requests.post(API_SETTINGS['apiUrl'], headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # 根据prompt_type生成适当的主题
            if prompt_type == 'future-self':
                subject = "来自10年后的你的一封信"
            elif prompt_type == 'family':
                relative = data.get('relative', '亲人')
                subject = f"来自{relative}的一封信"
            elif prompt_type == 'idol':
                idol = data.get('idol', '偶像')
                subject = f"来自{idol}的一封信"
            else:
                subject = "一封鼓励的信"
                
            # 格式化HTML内容
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; line-height: 1.6;">
                <h2 style="color: #4285F4;">{subject}</h2>
                <div style="white-space: pre-line;">{content}</div>
                <p style="color: #999; font-size: 12px; margin-top: 30px;">发送时间：{datetime.now().strftime("%Y年%m月%d日 %H:%M")}</p>
            </div>
            """
            
            return subject, html_content
        else:
            logger.error(f"AI API请求失败: {response.status_code}, {response.text}")
            raise Exception(f"AI API请求失败: {response.status_code}")
            
    except Exception as e:
        logger.error(f"生成邮件内容出错: {str(e)}")
        # 返回一个默认内容
        current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        subject = "一封鼓励的信"
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; line-height: 1.6;">
            <h2 style="color: #4285F4;">一封鼓励的信</h2>
            <p>生活中总会有起起落落，但请相信，每一次挫折都是成长的机会。</p>
            <p>愿你能保持积极乐观的心态，勇敢面对生活中的各种挑战。加油！</p>
            <p style="color: #999; font-size: 12px; margin-top: 30px;">发送时间：{current_time}</p>
        </div>
        """
        return subject, html_content

# 邮件发送函数
def send_email(receiver_email, subject, content):
    try:
        # 创建邮件
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = receiver_email
        msg['Subject'] = Header(subject, 'utf-8')
        
        # 添加正文
        msg.attach(MIMEText(content, 'html', 'utf-8'))
        
        # 连接到SMTP服务器并发送
        smtp_server = 'smtp.mail.me.com'  # iCloud邮箱的SMTP服务器
        smtp_port = 587  # iCloud邮箱的SMTP端口
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # 启用TLS加密
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
            
        logger.info(f"邮件已发送至 {receiver_email}")
        return True
    except Exception as e:
        logger.error(f"发送邮件出错: {str(e)}")
        return False

# 执行任务函数（由于Vercel的无状态特性，实际执行需要通过外部触发）
def execute_task(task_data):
    try:
        receiver_email = task_data.get('receiverEmail')
        prompt_type = task_data.get('promptType', 'future-self')
        
        subject, content = generate_email_content(prompt_type, task_data)
        
        # 发送邮件
        success = send_email(receiver_email, subject, content)
        return success
    except Exception as e:
        logger.error(f"执行任务出错: {str(e)}")
        return False

# API路由
@app.route('/api/schedule-email', methods=['POST'])
def schedule_email():
    try:
        data = request.json
        logger.info(f"收到的请求数据: {json.dumps(data)}")
        
        # 验证必要字段
        if not data.get('receiverEmail'):
            return jsonify({"message": "接收邮箱地址不能为空"}), 400
            
        # 生成唯一任务ID
        task_id = str(uuid.uuid4())
        
        # 解析时间
        schedule_time = data.get('scheduleTime', '08:00')
        hours, minutes = map(int, schedule_time.split(':'))
        
        # 创建目标时间
        now = datetime.now()
        target = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
        
        # 如果时间已经过去，则设置为明天
        if target < now:
            target += timedelta(days=1)
        
        # 如果是"立即发送"选项，我们直接尝试发送
        if data.get('sendOption') == 'now' or (hours == now.hour and abs(minutes - now.minute) <= 2):
            # 直接执行发送
            success = execute_task(data)
            if success:
                logger.info(f"邮件已直接发送至: {data.get('receiverEmail')}")
                return jsonify({
                    "message": "邮件已发送",
                    "taskId": task_id,
                    "nextRun": datetime.now().isoformat()
                })
            else:
                return jsonify({"message": "邮件发送失败，请稍后再试"}), 500
        
        # 存储任务信息 (注意: 在Vercel上，这只是临时存储)
        tasks[task_id] = {
            'id': task_id,
            'data': data,
            'nextRun': target.isoformat(),
            'created': now.isoformat(),
            'completed': False
        }
        
        logger.info(f"任务已创建: {task_id}, 将在 {target.isoformat()} 执行")
        
        # 注意: 在Vercel上，您需要外部机制来实际执行这些任务
        # 例如: 使用Vercel Cron Jobs或其他第三方服务
        
        return jsonify({
            "message": "任务已安排",
            "taskId": task_id,
            "nextRun": target.isoformat()
        })
        
    except Exception as e:
        logger.error(f"安排任务出错: {str(e)}")
        return jsonify({"message": f"发生错误: {str(e)}"}), 500

@app.route('/api/cancel-task/<task_id>', methods=['POST'])
def cancel_task(task_id):
    try:
        if task_id in tasks:
            # 在Vercel上，这只是从临时内存中移除
            task = tasks.pop(task_id)
            logger.info(f"任务已取消: {task_id}")
            return jsonify({"message": "任务已取消", "task": task})
        else:
            return jsonify({"message": "任务不存在或已完成"}), 404
    except Exception as e:
        logger.error(f"取消任务出错: {str(e)}")
        return jsonify({"message": f"发生错误: {str(e)}"}), 500

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({
        "status": "running",
        "taskCount": len(tasks),
        "time": datetime.now().isoformat()
    })

# Vercel特定的处理程序函数
def handler(request):
    """处理Vercel Serverless请求的函数"""
    
    # 从环境变量获取路径
    path = request.path
    
    # 根据路径路由到正确的处理程序
    if path == '/api/schedule-email' and request.method == 'POST':
        try:
            data = request.json
            response = schedule_email()
            return response
        except Exception as e:
            return jsonify({"message": f"错误: {str(e)}"}), 500
            
    elif path.startswith('/api/cancel-task/') and request.method == 'POST':
        try:
            task_id = path.split('/api/cancel-task/')[1]
            response = cancel_task(task_id)
            return response
        except Exception as e:
            return jsonify({"message": f"错误: {str(e)}"}), 500
            
    elif path == '/api/status' and request.method == 'GET':
        return status()
        
    else:
        return jsonify({"message": "路径不存在"}), 404
