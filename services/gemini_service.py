# services/gemini_service.py
"""
Gemini AI Service - รวมทุกฟังก์ชันที่เกี่ยวข้องกับ Gemini API
"""

import google.generativeai as genai
import os
from typing import List, Dict, Optional

# -----------------------------
# 🔧 Gemini Configuration
# -----------------------------
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ✅ กำหนดค่าพารามิเตอร์ที่สามารถ "จูน" ได้
GENERATION_CONFIG = {
    "temperature": 0.7,        
    "top_p": 0.9,              
    "top_k": 40,               
    "max_output_tokens": 512,  
}

def create_gemini_model():
    """สร้างโมเดล Gemini ที่มีพารามิเตอร์จูนไว้แล้ว"""
    return genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        generation_config=GENERATION_CONFIG
    )

# -----------------------------
# ✳️ ฟังก์ชันสรุปรีวิวสถานที่
# -----------------------------
def summarize_place_reviews(place_name: str, 
                            reviews: Optional[List[str]] = None, 
                            rating: Optional[float] = None, 
                            categories: Optional[List[str]] = None) -> str:
    """
    สร้างสรุปรีวิวสถานที่จาก AI
    
    Args:
        place_name: ชื่อสถานที่
        reviews: รายการรีวิวจากผู้ใช้
        rating: คะแนนเฉลี่ย
        categories: หมวดหมู่สถานที่
    
    Returns:
        ข้อความสรุปรีวิวจาก AI
    """
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    # เตรียม prompt
    reviews_text = ""
    if reviews and len(reviews) > 0:
        reviews_text = "\n".join([f"- {r}" for r in reviews[:5]])
    else:
        reviews_text = "ไม่มีรีวิวจากผู้ใช้"
    
    prompt = f"""
    สรุปข้อมูลสถานที่ท่องเที่ยวต่อไปนี้แบบกระชับและน่าสนใจ:

    ชื่อสถานที่: {place_name}
    คะแนน: {rating if rating else 'ไม่มีข้อมูล'}
    หมวดหมู่: {', '.join(categories) if categories else 'ไม่ระบุ'}

    รีวิวจากผู้ใช้:
    {reviews_text}

    กรุณาสรุปโดยใช้รูปแบบดังนี้ (ห้ามใช้ Markdown หรือสัญลักษณ์พิเศษอย่าง ** หรือ #):

    📍 จุดเด่น:
    (2-3 ประโยคสั้นๆ สรุปสิ่งที่โดดเด่นของสถานที่)

    👥 เหมาะกับใครบ้าง:
    (ระบุประเภทนักท่องเที่ยว เช่น ครอบครัว คู่รัก สายคาเฟ่)

    💡 คำแนะนำ:
    (ข้อควรรู้หรือเคล็ดลับสั้นๆ สำหรับการไปเที่ยว)

    ใช้ภาษาไทยแบบเป็นกันเอง ห้ามเกิน 200 คำ
    """

    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"❌ Gemini summarize error: {e}")
        return f"สถานที่นี้มีคะแนน {rating if rating else 'ไม่มีข้อมูล'} และอยู่ในหมวด {', '.join(categories) if categories else 'ทั่วไป'}"


