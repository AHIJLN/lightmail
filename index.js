export default {
  async fetch(request, env) {
    const url = new URL(request.url)
    
    // 根据请求路径判断是否是 API 调用
    if (url.pathname.startsWith('/api/generate')) {
      // 从环境变量中获取 API 密钥
      const aiKey = env.AIKEY
      // 根据需要构造调用 AI 接口的请求
      const response = await fetch("https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": "Bearer " + aiKey
        },
        body: await request.text()
      })
      return response
    }
    
    // 否则，返回静态资源（index.html 等）
    return await env.ASSETS.fetch(request)
  }
}
