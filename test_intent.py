# test_intent.py

import os
import json
from dotenv import load_dotenv
from intent_manager import IntentManager

load_dotenv()

def test_conversation():
    """ทดสอบการสนทนาแบบต่อเนื่อง"""
    
    # Initialize Intent Manager
    manager = IntentManager(api_key=os.getenv("GEMINI_API_KEY"))
    
    test_user_id = "test_user_001"
    
    # ชุดทดสอบ Scenario 1: ค้นหาสถานที่ + เพิ่มเงื่อนไข
    print("="*80)
    print("📋 Scenario 1: ค้นหาสถานที่ใน จังหวัด + เพิ่มเงื่อนไข")
    print("="*80)
    
    messages_scenario1 = [
        "ที่เที่ยวในเชียงใหม่",
        "มีคาเฟ่ไหม",
        "เพิ่มที่มีวิวภูเขาด้วย",
        "ค้นหา"
    ]
    
    for msg in messages_scenario1:
        print(f"\n👤 User: {msg}")
        intent_result = manager.classify_intent(test_user_id, msg)
        
        print(f"🎯 Intent: {intent_result['intent']} (Confidence: {intent_result['confidence']:.2f})")
        print(f"📦 Entities: {json.dumps(intent_result['entities'], ensure_ascii=False)}")
        
        state = manager.get_state(test_user_id)
        print(f"📊 Current State: {json.dumps(state.entities, ensure_ascii=False)}")
        print("-" * 80)
    
    # Reset state
    manager.reset_user_state(test_user_id)
    
    # Scenario 2: เส้นทาง + รีวิว
    print("\n\n" + "="*80)
    print("📋 Scenario 2: เส้นทาง + รีวิว + แนะนำสถานที่ต่อไป")
    print("="*80)
    
    messages_scenario2 = [
        "กรุงเทพ ไป เชียงใหม่",
        "เลือก ร้านอาหาร",
        "เสร็จแล้ว",
        "รีวิว 1",
        "ไปต่อไหนดี"
    ]
    
    for msg in messages_scenario2:
        print(f"\n👤 User: {msg}")
        intent_result = manager.classify_intent(test_user_id, msg)
        
        print(f"🎯 Intent: {intent_result['intent']} (Confidence: {intent_result['confidence']:.2f})")
        print(f"📦 Entities: {json.dumps(intent_result['entities'], ensure_ascii=False)}")
        
        state = manager.get_state(test_user_id)
        print(f"📊 Current State: {json.dumps(state.entities, ensure_ascii=False)}")
        print("-" * 80)
    
    # Reset state
    manager.reset_user_state(test_user_id)
    
    # Scenario 3: ปรับแก้เงื่อนไข
    print("\n\n" + "="*80)
    print("📋 Scenario 3: ปรับแก้เงื่อนไขระหว่างทาง")
    print("="*80)
    
    messages_scenario3 = [
        "ที่เที่ยวในภูเก็ต",
        "เลือก ธรรมชาติ",
        "ไม่เอาธรรมชาติแล้ว เปลี่ยนเป็นตลาด",
        "เพิ่มร้านอาหารทะเลด้วย"
    ]
    
    for msg in messages_scenario3:
        print(f"\n👤 User: {msg}")
        intent_result = manager.classify_intent(test_user_id, msg)
        
        print(f"🎯 Intent: {intent_result['intent']} (Confidence: {intent_result['confidence']:.2f})")
        print(f"📦 Entities: {json.dumps(intent_result['entities'], ensure_ascii=False)}")
        
        state = manager.get_state(test_user_id)
        print(f"📊 Current State: {json.dumps(state.entities, ensure_ascii=False)}")
        print("-" * 80)
    
    print("\n\n" + "="*80)
    print("✅ ทดสอบเสร็จสิ้น!")
    print("="*80)


def test_single_intent(message: str):
    """ทดสอบ Intent เดี่ยว"""
    manager = IntentManager(api_key=os.getenv("GEMINI_API_KEY"))
    
    print(f"\n👤 User: {message}")
    result = manager.classify_intent("test_single", message)
    
    print(f"🎯 Intent: {result['intent']}")
    print(f"📈 Confidence: {result['confidence']:.2f}")
    print(f"📦 Entities: {json.dumps(result['entities'], ensure_ascii=False, indent=2)}")
    print(f"🔄 Refined Query: {result['refined_query']}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # ถ้ามี argument ให้ทดสอบข้อความนั้น
        test_message = " ".join(sys.argv[1:])
        test_single_intent(test_message)
    else:
        # ไม่มี argument ให้รัน scenario ทั้งหมด
        test_conversation()