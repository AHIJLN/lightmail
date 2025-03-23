// functions/api/generate-content.js
export async function onRequest(context) {
  const { request, env } = context;

  // 只允许 POST
  if (request.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  try {
    // 读取前端请求的 JSON
    const requestData = await request.json();
    
    // 从环境变量获取 API Key
    const apiKey = env.AIKEY;

    // 调用阿里云 DashScope API
    const response = await fetch("https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${apiKey}`
      },
      body: JSON.stringify(requestData)
    });

    // 如果远端请求失败
    if (!response.ok) {
      return new Response(
        JSON.stringify({ error: "API request failed", status: response.status }),
        { status: 500, headers: { "Content-Type": "application/json" } }
      );
    }

    // 一次性读取远端返回的完整 JSON
    const data = await response.json();

    // 返回给前端
    return new Response(JSON.stringify(data), {
      headers: { "Content-Type": "application/json" }
    });

  } catch (error) {
    // 处理异常
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
}

