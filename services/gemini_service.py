# services/gemini_service.py
"""
Gemini AI Service - รวมทุกฟังก์ชันที่เกี่ยวข้องกับ Gemini API
"""

import google.generativeai as genai
import os
from typing import List, Dict, Optional

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


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
    
    สรุปในรูปแบบ:
    1. จุดเด่น (2-3 ประโยคสั้นๆ)
    2. เหมาะกับใครบ้าง
    3. คำแนะนำสำหรับการไป
    
    ใช้ภาษาไทยที่เป็นกันเอง ไม่เกิน 150 คำ
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"❌ Gemini summarize error: {e}")
        return f"สถานที่นี้มีคะแนน {rating if rating else 'ไม่มีข้อมูล'} และอยู่ในหมวด {', '.join(categories) if categories else 'ทั่วไป'}"


def generate_place_summary(places: List[Dict], search_type: str = "province") -> str:
    """
    สร้างสรุปรายการสถานที่ทั้งหมด
    
    Args:
        places: รายการสถานที่
        search_type: ประเภทการค้นหา (province, route)
    
    Returns:
        ข้อความสรุปจาก AI
    """
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
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
    
    ไม่เกิน 100 คำ ใช้ภาษาไทยเป็นกันเอง
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"❌ Gemini summary error: {e}")
        return "กำลังวิเคราะห์ข้อมูล..."


def ask_gemini_general(prompt: str) -> str:
    """
    ถามคำถามทั่วไปกับ Gemini (ไม่เกี่ยวกับสถานที่เฉพาะ)
    
    Args:
        prompt: คำถามจากผู้ใช้
    
    Returns:
        คำตอบจาก AI
    """
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
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


def ask_next_place_suggestion(current_place: Optional[str] = None, 
                              province: Optional[str] = None,
                              categories: Optional[List[str]] = None) -> str:
    """
    แนะนำสถานที่ต่อไปที่ควรไป (ใช้กับ "ไปต่อไหนดี")
    
    Args:
        current_place: สถานที่ปัจจุบันที่ผู้ใช้อยู่
        province: จังหวัด
        categories: หมวดหมู่ที่สนใจ
    
    Returns:
        คำแนะนำสถานที่จาก AI
    """
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
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
    
    ใช้ภาษาไทย ไม่เกิน 150 คำ เป็นกันเอง
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"❌ Gemini next place error: {e}")
        return "ขอโทษครับ ไม่สามารถแนะนำสถานที่ได้ในขณะนี้ กรุณาลองใหม่อีกครั้ง"


def generate_conversation_response(context_chain: str, user_message: str) -> str:
    """
    สร้างคำตอบจาก Context Chain (ใช้เมื่อต้องการให้ AI ตอบโดยพิจารณาบริบทการสนทนา)
    
    Args:
        context_chain: ประวัติการสนทนาที่ผ่านมา
        user_message: ข้อความล่าสุดจากผู้ใช้
    
    Returns:
        คำตอบจาก AI
    """
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
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


def get_gemini_response(user_message: str, prompt_prefix: str = "") -> str:
    """
    ฟังก์ชันทั่วไปสำหรับเรียก Gemini (backward compatible)
    
    Args:
        user_message: ข้อความจากผู้ใช้
        prompt_prefix: Prefix ที่จะเพิ่มหน้า prompt (ถ้ามี)
    
    Returns:
        คำตอบจาก Gemini
    """
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    full_prompt = f"{prompt_prefix}\n\nผู้ใช้: {user_message}\nผู้ช่วย:" if prompt_prefix else user_message
    
    try:
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        print(f"❌ Gemini error: {e}")
        return f"ขออภัยครับ เกิดข้อผิดพลาด: {str(e)}"