# -----------------------------
# ✳️ ฟังก์ชันสรุปสถานที่ทั้งหมด
# -----------------------------
def generate_place_summary(places: List[Dict], search_type: str = "province") -> str:
    model = create_gemini_model()
    
    places_text = "\n".join([
        f"- {p.get('name')} (คะแนน: {p.get('rating', 'N/A')})"
        for p in places[:5]
    ])
    
    prompt = f"""
    สรุปรายการสถานที่ท่องเที่ยวต่อไปนี้แบบสั้นและกระชับ:
    
    {places_text}
    
    สรุปในรูปแบบ:
    - ภาพรวมของสถานที่ทั้งหมด
    - แนวทางการเลือกไปเที่ยว
    
    ไม่เกิน 200 คำ ใช้ภาษาไทยเป็นกันเอง
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"❌ Gemini summary error: {e}")
        return "กำลังวิเคราะห์ข้อมูล..."


# -----------------------------
# ✳️ ฟังก์ชันถามทั่วไป
# -----------------------------
def ask_gemini_general(prompt: str) -> str:
    model = create_gemini_model()
    
    full_prompt = f"""
    คุณคือผู้ช่วยท่องเที่ยวที่เป็นมิตรและมีความรู้เกี่ยวกับการท่องเที่ยวในประเทศไทย
    
    ตอบคำถามต่อไปนี้แบบกระชับและเป็นประโยชน์:
    {prompt}
    
    ใช้ภาษาไทย ไม่เกิน 200 คำ ตอบแบบเป็นกันเอง
    """
    try:
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        print(f"❌ Gemini general error: {e}")
        return f"ขออภัยครับ เกิดข้อผิดพลาดในการสื่อสารกับ AI: {str(e)}"


# -----------------------------
# ✳️ ฟังก์ชันแนะนำสถานที่ต่อไป
# -----------------------------
def ask_next_place_suggestion(current_place: Optional[str] = None, 
                              province: Optional[str] = None,
                              categories: Optional[List[str]] = None) -> str:
    model = create_gemini_model()
    
    categories_text = f"หมวดหมู่ที่สนใจ: {', '.join(categories)}" if categories else ""
    
    prompt = f"""
    ผู้ใช้กำลังท่องเที่ยวและต้องการแนะนำสถานที่ต่อไป:
    
    สถานที่ปัจจุบัน: {current_place if current_place else 'ยังไม่ได้ระบุ'}
    จังหวัด: {province if province else 'ยังไม่ได้ระบุ'}
    {categories_text}
    
    แนะนำสถานที่ท่องเที่ยว 2-3 แห่งที่ควรไปต่อ พร้อมเหตุผลสั้นๆ
    
    ตอบในรูปแบบ:
    1. [ชื่อสถานที่] - เหตุผลที่ควรไป (1 ประโยค)
    2. [ชื่อสถานที่] - เหตุผลที่ควรไป (1 ประโยค)
    
    ใช้ภาษาไทย ไม่เกิน 200 คำ เป็นกันเอง
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"❌ Gemini next place error: {e}")
        return "ขอโทษครับ ไม่สามารถแนะนำสถานที่ได้ในขณะนี้ กรุณาลองใหม่อีกครั้ง"


# -----------------------------
# ✳️ ฟังก์ชันสนทนาต่อเนื่อง
# -----------------------------
def generate_conversation_response(context_chain: str, user_message: str) -> str:
    model = create_gemini_model()
    
    prompt = f"""
    คุณคือผู้ช่วยท่องเที่ยวที่ชาญฉลาด สามารถเข้าใจบริบทการสนทนาต่อเนื่อง
    
    ประวัติการสนทนา:
    {context_chain}
    
    ข้อความล่าสุดจากผู้ใช้:
    {user_message}
    
    ตอบคำถามโดยคำนึงถึงบริบทการสนทนาทั้งหมด
    ใช้ภาษาไทยที่เป็นกันเอง กระชับ ไม่เกิน 200 คำ
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"❌ Gemini conversation error: {e}")
        return f"ขออภัยครับ เกิดข้อผิดพลาด: {str(e)}"


# -----------------------------
# ✳️ ฟังก์ชันทั่วไป
# -----------------------------
def get_gemini_response(user_message: str, prompt_prefix: str = "") -> str:
    model = create_gemini_model()
    
    full_prompt = f"{prompt_prefix}\n\nผู้ใช้: {user_message}\nผู้ช่วย:" if prompt_prefix else user_message
    try:
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        print(f"❌ Gemini error: {e}")
        return f"ขออภัยครับ เกิดข้อผิดพลาด: {str(e)}"