from flask import Flask, request, jsonify
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
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   filename='email_sender.log')
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

# 内存中存储任务
tasks = {}

# 创建调度器
scheduler = BackgroundScheduler()
scheduler.start()

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

# 执行任务的函数
def execute_task(task_id):
    try:
        if task_id not in tasks:
            logger.error(f"任务不存在: {task_id}")
            return
        
        task = tasks[task_id]
        data = task['data']
        
        receiver_email = data.get('receiverEmail')
        prompt_type = data.get('promptType', 'future-self')
        
        subject, content = generate_email_content(prompt_type, data)
        
        # 发送邮件
        success = send_email(receiver_email, subject, content)
        
        if success:
            # 检查是否需要重复
            repeat_option = data.get('repeatOption', 'none')
            
            if repeat_option != 'none':
                # 计算下次执行时间
                next_run = datetime.fromisoformat(task['nextRun'])
                
                if repeat_option == 'daily':
                    next_run = next_run + timedelta(days=1)
                elif repeat_option == 'weekly':
                    next_run = next_run + timedelta(days=7)
                elif repeat_option == 'monthly':
                    # 简单处理，加30天
                    next_run = next_run + timedelta(days=30)
                
                # 更新任务
                task['nextRun'] = next_run.isoformat()
                task['lastRun'] = datetime.now().isoformat()
                
                # 调度下一次执行
                job_id = f"task_{task_id}_{next_run.timestamp()}"
                scheduler.add_job(
                    execute_task,
                    DateTrigger(run_date=next_run),
                    args=[task_id],
                    id=job_id,
                    replace_existing=True
                )
                
                logger.info(f"重复任务已调度: {task_id}, 下次执行时间: {next_run.isoformat()}")
            else:
                # 标记为已完成
                task['completed'] = True
                task['lastRun'] = datetime.now().isoformat()
                logger.info(f"任务已完成: {task_id}")
        else:
            logger.error(f"任务执行失败: {task_id}")
            # 可以在这里添加重试逻辑
    except Exception as e:
        logger.error(f"执行任务出错: {task_id}, 错误: {str(e)}")

# API路由
@app.route('/api/schedule-email', methods=['POST'])
def schedule_email():
    try:
        data = request.json
        logger.info(f"收到的请求数据: {data}")
        
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
            
        # 存储任务
        tasks[task_id] = {
            'id': task_id,
            'data': data,
            'nextRun': target.isoformat(),
            'created': now.isoformat(),
            'completed': False
        }
        
        # 调度任务
        job_id = f"task_{task_id}"
        scheduler.add_job(
            execute_task,
            DateTrigger(run_date=target),
            args=[task_id],
            id=job_id,
            replace_existing=True
        )
        
        logger.info(f"任务已创建: {task_id}, 将在 {target.isoformat()} 执行")
        
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
            # 移除调度任务
            job_id = f"task_{task_id}"
            try:
                scheduler.remove_job(job_id)
            except:
                pass  # 任务可能已经执行或不存在
                
            # 移除任务
            task = tasks.pop(task_id)
            logger.info(f"任务已取消: {task_id}")
            return jsonify({"message": "任务已取消", "task": task})
        else:
            return jsonify({"message": "任务不存在"}), 404
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

# Vercel Serverless函数处理
def handler(environ, start_response):
    return app(environ, start_response)
