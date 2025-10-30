# intent_manager.py
"""
ระบบจัดการ Intent และ State Management
รองรับการวิเคราะห์ความตั้งใจและเก็บ Context แบบต่อเนื่อง
"""

from typing import Dict, List, Optional, Any
import json
from datetime import datetime
import google.generativeai as genai
import os

# Intent Types
INTENT_TYPES = {
    "GREETING": "ทักทาย",
    "ROUTE_REQUEST": "ขอเส้นทาง",
    "PLACE_SEARCH": "ค้นหาสถานที่",
    "REVIEW_REQUEST": "ขอรีวิว",
    "FILTER_REQUEST": "กรองข้อมูล",
    "NEXT_PLACE": "ถามว่าไปต่อไหนดี",
    "GENERAL_QUESTION": "ถามคำถามทั่วไป",
    "REFINE_REQUEST": "ปรับแก้เงื่อนไข",
    "UNKNOWN": "ไม่ทราบความตั้งใจ"
}

# Intent Classification Prompt
INTENT_CLASSIFICATION_PROMPT = """
คุณคือระบบวิเคราะห์ความตั้งใจ (Intent Classification) สำหรับแชทบอทท่องเที่ยวไทย

วิเคราะห์ข้อความของผู้ใช้และจำแนกเป็น intent ประเภทใดประเภทหนึ่ง พร้อมดึงข้อมูลสำคัญออกมา



**Intent Types:**
1. GREETING - ทักทาย (สวัสดี, หวัดดี, hi, hello, เริ่ม)
2. ROUTE_REQUEST - ขอเส้นทาง (จาก A ไป B, เส้นทาง)
3. PLACE_SEARCH - ค้นหาสถานที่ในจังหวัด (ที่เที่ยวในจังหวัดX, ที่ไปX)
4. REVIEW_REQUEST - ขอรีวิว (รีวิว X, X เป็นยังไง, รีวิว 1, รีวิว 2) หรือพิมชื่อสถานที่โดยตรง
5. FILTER_REQUEST - กรองด้วยเงื่อนไข (มีคาเฟ่ไหม, ที่มีธรรมชาติ, แบบมีร้านอาหาร, เลือก X) กรอก keywords หรือ categories
6. NEXT_PLACE - ถามว่าไปต่อไหนดี (ไปต่อไหนดี, แล้วต่อไป, แวะไหนต่อ) เอา Markdown ออก ให้เอาออกให้ได้
7. GENERAL_QUESTION - ถามคำถามทั่วไป (ฤดูไหนดี, ควรไปเมื่อไหร่, ถาม AI:) 
8. REFINE_REQUEST - ปรับแก้/เพิ่มเติมเงื่อนไข (เปลี่ยนเป็น, ไม่เอาแล้ว, เพิ่ม, ลด)

ตอบกลับเป็นข้อความปกติ **ไม่ใช้ Markdown เลย**:
- ไม่ต้องใช้ **ตัวหนา**
- ไม่ต้องใช้ *ตัวเอียง*
- ไม่ต้องใช้ list หรือ bullet
- ตอบเป็นข้อความธรรมดา

**ข้อมูลที่ต้องดึง (Entities):**
- origin: จุดเริ่มต้น (สำหรับเส้นทาง)
- destination: จุดหมายปลายทาง (สำหรับเส้นทาง)
- province: จังหวัด
- place_name: ชื่อสถานที่
- place_index: หมายเลขสถานที่ (ถ้าพิมพ์ "รีวิว 1" ให้ดึง "1" ออกมา)
- categories: หมวดหมู่ (ธรรมชาติ, คาเฟ่, ร้านอาหาร, วัด, ตลาด, จุดชมวิว, แหล่งเรียนรู้, ชุมชน/ตลาด)
- filters: เงื่อนไขเพิ่มเติม (ใกล้, ไกล, ราคาถูก, มีวิว)
- action: การกระทำ (เพิ่ม, ลบ, เปลี่ยน)

**Previous Context:**
{context_history}

**User Message:** 
{user_message}

**คำตอบในรูปแบบ JSON:**
{{
  "intent": "INTENT_TYPE",
  "confidence": 0.0-1.0,
  "entities": {{
    "origin": "...",
    "destination": "...",
    "province": "...",
    "place_name": "...",
    "place_index": "...",
    "categories": [...],
    "filters": [...],
    "action": "..."
  }},
  "refined_query": "ประโยคที่ปรับแล้ว",
  "requires_clarification": false,
  "clarification_question": "คำถามชี้แจงถ้าจำเป็น"
}}

**หมายเหตุสำคัญ:**
- ถ้าผู้ใช้พิมพ์ "รีวิว 1", "รีวิว 2" ให้ตีความเป็น REVIEW_REQUEST และดึง place_index = "1" หรือ "2"
- ถ้าพิมพ์ "เลือก คาเฟ่" ให้ตีความเป็น FILTER_REQUEST และดึง categories = ["คาเฟ่"]
- ถ้าพิมพ์ "เสร็จแล้ว" หรือ "ค้นหา" ให้ดูจาก context ว่าเป็น ROUTE_REQUEST หรือ PLACE_SEARCH

ตอบเฉพาะ JSON เท่านั้น ไม่ต้องมีคำอธิบายเพิ่มเติม
"""

