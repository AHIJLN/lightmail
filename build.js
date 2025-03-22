const fs = require('fs');
const path = require('path');

// 读取原始的 index.html
let html = fs.readFileSync('index.html', 'utf8');

// 将环境变量注入到 HTML 中
html = html.replace('const API_KEY = "AIKEY";', `const API_KEY = "${process.env.AIKEY}";`);

// 写入修改后的 HTML
fs.writeFileSync('dist/index.html', html);
