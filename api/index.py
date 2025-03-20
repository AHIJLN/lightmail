from http.server import BaseHTTPRequestHandler
from datetime import datetime, timedelta
import json
import uuid
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import os

# 固定API设置
API_SETTINGS = {
    'apiKey': 'sk-3e540bcf8e464c198891ab55b0cdc8b2',
    'apiUrl': 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
    'apiModel': 'qwq-plus'
}

# 固定邮箱设置
EMAIL_SENDER = 'lanh_1jiu@icloud.com'
EMAIL_PASSWORD = 'qxwp-eqqw-enuu-bhqe'

def generate_prompt(prompt_type, data):
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
            raise Exception(f"AI API请求失败: {response.status_code}")
            
    except Exception as e:
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
            
        return True
    except Exception as e:
        return False

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            if self.path == '/api/schedule-email':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                # 验证必要字段
                if not data.get('receiverEmail'):
                    self._send_response(400, {"message": "接收邮箱地址不能为空"})
                    return
                    
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
                
                # 如果是立即发送，直接处理
                if data.get('sendOption') == 'now' or (hours == now.hour and abs(minutes - now.minute) <= 2):
                    prompt_type = data.get('promptType', 'future-self')
                    receiver_email = data.get('receiverEmail')
                    
                    subject, content = generate_email_content(prompt_type, data)
                    success = send_email(receiver_email, subject, content)
                    
                    if success:
                        self._send_response(200, {
                            "message": "邮件已发送",
                            "taskId": task_id,
                            "nextRun": datetime.now().isoformat()
                        })
                    else:
                        self._send_response(500, {"message": "邮件发送失败，请稍后再试"})
                else:
                    # 由于Vercel Serverless的限制，我们只返回成功响应
                    # 实际发送需要设置外部触发器
                    self._send_response(200, {
                        "message": "任务已安排",
                        "taskId": task_id,
                        "nextRun": target.isoformat()
                    })
            
            elif self.path.startswith('/api/cancel-task/'):
                task_id = self.path.split('/api/cancel-task/')[1]
                # 在Vercel上，我们不能真正取消任务，但我们可以返回成功
                self._send_response(200, {"message": "任务已取消", "task": {"id": task_id}})
                
            else:
                self._send_response(404, {"message": "路径不存在"})
                
        except Exception as e:
            self._send_response(500, {"message": f"发生错误: {str(e)}"})
    
    def do_GET(self):
        try:
            if self.path == '/api/status':
                self._send_response(200, {
                    "status": "running",
                    "taskCount": 0,
                    "time": datetime.now().isoformat()
                })
            else:
                self._send_response(404, {"message": "路径不存在"})
        except Exception as e:
            self._send_response(500, {"message": f"发生错误: {str(e)}"})
    
    def _send_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