class ConversationState:
    """เก็บ State ของการสนทนา"""
    
    def __init__(self):
        self.intent_history: List[Dict] = []
        self.entities: Dict[str, Any] = {
            "origin": None,
            "destination": None,
            "province": None,
            "place_name": None,
            "place_index": None,
            "categories": [],
            "filters": [],
            "current_place": None
        }
        self.last_results: List[Dict] = []
        self.conversation_context: str = ""
        self.mode: Optional[str] = None  # "route_with_stops" หรือ "province_search"
        self.waiting_for_category: bool = False
        self.created_at = datetime.now()
    
    def add_intent(self, intent_data: Dict):
        """เพิ่ม Intent ใหม่และ merge entities"""
        self.intent_history.append({
            "timestamp": datetime.now().isoformat(),
            "intent": intent_data["intent"],
            "entities": intent_data.get("entities", {}),
            "user_message": intent_data.get("user_message", "")
        })
        
        # Merge entities
        new_entities = intent_data.get("entities", {})
        for key, value in new_entities.items():
            if value:  # ถ้ามีค่า
                if key in ["categories", "filters"]:
                    # สำหรับ list ให้ merge
                    if isinstance(value, list):
                        self.entities[key] = list(set(self.entities[key] + value))
                else:
                    # สำหรับค่าเดี่ยวให้ replace
                    self.entities[key] = value
    
    def get_context_summary(self) -> str:
        """สร้างสรุป context สำหรับส่งให้ Gemini"""
        if not self.intent_history:
            return "ไม่มีประวัติการสนทนา"
        
        summary = "ประวัติการสนทนา:\n"
        for idx, intent in enumerate(self.intent_history[-5:], 1):  # เอาแค่ 5 รอบล่าสุด
            summary += f"{idx}. Intent: {intent['intent']}\n"
            summary += f"   User: {intent['user_message']}\n"
            summary += f"   Entities: {json.dumps(intent['entities'], ensure_ascii=False)}\n"
        
        summary += f"\nCurrent Entities: {json.dumps(self.entities, ensure_ascii=False)}"
        summary += f"\nCurrent Mode: {self.mode}"
        return summary
    
    def clear_filters(self):
        """ล้างเงื่อนไขการกรอง"""
        self.entities["categories"] = []
        self.entities["filters"] = []
    
    def reset(self):
        """Reset state ทั้งหมด"""
        self.__init__()


