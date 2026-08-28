import os
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai

app = FastAPI()

# OpenAI API Key (ভবিষ্যতে আমরা সিক্রেট কি-তে রাখবো)
openai.api_key = os.getenv("OPENAI_API_KEY", "YOUR_API_KEY")

APP_DATABASE = {}

class InitAppRequest(BaseModel):
    user_email: str
    prompt: str

class VerifyAndGenerateRequest(BaseModel):
    app_id: str
    transaction_id: str

@app.post("/initiate-app/")
async def initiate_app(request: InitAppRequest):
    app_id = f"app_{uuid.uuid4().hex[:8]}"
    APP_DATABASE[app_id] = {
        "user_email": request.user_email,
        "prompt": request.prompt,
        "status": "Pending_Payment",
        "download_url": None,
        "download_count": 0
    }
    return {
        "status": "Success",
        "app_id": app_id,
        "fee_amount": "BDT 500",
        "payment_instruction": "বিকাশ বা নগদে ৫০০ টাকা পাঠিয়ে /verify-and-generate/ এ TrxID দিন।"
    }

@app.post("/verify-and-generate/")
async def verify_and_generate(request: VerifyAndGenerateRequest):
    app_id = request.app_id
    if app_id not in APP_DATABASE:
        raise HTTPException(status_code=404, detail="ভুল App ID!")
    app_data = APP_DATABASE[app_id]
    if app_data["status"] == "Completed":
        raise HTTPException(status_code=400, detail="এই পেমেন্টে অলরেডি অ্যাপ তৈরি শেষ!")
    if len(request.transaction_id) < 6:
        raise HTTPException(status_code=400, detail="অবৈধ TrxID!")
    
    try:
        system_instruction = "Generate a single-file beautiful HTML/CSS video app based on prompt. Return ONLY valid HTML."
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": app_data["prompt"]}
            ]
        )
        html_code = response.choices.message.content.strip()
        file_name = f"{app_id}.html"
        os.makedirs("./static", exist_ok=True)
        with open(f"./static/{file_name}", "w", encoding="utf-8") as f:
            f.write(html_code)
            
        app_data["status"] = "Completed"
        app_data["download_url"] = f"https://your-server-url/static/{file_name}"
        
        return {
            "status": "App Generated",
            "message": "পেমেন্ট সফল! অ্যাপ তৈরি হয়েছে।",
            "download_link": app_data["download_url"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
