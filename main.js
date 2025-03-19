document.addEventListener('DOMContentLoaded', function() {
    // DOM元素引用
    const emailSettingsForm = document.getElementById('emailSettingsForm');
    const senderEmailInput = document.getElementById('senderEmail');
    const authCodeInput = document.getElementById('authCode');
    const receiverEmailInput = document.getElementById('receiverEmail');
    const scheduleTimeInput = document.getElementById('scheduleTime');
    const toggleAuthCodeBtn = document.getElementById('toggleAuthCode');
    const scheduleStatusSection = document.getElementById('scheduleStatus');
    const nextSendTimeSpan = document.getElementById('nextSendTime');
    const stopScheduleBtn = document.getElementById('stopScheduleBtn');
    const testSendBtn = document.getElementById('testSendBtn');
    const repeatFrequencySpan = document.getElementById('repeatFrequency');
    const selectedPromptSpan = document.getElementById('selectedPrompt');
    const scheduleProgress = document.getElementById('scheduleProgress');
    const timeRemainingSpan = document.getElementById('timeRemaining');
    const networkAlert = document.getElementById('networkAlert');
    const notificationToast = document.getElementById('notificationToast');
    const toastMessage = document.getElementById('toastMessage');
    
    // 创建Bootstrap Toast对象
    const toast = new bootstrap.Toast(notificationToast);
    
    // 全局变量
    let scheduleInterval;
    let startTime;
    let endTime;
    let isScheduleRunning = false;
    
    // 加载保存的设置
    loadEmailSettings();
    
    // 初始化UI状态
    initializeUI();
    
    // 定义鼓励Prompt模板
    const promptTemplates = {
        futureSelf: {
            systemPrompt: "你是一个专业的谈判专家和顶级心理医生顾问，有10年丰富经验并拯救了100000个轻生少年少女和中老年人。",
            userPrompt: "以10年后成功的自己的口吻，给过去的自己（男，35岁，程序员）写一封300汉字的鼓励信。内容须轻松自然，避免提及过去的自己相关生活细节。力求使对方重燃生活希望，并承诺每天发送邮件鼓励，帮助其好好过每一天。请以'致过去的我：'开头，并以'未来的你'结尾。正文中不得出现'药物、自杀、割腕、具体的细节、具体的物件、具体地名、具体植物名、具体动物名、咖啡'等敏感词汇。"
        },
        family: {
            systemPrompt: "你是一个专业的谈判专家和顶级心理医生顾问，有10年丰富经验并拯救了100000个轻生少年少女和中老年人。",
            userPrompt: "以家人（奶奶）的口吻，给过去的自己（女，17岁，学生）写一封300汉字的鼓励信。内容须轻松自然，避免提及过去的自己相关生活细节。目标是激发对方重燃生活希望，并承诺天天发送邮件鼓励，帮助其度过每一天。请以'致囡囡：'开头，并以'最爱你的奶奶'结尾。正文中不得出现'药物、自杀、割腕、具体的细节、具体的物件、具体地名、具体植物名、具体动物名、咖啡'等敏感词汇。"
        },
        idol: {
            systemPrompt: "你是一个专业的谈判专家和顶级心理医生顾问，有10年丰富经验并拯救了100000个轻生少年少女和中老年人。",
            userPrompt: "以华语歌坛创作型歌手周杰伦的口吻，给过去的自己（男，16岁，学生）写一封300汉字的鼓励信。内容须轻松自然，避免提及过去的自己相关生活细节。力求让对方重燃生活希望，并承诺每天发送邮件鼓励，帮助其过好今天、期待明天。请以'致杰迷：'开头，并以'周董'结尾。正文中不得出现'药物、自杀、割腕、具体的细节、具体的物件、具体地名、具体植物名、具体动物名、咖啡'等敏感词汇。"
        }
    };
    
    // 初始化UI状态
    function initializeUI() {
        // 检查是否有正在运行的定时任务
        const scheduleData = JSON.parse(localStorage.getItem('lightMailSchedule')) || {};
        if (scheduleData.isRunning) {
            // 恢复定时任务状态
            isScheduleRunning = true;
            startTime = new Date().getTime();
            endTime = new Date(scheduleData.nextSendTime).getTime();
            
            // 更新UI
            updateScheduleUI(scheduleData);
            scheduleStatusSection.classList.remove('d-none');
            startScheduleCountdown();
        }
        
        // 检查网络状态
        checkNetworkStatus();
        window.addEventListener('online', checkNetworkStatus);
        window.addEventListener('offline', checkNetworkStatus);
    }
    
    // 检查网络状态
    function checkNetworkStatus() {
        if (navigator.onLine) {
            networkAlert.classList.add('d-none');
        } else {
            networkAlert.classList.remove('d-none');
            showNotification('检测到网络异常，邮件可能无法发送', 'warning');
        }
    }
    
    // 事件监听器
    emailSettingsForm.addEventListener('submit', saveEmailSettings);
    toggleAuthCodeBtn.addEventListener('click', togglePasswordVisibility);
    stopScheduleBtn.addEventListener('click', stopSchedule);
    testSendBtn.addEventListener('click', sendTestEmail);
    
    // 保存邮箱设置
    function saveEmailSettings(e) {
        e.preventDefault();
        
        // 获取表单值
        const senderEmail = senderEmailInput.value;
        const authCode = authCodeInput.value;
        const receiverEmail = receiverEmailInput.value || senderEmail;
        const scheduleTime = scheduleTimeInput.value;
        const repeatOption = document.querySelector('input[name="repeatOption"]:checked').value;
        const promptType = document.querySelector('input[name="promptType"]:checked').value;
        
        // 计算下次发送时间
        const nextSendTime = calculateNextSendTime(scheduleTime);
        
        // 准备保存的数据
        const emailSettings = {
            senderEmail,
            authCode,
            receiverEmail,
            scheduleTime,
            repeatOption,
            promptType,
            nextSendTime: nextSendTime.toISOString(),
            isRunning: true,
            lastUpdated: new Date().toISOString()
        };
        
        // 保存到localStorage
        localStorage.setItem('lightMailSettings', JSON.stringify(emailSettings));
        localStorage.setItem('lightMailSchedule', JSON.stringify({
            isRunning: true,
            nextSendTime: nextSendTime.toISOString(),
            repeatOption,
            promptType
        }));
        
        // 更新UI
        updateScheduleUI(emailSettings);
        scheduleStatusSection.classList.remove('d-none');
        
        // 开始倒计时
        startScheduleCountdown();
        
        // 显示通知
        showNotification('邮箱设置已保存，定时发送已启动', 'success');
    }
    
    // 更新定时发送UI
    function updateScheduleUI(data) {
        const nextSendDate = new Date(data.nextSendTime);
        nextSendTimeSpan.textContent = nextSendDate.getHours().toString().padStart(2, '0') + ':' + 
                                      nextSendDate.getMinutes().toString().padStart(2, '0');
        
        // 更新发送频率显示
        switch(data.repeatOption) {
            case 'daily':
                repeatFrequencySpan.textContent = '每天';
                break;
            case 'weekly':
                repeatFrequencySpan.textContent = '每周';
                break;
            case 'once':
                repeatFrequencySpan.textContent = '仅一次';
                break;
        }
        
        // 更新选择的Prompt显示
        switch(data.promptType) {
            case 'futureSelf':
                selectedPromptSpan.textContent = '10年后自己的信';
                break;
            case 'family':
                selectedPromptSpan.textContent = '亲人的信';
                break;
            case 'idol':
                selectedPromptSpan.textContent = '偶像的信';
                break;
        }
    }
    
    // 计算下次发送时间
    function calculateNextSendTime(timeString) {
        const [hours, minutes] = timeString.split(':').map(Number);
        const now = new Date();
        const nextSendTime = new Date();
        
        // 设置时间
        nextSendTime.setHours(hours, minutes, 0, 0);
        
        // 如果设置的时间已经过去，则设为明天
        if (nextSendTime < now) {
            nextSendTime.setDate(nextSendTime.getDate() + 1);
        }
        
        return nextSendTime;
    }
    
    // 开始定时倒计时
    function startScheduleCountdown() {
        // 清除可能存在的定时器
        if (scheduleInterval) {
            clearInterval(scheduleInterval);
        }
        
        // 获取当前时间和目标时间
        startTime = new Date().getTime();
        const scheduleData = JSON.parse(localStorage.getItem('lightMailSchedule')) || {};
        endTime = new Date(scheduleData.nextSendTime).getTime();
        
        // 更新进度条和倒计时
        updateProgressBar();
        
        // 设置定时器，每秒更新一次
        scheduleInterval = setInterval(() => {
            updateProgressBar();
            
            // 检查是否到达发送时间
            const now = new Date().getTime();
            if (now >= endTime) {
                sendScheduledEmail();
            }
        }, 1000);
    }
    
    // 更新进度条
    function updateProgressBar() {
        const now = new Date().getTime();
        const totalDuration = endTime - startTime;
        const elapsed = now - startTime;
        const remaining = endTime - now;
        
        // 计算进度百分比
        let progressPercent = (elapsed / totalDuration) * 100;
        progressPercent = Math.min(progressPercent, 100); // 确保不超过100%
        
        // 更新进度条
        scheduleProgress.style.width = progressPercent + '%';
        
        // 更新剩余时间文本
        const hours = Math.floor(remaining / (1000 * 60 * 60));
        const minutes = Math.floor((remaining % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((remaining % (1000 * 60)) / 1000);
        
        timeRemainingSpan.textContent = `距离下次发送还有: ${hours}小时 ${minutes}分钟 ${seconds}秒`;
    }
    
    // 发送定时邮件
    function sendScheduledEmail() {
        clearInterval(scheduleInterval);
        
        // 检查网络状态
        if (!navigator.onLine) {
            showNotification('网络异常，邮件发送失败', 'danger');
            scheduleNextSend();
            return;
        }
        
        // 获取设置
        const settings = JSON.parse(localStorage.getItem('lightMailSettings')) || {};
        const scheduleData = JSON.parse(localStorage.getItem('lightMailSchedule')) || {};
        
        // 获取API设置
        const apiSettings = JSON.parse(localStorage.getItem('lightMailApiSettings')) || {};
        if (!apiSettings.apiKey || !apiSettings.apiUrl || !apiSettings.modelName) {
            showNotification('API设置不完整，邮件发送失败', 'danger');
            scheduleNextSend();
            return;
        }
        
        // 获取对应的Prompt模板
        const promptTemplate = promptTemplates[scheduleData.promptType];
        
        // 构建API请求
        generateEmail(promptTemplate, apiSettings)
            .then(emailContent => {
                // 发送邮件
                sendEmail(settings.senderEmail, settings.authCode, settings.receiverEmail, emailContent)
                    .then(() => {
                        showNotification('邮件发送成功', 'success');
                    })
                    .catch(error => {
                        console.error('邮件发送失败:', error);
                        showNotification('邮件发送失败: ' + error.message, 'danger');
                    })
                    .finally(() => {
                        // 计算下一次发送时间
                        scheduleNextSend();
                    });
            })
            .catch(error => {
                console.error('邮件内容生成失败:', error);
                showNotification('邮件内容生成失败: ' + error.message, 'danger');
                // 尽管生成失败，仍计划下一次发送
                scheduleNextSend();
            });
    }
    
    // 安排下一次发送
    function scheduleNextSend() {
        const scheduleData = JSON.parse(localStorage.getItem('lightMailSchedule')) || {};
        const settings = JSON.parse(localStorage.getItem('lightMailSettings')) || {};
        
        // 根据重复选项计算下一次发送时间
        let nextSendTime = new Date(scheduleData.nextSendTime);
        
        switch(scheduleData.repeatOption) {
            case 'daily':
                // 下一天相同时间
                nextSendTime.setDate(nextSendTime.getDate() + 1);
                break;
            case 'weekly':
                // 下周相同时间
                nextSendTime.setDate(nextSendTime.getDate() + 7);
                break;
            case 'once':
                // 仅一次，标记为已停止
                stopSchedule();
                return;
        }
        
        // 更新scheduleData
        scheduleData.nextSendTime = nextSendTime.toISOString();
        localStorage.setItem('lightMailSchedule', JSON.stringify(scheduleData));
        
        // 更新UI
        updateScheduleUI(scheduleData);
        
        // 重新开始倒计时
        startScheduleCountdown();
    }
    
    // 通过AI API生成邮件内容
    async function generateEmail(promptTemplate, apiSettings) {
        try {
            const response = await fetch(apiSettings.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiSettings.apiKey}`
                },
                body: JSON.stringify({
                    model: apiSettings.modelName,
                    messages: [
                        {
                            role: "system",
                            content: promptTemplate.systemPrompt
                        },
                        {
                            role: "user",
                            content: promptTemplate.userPrompt
                        }
                    ]
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error?.message || 'API请求失败');
            }
            
            const data = await response.json();
            return data.choices[0].message.content.trim();
        } catch (error) {
            console.error('生成邮件内容失败:', error);
            throw error;
        }
    }
    
    // 发送邮件（模拟）
    async function sendEmail(from, authCode, to, content) {
        // 在实际项目中，这里应该调用真实的邮件发送服务
        // 出于演示目的，我们使用一个模拟的延迟Promise
        return new Promise((resolve, reject) => {
            setTimeout(() => {
                // 随机成功或失败（90%概率成功）
                if (Math.random() < 0.9) {
                    console.log(`模拟发送邮件: 从 ${from} 到 ${to}`);
                    console.log(`邮件内容: ${content}`);
                    resolve();
                } else {
                    reject(new Error('邮件服务器连接失败'));
                }
            }, 1500);
        });
    }
    
    // 发送测试邮件
    function sendTestEmail() {
        // 检查网络状态
        if (!navigator.onLine) {
            showNotification('网络异常，无法发送测试邮件', 'warning');
            return;
        }
        
        // 获取设置
        const settings = JSON.parse(localStorage.getItem('lightMailSettings')) || {};
        if (!settings.senderEmail || !settings.authCode) {
            showNotification('邮箱设置不完整，请先保存设置', 'warning');
            return;
        }
        
        // 获取API设置
        const apiSettings = JSON.parse(localStorage.getItem('lightMailApiSettings')) || {};
        if (!apiSettings.apiKey || !apiSettings.apiUrl || !apiSettings.modelName) {
            showNotification('API设置不完整，请先完成API设置', 'warning');
            return;
        }
        
        // 显示发送中状态
        testSendBtn.disabled = true;
        testSendBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 发送中...';
        
        // 获取当前选择的Prompt类型
        const scheduleData = JSON.parse(localStorage.getItem('lightMailSchedule')) || {};
        const promptType = scheduleData.promptType || 'futureSelf';
        const promptTemplate = promptTemplates[promptType];
        
        // 生成邮件内容并发送
        generateEmail(promptTemplate, apiSettings)
            .then(emailContent => {
                return sendEmail(settings.senderEmail, settings.authCode, settings.receiverEmail, emailContent);
            })
            .then(() => {
                showNotification('测试邮件发送成功', 'success');
            })
            .catch(error => {
                console.error('测试邮件发送失败:', error);
                showNotification('测试邮件发送失败: ' + error.message, 'danger');
            })
            .finally(() => {
                // 恢复按钮状态
                testSendBtn.disabled = false;
                testSendBtn.textContent = '测试发送';
            });
    }
    
    // 停止定时发送
    function stopSchedule() {
        if (scheduleInterval) {
            clearInterval(scheduleInterval);
        }
        
        // 更新localStorage状态
        const scheduleData = JSON.parse(localStorage.getItem('lightMailSchedule')) || {};
        scheduleData.isRunning = false;
        localStorage.setItem('lightMailSchedule', JSON.stringify(scheduleData));
        
        // 隐藏定时状态区域
        scheduleStatusSection.classList.add('d-none');
        
        // 显示通知
        showNotification('定时发送已停止', 'info');
    }
    
    // 加载保存的邮箱设置
    function loadEmailSettings() {
        const settings = JSON.parse(localStorage.getItem('lightMailSettings')) || {};
        
        // 填充表单
        if (settings.senderEmail) senderEmailInput.value = settings.senderEmail;
        if (settings.authCode) authCodeInput.value = settings.authCode;
        if (settings.receiverEmail) receiverEmailInput.value = settings.receiverEmail;
        if (settings.scheduleTime) scheduleTimeInput.value = settings.scheduleTime;
        
        // 选择重复选项
        if (settings.repeatOption) {
            document.querySelector(`input[name="repeatOption"][value="${settings.repeatOption}"]`).checked = true;
        }
        
        // 选择Prompt类型
        if (settings.promptType) {
            document.querySelector(`input[name="promptType"][value="${settings.promptType}"]`).checked = true;
        }
    }
    
    // 切换密码可见性
    function togglePasswordVisibility() {
        const icon = toggleAuthCodeBtn.querySelector('i');
        if (authCodeInput.type === 'password') {
            authCodeInput.type = 'text';
            icon.classList.remove('bi-eye');
            icon.classList.add('bi-eye-slash');
        } else {
            authCodeInput.type = 'password';
            icon.classList.remove('bi-eye-slash');
            icon.classList.add('bi-eye');
        }
    }
    
    // 显示通知提示
    function showNotification(message, type = 'success') {
        toastMessage.textContent = message;
        notificationToast.classList.remove('bg-success', 'bg-danger', 'bg-warning', 'bg-info');
        
        switch(type) {
            case 'success':
                notificationToast.classList.add('bg-success', 'text-white');
                break;
            case 'danger':
                notificationToast.classList.add('bg-danger', 'text-white');
                break;
            case 'warning':
                notificationToast.classList.add('bg-warning');
                break;
            case 'info':
                notificationToast.classList.add('bg-info');
                break;
        }
        
        toast.show();
    }
});