class IntentManager:
    """จัดการ Intent Classification และ State"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.user_states: Dict[str, ConversationState] = {}
    
    def get_state(self, user_id: str) -> ConversationState:
        """ดึง state ของ user"""
        if user_id not in self.user_states:
            self.user_states[user_id] = ConversationState()
        return self.user_states[user_id]
    
    def classify_intent(self, user_id: str, user_message: str) -> Dict:
        """วิเคราะห์ Intent จากข้อความผู้ใช้"""
        state = self.get_state(user_id)
        context = state.get_context_summary()
        
        prompt = INTENT_CLASSIFICATION_PROMPT.format(
            context_history=context,
            user_message=user_message
        )
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # ลบ markdown code block ถ้ามี
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            
            intent_data = json.loads(result_text.strip())
            intent_data["user_message"] = user_message
            
            # บันทึก intent ลง state
            state.add_intent(intent_data)
            
            return intent_data
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse Error: {e}")
            print(f"Raw response: {response.text}")
            return {
                "intent": "UNKNOWN",
                "confidence": 0.0,
                "entities": {},
                "refined_query": user_message,
                "requires_clarification": True,
                "clarification_question": "ขอโทษครับ ผมไม่เข้าใจคำถามคุณ ช่วยอธิบายเพิ่มเติมได้ไหมครับ?"
            }
        except Exception as e:
            print(f"❌ Intent Classification Error: {e}")
            return {
                "intent": "UNKNOWN",
                "confidence": 0.0,
                "entities": {},
                "refined_query": user_message,
                "requires_clarification": False
            }
    
    def handle_refine_request(self, user_id: str, intent_data: Dict) -> Dict:
        """จัดการคำขอปรับแก้เงื่อนไข"""
        state = self.get_state(user_id)
        action = intent_data.get("entities", {}).get("action", "")
        
        if action == "เพิ่ม":
            # เพิ่ม categories/filters
            new_categories = intent_data.get("entities", {}).get("categories", [])
            state.entities["categories"].extend(new_categories)
            state.entities["categories"] = list(set(state.entities["categories"]))
            
        elif action == "ลบ":
            # ลบ categories/filters
            remove_categories = intent_data.get("entities", {}).get("categories", [])
            for cat in remove_categories:
                if cat in state.entities["categories"]:
                    state.entities["categories"].remove(cat)
        
        elif action == "เปลี่ยน":
            # เปลี่ยน entities
            state.entities.update(intent_data.get("entities", {}))
        
# สร้างข้อความสรุปการเปลี่ยนแปลงให้อ่านง่าย
        entities = state.entities
        changes = []

        if "province" in entities:
            changes.append(f"จังหวัด: {entities['province']}")

        if "categories" in entities and entities["categories"]:
            cat_list = " ,".join(entities["categories"])
            changes.append(f"หมวดหมู่: {cat_list}")

        if not changes:
            msg = "ยังไม่มีการเปลี่ยนแปลงครับ"
        else:
            msg = "ปรับเงื่อนไขแล้วครับ 🎯\n" + "\n".join(f"• {c}" for c in changes)

        return {
            "status": "refined",
            "current_entities": entities,
            "message": msg
        }
    
    def reset_user_state(self, user_id: str):
        """Reset state ของ user"""
        if user_id in self.user_states:
            self.user_states[user_id].reset()
    
    def get_chain_context(self, user_id: str) -> str:
        """ดึง context chain สำหรับการตอบคำถาม"""
        state = self.get_state(user_id)
        
        if not state.intent_history:
            return "ไม่มี context ก่อนหน้า"
        
        chain = "🔗 Context Chain:\n"
        for idx, intent in enumerate(state.intent_history, 1):
            chain += f"Step {idx}: {intent['intent']} - {intent['user_message']}\n"
        
        chain += f"\n📊 Current State:\n{json.dumps(state.entities, ensure_ascii=False, indent=2)}"
        return chain