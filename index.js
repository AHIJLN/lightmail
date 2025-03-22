export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    // 处理静态资源请求
    if (url.pathname === "/" || url.pathname === "/index.html") {
      return fetch(new URL("index.html", request.url));
    }
    
    // 处理 AI API 代理请求
    if (url.pathname === "/api/generate-content" && request.method === "POST") {
      try {
        const requestData = await request.json();
        
        // 使用环境变量中的 API 密钥
        const apiKey = env.AIKEY;
        
        // 调用阿里云 API
        const response = await fetch("https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${apiKey}`
          },
          body: JSON.stringify(requestData)
        });
        
        // 如果是流式响应，需要特殊处理
        if (requestData.stream) {
          // 创建一个新的 ReadableStream 来转发响应
          const { readable, writable } = new TransformStream();
          response.body.pipeTo(writable);
          
          return new Response(readable, {
            headers: {
              "Content-Type": "text/event-stream",
              "Cache-Control": "no-cache",
              "Connection": "keep-alive"
            }
          });
        }
        
        // 非流式响应直接返回
        const data = await response.json();
        return new Response(JSON.stringify(data), {
          headers: { "Content-Type": "application/json" }
        });
      } catch (error) {
        return new Response(JSON.stringify({ error: error.message }), {
          status: 500,
          headers: { "Content-Type": "application/json" }
        });
      }
    }
    
    
    // 处理其他静态资源
    return fetch(new URL(url.pathname, request.url));
  }
};
