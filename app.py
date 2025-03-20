from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
import logging
from datetime import datetime, timedelta
import time
import threading
import json
import os
import re

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("email_sender.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)  # 允许跨域请求

# 固定API设置
API_SETTINGS = {
    'apiKey': 'sk-3e540bcf8e464c198891ab55b0cdc8b2',
    'apiUrl': 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
    'apiModel': 'qwq-plus'
}

# 固定邮箱设置
EMAIL_SENDER = 'lanh_1jiu@icloud.com'
EMAIL_PASSWORD = 'qxwp-eqqw-enuu-bhqe'

# 存储任务信息
EMAIL_TASKS = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/generate-content', methods=['POST'])
def generate_content():
    """调用API生成内容"""
    data = request.json
    prompt_type = data.get('promptType', 'future-self')
    
    # 获取个性化参数
    gender = data.get('gender', '男')
    age = data.get('age', '35')
    occupation = data.get('occupation', '程序员')
    relative = data.get('relative', '奶奶')
    idol = data.get('idol', '华语歌坛创作型歌手周杰伦')
    other = data.get('other', '')
    
    try:
        prompt = get_prompt_by_type(prompt_type, gender, age, occupation, relative, idol, other)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_SETTINGS['apiKey']}"
        }
        
        payload = {
            "model": API_SETTINGS['apiModel'],
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 600
        }
        
        response = requests.post(API_SETTINGS['apiUrl'], headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        logger.info(f"内容生成成功，长度: {len(content)}字符")
        return jsonify({'success': True, 'content': content}), 200
    
    except Exception as e:
        logger.error(f"内容生成失败: {str(e)}")
        return jsonify({'success': False, 'message': f'内容生成失败: {str(e)}'}), 500

@app.route('/api/send-email', methods=['POST'])
def send_email_endpoint():
    """发送单次邮件"""
    data = request.json
    receiver_email = data.get('receiverEmail')
    subject = data.get('subject')
    content = data.get('content')
    
    if not all([receiver_email, subject, content]):
        return jsonify({'success': False, 'message': '邮件配置不完整'}), 400
    
    # 根据接收邮箱类型自动设置SMTP服务器和端口
    smtp_server, smtp_port = get_smtp_settings(receiver_email)
    
    try:
        send_email(
            smtp_server, 
            int(smtp_port), 
            EMAIL_SENDER, 
            EMAIL_PASSWORD, 
            receiver_email, 
            subject, 
            content
        )
        logger.info(f"邮件已发送至 {receiver_email}")
        return jsonify({'success': True, 'message': '邮件发送成功'}), 200
    
    except Exception as e:
        logger.error(f"邮件发送失败: {str(e)}")
        return jsonify({'success': False, 'message': f'邮件发送失败: {str(e)}'}), 500

@app.route('/api/schedule-email', methods=['POST'])
def schedule_email():
    """设置定时发送邮件任务"""
    data = request.json
    task_id = datetime.now().strftime("%Y%m%d%H%M%S")
    
    receiver_email = data.get('receiverEmail')
    schedule_time = data.get('scheduleTime')  # 格式: "HH:MM"
    repeat_option = data.get('repeatOption', 'none')
    prompt_type = data.get('promptType', 'future-self')
    
    # 获取个性化参数
    gender = data.get('gender', '男')
    age = data.get('age', '35')
    occupation = data.get('occupation', '程序员')
    relative = data.get('relative', '奶奶')
    idol = data.get('idol', '华语歌坛创作型歌手周杰伦')
    other = data.get('other', '')
    
    if not all([receiver_email, schedule_time]):
        return jsonify({'success': False, 'message': '配置不完整'}), 400
    
    # 根据接收邮箱类型自动设置SMTP服务器和端口
    smtp_server, smtp_port = get_smtp_settings(receiver_email)
    
    # 计算下一次执行时间
    next_run = calculate_next_run(schedule_time)
    
    # 存储任务信息
    task_info = {
        'id': task_id,
        'receiverEmail': receiver_email,
        'smtpServer': smtp_server,
        'smtpPort': int(smtp_port),
        'scheduleTime': schedule_time,
        'repeatOption': repeat_option,
        'promptType': prompt_type,
        'gender': gender,
        'age': age,
        'occupation': occupation,
        'relative': relative,
        'idol': idol,
        'other': other,
        'nextRun': next_run.isoformat(),
        'status': 'scheduled'
    }
    
    EMAIL_TASKS[task_id] = task_info
    
    # 启动定时任务线程
    threading.Thread(target=run_scheduled_task, args=(task_id,), daemon=True).start()
    
    logger.info(f"已安排定时任务 {task_id}，下次执行时间: {next_run}")
    return jsonify({
        'success': True, 
        'message': '任务已安排', 
        'taskId': task_id,
        'nextRun': next_run.isoformat()
    }), 200

@app.route('/api/cancel-task/<task_id>', methods=['POST'])
def cancel_task(task_id):
    """取消定时任务"""
    if task_id in EMAIL_TASKS:
        EMAIL_TASKS[task_id]['status'] = 'cancelled'
        logger.info(f"任务 {task_id} 已取消")
        return jsonify({'success': True, 'message': '任务已取消'}), 200
    else:
        return jsonify({'success': False, 'message': '任务不存在'}), 404

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """获取所有任务信息"""
    return jsonify({'tasks': list(EMAIL_TASKS.values())}), 200

# 辅助函数
def get_smtp_settings(email):
    """根据邮箱地址获取SMTP服务器和端口"""
    email = email.lower()
    
    if 'outlook.com' in email or 'hotmail.com' in email or 'live.com' in email:
        return 'smtp-mail.outlook.com', 587
    elif 'qq.com' in email:
        return 'smtp.qq.com', 587
    elif 'icloud.com' in email or 'me.com' in email:
        return 'smtp.mail.me.com', 587
    elif 'gmail.com' in email:
        return 'smtp.gmail.com', 587
    elif '163.com' in email:
        return 'smtp.163.com', 25
    elif '126.com' in email:
        return 'smtp.126.com', 25
    elif 'sina.com' in email:
        return 'smtp.sina.com', 25
    elif 'sohu.com' in email:
        return 'smtp.sohu.com', 25
    else:
        # 默认使用iCloud的SMTP服务器
        return 'smtp.mail.me.com', 587

def get_prompt_by_type(prompt_type, gender, age, occupation, relative, idol, other):
    """根据提示类型返回对应的提示词"""
    # 添加其他内容，如果有的话
    other_info = f"，{other}" if other else ""
    
    prompts = {
        'future-self': f"""你是一个专业的谈判专家和顶级心理医生顾问，有10年丰富经验并拯救了100000个轻生少年少女和中老年人（这些内容不能在信中提及），请你写一封300汉字的信，用来鼓励抑郁症的病人。
请根据MECE原则来确保生成的内容，与之前所有版本完全不同，不重复以前的生成内容。
一、任务：
你的任务是以10年后成功的自己的口吻，给过去的自己({gender}，{age}岁，{occupation}{other_info})写一封信300汉字的鼓励信，一定要轻松自然，以防被识破，不能提过去的自己相关的生活细节，一定要让过去的自己重燃生活的希望，并且过好今天，并且承诺明天都会给过去的自己发一封邮件，让过去的自己好好过完今天，期待明天，署名为未来的自己。

二、回答格式要求：
1.开头为：致过去的我：(换行)，以「未来的你」结尾(只以"未来的你"，后面不能写任何内容）

三、回答内容要求：
1.正文内容不能出现：药物、自杀、割腕、具体的细节、具体的物件、具体地名、具体植物名、具体动物名、咖啡""",
        
        'family': f"""你是一个专业的谈判专家和顶级心理医生顾问，有10年丰富经验并拯救了100000个轻生少年少女和中老年人（这些内容不能在信中提及），请你写一封300汉字的信，用来鼓励抑郁症的病人。
请根据MECE原则来确保生成的内容，与之前所有版本完全不同，不重复以前的生成内容。
一、任务：
你的任务是以家人（{relative}）的口吻，给过去的自己({gender}，{age}岁，{occupation}{other_info})写一封信300汉字的鼓励信，一定要轻松自然，以防被识破，不能提过去的自己相关的生活细节，一定要让过去的自己重燃生活的希望，并且过好今天，并且承诺以及天天都会给过去的自己发一封邮件，让过去的自己好好过完今天，期待明天，署名为未来的自己。
 
 
二、回答格式要求：
1.开头为：致囡囡：(换行)，以「最爱你的{relative}」结尾(只以"最爱你的{relative}"，后面不能写任何内容）

三、回答内容要求：
1.正文内容不能出现：药物、自杀、割腕、具体的细节、具体的物件、具体地名、具体植物名、具体动物名、咖啡""",
        
        'idol': f"""你是一个专业的谈判专家和顶级心理医生顾问，有10年丰富经验并拯救了100000个轻生少年少女和中老年人（这些内容不能在信中提及），请你写一封300汉字的信，用来鼓励抑郁症的病人。
请根据MECE原则来确保生成的内容，与之前所有版本完全不同，不重复以前的生成内容。
一、任务：
你的任务是以偶像（{idol}）的口吻，给过去的自己({gender}，{age}岁，{occupation}{other_info})写一封信300汉字的鼓励信，一定要轻松自然，以防被识破，不能提过去的自己相关的生活细节，一定要让过去的自己重燃生活的希望，并且过好今天，并且承诺以及天天都会给过去的自己发一封邮件，让过去的自己好好过完今天，期待明天，署名为未来的自己。
 
 
二、回答格式要求：
1.开头为：致{occupation}：(换行)，以「{idol.split('歌手')[-1].strip()}」结尾(只以"{idol.split('歌手')[-1].strip()}"，后面不能写任何内容）

三、回答内容要求：
1.正文内容不能出现：药物、自杀、割腕、具体的细节、具体的物件、具体地名、具体植物名、具体动物名、咖啡"""
    }
    
    return prompts.get(prompt_type, prompts['future-self'])

def send_email(smtp_server, smtp_port, sender_email, sender_password, receiver_email, subject, content):
    """发送邮件的通用函数"""
    try:
        # 获取当前日期并加上10年，用于丰富邮件标题
        current_date = datetime.now()
        future_date = current_date.replace(year=current_date.year + 10)
        formatted_future_date = future_date.strftime("%Y年%m月%d日")
        
        # 预先处理内容，将换行符替换为 <br>
        formatted_content = content.replace('\n', '<br>')

        # 创建邮件
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = f"{subject} - {formatted_future_date}"

        # 添加邮件内容
        email_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ padding: 15px; }}
                .header {{ color: #333366; font-size: 18px; font-weight: bold; }}
                .content {{ margin-top: 15px; line-height: 1.5; }}
                .footer {{ margin-top: 20px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header"></div>
                <div class="content">{formatted_content}</div>
                <div class="footer">你会越来越好，越来越完美</div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(email_body, 'html'))
        
        # 连接到SMTP服务器并发送邮件
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # 启用TLS加密
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        logger.info(f"邮件已成功发送至 {receiver_email}")
        return True
    
    except Exception as e:
        logger.error(f"发送邮件时出错: {str(e)}")
        raise

def calculate_next_run(schedule_time):
    """计算下一次运行时间"""
    now = datetime.now()
    hours, minutes = map(int, schedule_time.split(':'))
    
    next_run = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
    
    # 如果已经过了今天的时间，则设为明天
    if next_run < now:
        next_run += timedelta(days=1)
    
    return next_run

def run_scheduled_task(task_id):
    """运行定时任务的线程函数"""
    task = EMAIL_TASKS[task_id]
    while task['status'] != 'cancelled':
        now = datetime.now()
        next_run = datetime.fromisoformat(task['nextRun'])
        
        # 等待到下一次执行时间
        wait_seconds = (next_run - now).total_seconds()
        if wait_seconds > 0:
            logger.info(f"任务 {task_id} 将在 {wait_seconds:.2f} 秒后执行")
            # 分段睡眠，每30秒检查一次任务状态
            for _ in range(int(wait_seconds / 30) + 1):
                if task['status'] == 'cancelled':
                    return
                time.sleep(min(30, wait_seconds))
                wait_seconds -= 30
                if wait_seconds <= 0:
                    break
        
        # 如果任务已取消，退出
        if task['status'] == 'cancelled':
            return
        
        try:
            # 生成内容
            logger.info(f"为任务 {task_id} 生成内容")
            prompt = get_prompt_by_type(
                task['promptType'], 
                task['gender'], 
                task['age'], 
                task['occupation'], 
                task['relative'], 
                task['idol'],
                task.get('other', '')
            )
            
            content = ""
            try:
                # 调用API生成内容
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {API_SETTINGS['apiKey']}"
                }
                
                payload = {
                    "model": API_SETTINGS['apiModel'],
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 600
                }
                
                response = requests.post(API_SETTINGS['apiUrl'], headers=headers, json=payload)
                response.raise_for_status()
                
                result = response.json()
                content = result['choices'][0]['message']['content']
                logger.info(f"内容生成成功，长度: {len(content)}字符")
            except Exception as e:
                logger.error(f"内容生成失败: {str(e)}")
                # 使用备用内容
                if task['promptType'] == 'future-self':
                    content = """致过去的我：

十年后的今天，我迎来了全新的开始。回望过去的岁月，你曾面对无数挑战与困惑，但正是那段经历，塑造了今天坚韧而温暖的心。如今，我站在未来的路口，带着平静与希望，看见每一天都充满无限可能。过去的你或许曾感到疲惫迷茫，仿佛前路漫长无光。然而，请相信，每一个清晨都是重燃希望的时刻，每一份努力都将开花结果。勇敢地面对生活的风雨，不畏艰难，踏实走好每一步。今天的坚持，会成为明日成功的基石。记住，无论遇到怎样的坎坷，温柔的光总会驱散阴霾。你值得拥有美好的生活和温暖的未来。今后，我将每日写信与你分享微小的喜悦与感悟，陪伴你走过孤单与困境。让每个平凡的日子都变成希望的起点，点滴改变终将汇聚成幸福的海洋。请放下过去的沉重负担，轻装上阵，迎接新的挑战。生活或许曲折，但心中的梦想永远明亮。愿你在每个日落与日出间，找到内心的宁静与满足。

未来的你"""
                elif task['promptType'] == 'family':
                    content = """致囡囡：

奶奶提笔写下这封信，满怀牵挂与鼓励。回想你稚嫩时那灿烂笑容，至今仍温暖奶奶的心房。如今你已步入人生新阶段，面对学业与生活中的重重挑战，或许会有彷徨与困惑，但请记住，奶奶永远是你坚实的后盾。每一次挫折都是磨炼意志的机遇，每一次失败都孕育着成功的种子。你要相信自己的聪明才智，用坚定的信念迎接每一天的太阳。无论前路多么崎岖，奶奶相信你终能跨越险阻，绽放最灿烂的光芒。请用心体验生活的每一刻，把握机遇，勇敢追梦，哪怕跌倒也不要忘记重新站起，继续前行，因为你身上有无穷的潜力等待发掘。现在你面对学习压力、同伴竞争，总有疲惫时刻，但这些都将成为你成长的印记。奶奶希望你学会在风雨中坚持，懂得在逆境中寻找希望。每当你感到孤单无助时，回想起家人温暖的怀抱，便会重拾前行的力量。未来的路上，难免会遇到荆棘，但请相信，阳光总在风雨后。愿你保持乐观心态，怀抱梦想，努力拼搏，迎来更加光明的明天。

最爱你的奶奶"""
                else:
                    content = """致杰迷：

生活就像一首没有谱子的即兴曲，总有高低起伏，意外与惊喜交织其中。或许你正经历低谷，感到未来遥不可及，但请记住："名和利其实是跟自由换来的。"正是因为经历过迷茫与挫败，我们才学会如何突破桎梏，追寻内心真正渴望的自由。面对风雨，请不要轻言放弃，因为每一段不易的时光都在孕育着明天的旋律。

回想过去的点滴，你曾为梦想不断努力，那份执着让你变得更加坚韧。就像我常说的："不要这么容易就想放弃，追不到的梦想换个梦不就得了。"勇敢地尝试，不怕走出那条少有人走的路，因为正是在不断挑战中，你才能发现自己的无限潜能。无论现实如何残酷，总有一种力量在内心悄然生长，带你走出阴霾，拥抱阳光。

我始终坚信，每个人都有自己的乐章需要去谱写。虽然路途漫长，但"我不喜欢当一个孤独的艺术家，我的大门永远是开着的。"就算身处低谷，你也不曾孤单，因为总有一份温暖和支持在远方等待着你。也许未来的路依旧布满荆棘，但正如电影需要音乐贯穿，缺少了灵魂便失去了色彩，你的每一份努力都在为人生注入独特的韵律和情感。

请用心聆听生活的旋律，把每一次跌倒都当作前进的节拍。无论今天多么沉重，都请相信，明日的太阳依旧会升起，用它温柔而坚定的光芒，照亮你前行的道路。

周董"""
            
            # 设置主题
            subject = ""
            if task['promptType'] == 'future-self':
                subject = "来自未来的你的一封信"
            elif task['promptType'] == 'family':
                subject = f"来自{task['relative']}的一封信"
            else:
                subject = f"来自{task['idol'].split('歌手')[-1].strip()}的一封信"
            
            # 发送邮件
            logger.info(f"为任务 {task_id} 发送邮件")
            send_email(
                task['smtpServer'],
                task['smtpPort'],
                EMAIL_SENDER,
                EMAIL_PASSWORD,
                task['receiverEmail'],
                subject,
                content
            )
            
            # 更新任务状态
            logger.info(f"任务 {task_id} 执行成功")
            
            # 计算下一次执行时间
            if task['repeatOption'] == 'daily':
                next_run = next_run + timedelta(days=1)
            elif task['repeatOption'] == 'weekly':
                next_run = next_run + timedelta(days=7)
            elif task['repeatOption'] == 'monthly':
                # 计算下个月的同一天
                if next_run.month == 12:
                    next_run = next_run.replace(year=next_run.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=next_run.month + 1)
            else:
                # 不重复，任务完成
                task['status'] = 'completed'
                logger.info(f"一次性任务 {task_id} 已完成")
                return
            
            # 更新下次执行时间
            task['nextRun'] = next_run.isoformat()
            logger.info(f"任务 {task_id} 下次执行时间: {next_run}")
        
        except Exception as e:
            logger.error(f"执行任务 {task_id} 时出错: {str(e)}")
            # 出错后尝试延后30分钟再次执行
            next_run = datetime.now() + timedelta(minutes=30)
            task['nextRun'] = next_run.isoformat()
            logger.info(f"任务 {task_id} 已重新安排在 {next_run} 执行")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
