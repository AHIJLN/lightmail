// functions/api/generate-content.js
export async function onRequest(context) {
  const { request, env } = context;
  
  // 只接受 POST 请求
  if (request.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405 });
  }
  
  try {
    // 获取请求数据
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
    
    // 如果是流式响应，直接传递流
    if (requestData.stream) {
      // 创建一个转换流，直接传递JSON数据而不是SSE格式
      const { readable, writable } = new TransformStream({
        transform(chunk, controller) {
          // 将原始数据直接传递
          controller.enqueue(chunk);
        }
      });
      
      // 将原始响应通过转换流传递
      response.body.pipeTo(writable).catch(err => console.error('Stream error:', err));
      
      return new Response(readable, {
        headers: {
          "Content-Type": "application/octet-stream",
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
