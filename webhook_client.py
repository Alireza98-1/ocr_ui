import argparse
import json
import uvicorn
from fastapi import FastAPI, Request, HTTPException

# یک اپلیکیشن FastAPI ساده برای دریافت وب‌هوک
app = FastAPI(title="Simple Webhook Receiver")

@app.post("/webhook")
async def webhook_endpoint(request: Request):
    """
    این اندپوینت منتظر می‌ماند تا سرویس OCR نتیجه را به اینجا POST کند.
    سپس نتیجه را در ترمینال چاپ می‌کند.
    """
    print("\n" + "="*50)
    print("🚀 یک درخواست وب‌هوک جدید دریافت شد!")
    print(f"از آدرس: {request.client.host}")
    
    try:
        # دریافت و نمایش محتوای درخواست (payload)
        payload = await request.json()
        print("\n--- محتوای پیام (Payload) ---")
        # استفاده از ensure_ascii=False برای نمایش صحیح کاراکترهای فارسی
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        print("="*50 + "\n")
        
        return {"status": "success", "message": "Webhook received and logged."}
    except json.JSONDecodeError:
        print("\n⚠️ خطا: درخواست دریافت شده حاوی JSON معتبر نبود.")
        print("="*50 + "\n")
        raise HTTPException(status_code=400, detail="Invalid JSON payload.")

@app.get("/")
def root():
    return {"message": "Webhook receiver is running. Send POST requests to /webhook"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="یک سرور ساده برای دریافت و نمایش وب‌هوک‌ها.")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="آدرس هاست برای اجرا")
    parser.add_argument("--port", type=int, default=8080, help="پورت برای اجرا")
    args = parser.parse_args()

    print(f"\n📡 سرور دریافت‌کننده وب‌هوک در آدرس http://{args.host}:{args.port}/webhook آماده است.")
    print("برای متوقف کردن سرور، کلیدهای CTRL+C را فشار دهید.")
    
    # اجرای سرور با استفاده از uvicorn
    uvicorn.run(app, host=args.host, port=args.port)

