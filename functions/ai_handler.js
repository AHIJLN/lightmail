export async function onRequest(context) {
  // 从环境变量中获取
  const { AIKEY } = context.env;
  
  // 例如你要调用第三方 API，需要 AIKEY 做认证
  // const response = await fetch("https://api.example.com/", {
  //   headers: { "Authorization": `Bearer ${AIKEY}` }
  // });

  return new Response("AIKEY length is: " + AIKEY.length);
}
