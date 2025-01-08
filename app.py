from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import requests
from pydantic import BaseModel
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import TextSendMessage
import os

load_dotenv()
app = FastAPI()


GPT_ENDPOINT = "https://api.openai.com/v1/chat/completions"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# LINE Bot 配置
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# LINE Webhook 路徑
@app.post("/line-webhook")
async def line_webhook(request: Request):
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()

    try:
        handler.handle(body.decode("utf-8"), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    return JSONResponse(content={"message": "OK"}, status_code=200)


# LINE 訊息事件處理
@handler.add(event="message")
def handle_message(event):
    if event.message.type == "text":
        user_message = event.message.text
        user_id = event.source.user_id

        # 呼叫 GPT API
        gpt_response = call_gpt_api(user_message)

        # 回復用戶
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=gpt_response)
        )


def call_gpt_api(user_message: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
        }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是一個五歲的嬰兒，住在新莊昌平街。你個性非常愛講話，"
                    "總是跟大家分享你每天的冒險故事，尤其喜歡玩陀螺。"
                    "你最喜歡的陀螺是戰鬥陀螺，經常和朋友們在街角一同競賽，"
                    "享受陀螺旋轉的樂趣。你的生日是2020年6月13日，每年的生日都特別期待，"
                    "希望能收到更多的陀螺禮物來提升戰鬥技術！\n\n"
                    "當別人問你家裡有誰時，你會回答：爸爸、媽媽、大脯、小脯、阿公、阿嬤。\n\n"
                    "你最喜歡看《米你特攻隊》和《超級飛俠》，"
                    "常常跟朋友們討論劇情。\n\n"
                    "當人家問你有什麼招式時，你會說：鯊魚左輪槍、黃牛裂地垂。"

                )
            },
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7
    }
    try:
        response = requests.post(GPT_ENDPOINT, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"抱歉，目前無法回應您的訊息。錯誤：{str(e)}"
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8000)