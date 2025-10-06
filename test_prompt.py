import os
from dotenv import load_dotenv
import google.generativeai as genai
from prompt import *

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def test_prompt(prompt_name, prompt_template, variables):
    """ทดสอบ prompt แต่ละตัว"""
    print(f"\n{'='*60}")
    print(f"🧪 Testing: {prompt_name}")
    print(f"{'='*60}")
    
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    # Format prompt
    prompt = prompt_template.format(**variables)
    
    print(f"\n📝 Prompt Preview:")
    print(prompt[:200] + "..." if len(prompt) > 200 else prompt)
    
    # Generate response
    response = model.generate_content(prompt)
    
    print(f"\n🤖 AI Response:")
    print(response.text)
    print(f"\n📊 Response Length: {len(response.text)} characters")
    print(f"{'='*60}")


if __name__ == "__main__":
    # Test 1: Review Summary
    test_prompt(
        "PROMPT_REVIEW_SUMMARY",
        PROMPT_REVIEW_SUMMARY,
        {
            "place_name": "วัดพระธาตุดอยสุเทพ",
            "rating": 4.7,
            "categories": "วัด, จุดชมวิว",
            "reviews": "- วิวสวยมาก\n- ต้องเดินขึ้นบันไดเยอะ\n- ศักดิ์สิทธิ์"
        }
    )
    
    # Test 2: Next Destination
    test_prompt(
        "PROMPT_NEXT_DESTINATION",
        PROMPT_NEXT_DESTINATION,
        {
            "place": "วัดพระธาตุดอยสุเทพ",
            "province": "เชียงใหม่",
            "categories": "วัด, ธรรมชาติ"
        }
    )
    
    # Test 3: General Question
    test_prompt(
        "PROMPT_GENERAL_QUESTION",
        PROMPT_GENERAL_QUESTION,
        {
            "question": "ช่วงไหนเที่ยวทะเลดีที่สุด"
        }
    )