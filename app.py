"""
LINE Bot + Web Chat with Intent Classification System
รองรับการสนทนาแบบต่อเนื่องด้วย State Management
"""

from linebot.v3.messaging import (
    MessagingApi, ReplyMessageRequest, TextMessage,
    QuickReply, QuickReplyItem, MessageAction
)
from linebot.v3.messaging.configuration import Configuration
from linebot.v3.messaging.api_client import ApiClient
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.exceptions import InvalidSignatureError
from utils.maps_utils import directions
from services.route_service import route_suggestions

import os
import json
import random
from flask import Flask, render_template, request, abort, jsonify, session
from flask_session import Session
from dotenv import load_dotenv
import requests
from flask import send_file
from io import BytesIO
import os

# Import Intent Manager
from intent_manager import IntentManager, INTENT_TYPES

# Import existing services
from services.route_service import route_suggestions
from services.province_service import search_by_province  
from services.gemini_service import (
    summarize_place_reviews, 
    generate_place_summary,
    ask_gemini_general,
    ask_next_place_suggestion,
    get_gemini_response
)

# Import utilities
from utils.common import validate_province_in_thailand

# Import routes
from routes.api import api_bp

# Import config
from config import SECRET_KEY, SESSION_TYPE

load_dotenv()

# ============================================
# Flask App Configuration
# ============================================
app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config["SESSION_TYPE"] = SESSION_TYPE
Session(app)

# ============================================
# LINE Bot Configuration
# ============================================
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY") or os.getenv("GOOGLE_API_KEY")

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
api_client = ApiClient(configuration)         
messaging_api = MessagingApi(api_client)       
handler = WebhookHandler(CHANNEL_SECRET)

# ============================================
# Initialize Intent Manager
# ============================================
intent_manager = IntentManager(api_key=GEMINI_API_KEY)

# ============================================
# Constants
# ============================================
MAX_PLACES = 5

CATEGORIES = {
    "ธรรมชาติ": {"emoji": "🏞️", "description": "national park waterfall mountain beach forest nature อุทยาน น้ำตก ภูเขา ป่า ชายหาด สวนสัตว์"},
    "วัด": {"emoji": "🛕", "description": "temple wat mosque church วัด โบสถ์ มัสยิด ศาลเจ้า"},
    "คาเฟ่": {"emoji": "☕", "description": "cafecoffee bakery คาเฟ่ กาแฟ เบเกอรี่"},
    "ร้านอาหาร": {"emoji": "🍽️", "description": "restaurant food ร้านอาหาร อาหาร โรงแรม"},
    "แหล่งเรียนรู้": {"emoji": "📚", "description": "พิพิธภัณฑ์ หอศิลป์"},
    "จุดชมวิว": {"emoji": "🌅", "description": "จุดชมวิว ทิวทัศน์"},
    "ชุมชน/ตลาด": {"emoji": "🏪", "description": "ตลาด ชุมชน ห้าง"}
}

GREETINGS = [
    "สวัสดีครับ!",
    "หวัดดีครับ!",  
    "ยินดีต้อนรับครับ!"
]

# Register blueprints
app.register_blueprint(api_bp, url_prefix="/api")

# ============================================
# Helper Functions - Quick Reply
# ============================================
def create_category_quick_reply():
    """สร้าง Quick Reply สำหรับเลือกหมวดหมู่"""
    quick_reply_items = []
    
    for category, info in CATEGORIES.items():
        quick_reply_items.append(
            QuickReplyItem(
                action=MessageAction(
                    label=f"{info['emoji']} {category}",
                    text=f"เลือก {category}"
                )
            )
        )
    
    quick_reply_items.extend([
        QuickReplyItem(
            action=MessageAction(
                label="🎯 ทั้งหมด",
                text="เลือก ทั้งหมด"
            )
        ),
        QuickReplyItem(
            action=MessageAction(
                label="✅ เสร็จแล้ว",
                text="เสร็จแล้ว"
            )
        )
    ])
    
    return QuickReply(items=quick_reply_items)


def create_review_quick_reply():
    """สร้าง Quick Reply หลังแสดงผลลัพธ์"""
    items = [
        QuickReplyItem(
            action=MessageAction(
                label="🔄 ค้นหาใหม่",
                text="เริ่ม"
            )
        )
    ]
    return QuickReply(items=items)


def extract_quick_replies(quick_reply_obj):
    """แปลง Quick Reply object เป็น list ของข้อความ"""
    if not quick_reply_obj:
        return []
    
    try:
        if hasattr(quick_reply_obj, 'items'):
            return [item.action.text for item in quick_reply_obj.items if hasattr(item.action, 'text')]
        return []
    except Exception as e:
        print(f"Warning: Cannot extract quick replies: {e}")
        return []


# ============================================
# Helper Functions - Response Formatting
# ============================================
# ============================================
# Helper Functions - Response Formatting (UPDATED)
# ============================================

def format_route_response(origin, destination, route_info, stops, categories):
    """จัดรูปแบบ response สำหรับเส้นทาง"""
    distance = route_info.get("distance_text", "?")
    duration = route_info.get("duration_text", "?")
    
    origin_display = route_info.get("origin", origin)
    destination_display = route_info.get("destination", destination)
    
    response = f"🛣️ เส้นทาง {origin_display} ➜ {destination_display}\n\n"
    response += f"📏 ระยะทาง: {distance}\n"
    response += f"⏰ เวลา: {duration}\n"
    
    if categories:
        response += f"🏷️ หมวด: {', '.join(categories)}\n\n"
    else:
        response += "\n"
    
    if stops:
        displayed = stops[:MAX_PLACES]
        response += f"📍 สถานที่แนะนำ ({len(displayed)} แห่ง):\n\n"
        
        for i, stop in enumerate(displayed, 1):
            name = stop.get("name", "?")
            rating = stop.get("rating", "-")
            reviews_count = stop.get("user_ratings_total", 0)
            address = stop.get("address", "")
            detour = stop.get("detour_minutes_est")
            
            # ชื่อและเรตติ้ง
            rating_text = f"⭐ {rating}" if rating else "⭐ -"
            response += f"{i}. {name}\n"
            response += f"   {rating_text} ({reviews_count} รีวิว)\n"
            
            # ที่อยู่
            if address:
                short_address = address[:60] + "..." if len(address) > 60 else address
                response += f"   📍 {short_address}\n"
            
            # เวลาเลี่ยงทาง
            if detour:
                response += f"   🕐 เลี่ยงทางหลัก +{detour} นาที\n"
            
            # หมวดหมู่
            stop_categories = stop.get("categories", [])
            if stop_categories:
                cat_emojis = [f"{CATEGORIES[cat]['emoji']}" for cat in stop_categories[:2] if cat in CATEGORIES]
                if cat_emojis:
                    response += f"   {' '.join(cat_emojis)} {', '.join(stop_categories[:2])}\n"
            
            # อากาศ
            weather = stop.get("weather", {})
            if weather and weather.get("temp_c"):
                temp = weather.get("temp_c")
                condition = weather.get("condition", "")
                response += f"   🌡️ {temp}°C {condition}\n"
            
            response += "\n"
        
        response += "💡 คลิกที่การ์ดด้านล่างเพื่อดูรูปภาพและรายละเอียดเพิ่มเติม\n"
        response += "📱 กดปุ่ม 'แผนที่' เพื่อเปิดใน Google Maps\n"
        response += "💬 พิมพ์ 'รีวิว [ชื่อสถานที่]' เพื่อออ่านรีวิว AI"
    else:
        response += "ไม่มีสถานที่แวะตามหมวดหมู่ที่เลือก"
    
    return response


def format_place_response(province, items, categories):
    """จัดรูปแบบ response สำหรับสถานที่ในจังหวัด"""
    response = f"🏞️ สถานที่ใน {province}"
    
    if categories:
        response += f" ({', '.join(categories)})"
    response += ":\n\n"
    
    displayed = items[:MAX_PLACES]
    
    for i, item in enumerate(displayed, 1):
        name = item.get("name", "?")
        rating = item.get("rating", "-")
        reviews_count = item.get("user_ratings_total", 0)
        address = item.get("address", "")
        
        # ชื่อและเรตติ้ง
        rating_text = f"⭐ {rating}" if rating else "⭐ -"
        response += f"{i}. {name}\n"
        response += f"   {rating_text} ({reviews_count} รีวิว)\n"
        
        # ที่อยู่
        if address:
            short_address = address[:60] + "..." if len(address) > 60 else address
            response += f"   📍 {short_address}\n"
        
        # หมวดหมู่
        item_categories = item.get("categories", [])
        if item_categories:
            cat_emojis = [f"{CATEGORIES[cat]['emoji']}" for cat in item_categories[:2] if cat in CATEGORIES]
            if cat_emojis:
                response += f"   {' '.join(cat_emojis)} {', '.join(item_categories[:2])}\n"
        
        # อากาศ
        weather = item.get("weather", {})
        if weather and weather.get("temp_c"):
            temp = weather.get("temp_c")
            condition = weather.get("condition", "")
            response += f"   🌡️ {temp}°C {condition}\n"
        
        response += "\n"
    
    response += "💡 คลิกที่การ์ดด้านล่างเพื่อดูรูปภาพและรายละเอียดเพิ่มเติม\n"
    response += "📱 กดปุ่ม 'แผนที่' เพื่อเปิดใน Google Maps\n"
    response += "💬 พิมพ์ 'รีวิว [ชื่อสถานที่]' เพื่ออ่านรีวิว AI"
    
    return response


# ============================================
# Intent Handlers
# ============================================

def handle_greeting_intent(user_id: str, intent_data: dict) -> tuple:
    """จัดการ Intent: GREETING"""
    intent_manager.reset_user_state(user_id)
    
    reply_text = (
        f"{random.choice(GREETINGS)}\n"
        "ผมเป็นผู้ช่วยท่องเที่ยวอัจฉริยะครับ!\n\n"
        "💡 ลองพิมพ์:\n"
        "• 'ที่เที่ยวในเชียงใหม่'\n"
        "• 'กรุงเทพ ไป เชียงใหม่'\n"
        "• 'มีคาเฟ่ไหม'\n"
        "• 'ไปต่อไหนดี'"
    )
    return reply_text, None


def handle_route_request_intent(user_id: str, intent_data: dict) -> tuple:
    """จัดการ Intent: ROUTE_REQUEST"""
    state = intent_manager.get_state(user_id)
    entities = state.entities

    origin = entities.get("origin")
    destination = entities.get("destination")
    categories = entities.get("categories", [])
    
    # ถ้าไม่มีจุดเริ่มหรือจุดหมาย
    if not origin or not destination:
        reply_text = (
            "กรุณาระบุจุดเริ่มต้นและจุดหมายครับ\n"
            "เช่น: 'กรุงเทพ ไป เชียงใหม่'"
        )
        return reply_text, None
    print(f"🐞 Debug categories before route: {categories}")
    # ✅ ถ้ายังไม่มีหมวดหมู่ ให้ถามก่อน (ไม่คำนวณ route)
    if not categories:
        state.mode = "route_with_stops"
        state.waiting_for_category = True
        reply_text = (
            f"📍 เส้นทาง: {origin} ➜ {destination}\n\n"
            "เลือกหมวดหมู่สถานที่ที่ต้องการแวะ:"
        )
        return reply_text, create_category_quick_reply()

    # ✅ ถ้ามีหมวดหมู่แล้วค่อยคำนวณเส้นทาง
    result = route_suggestions(origin, destination, categories_th=categories)
    if "error" in result:
        return f"ขอโทษครับ: {result['error']}", None

    route_info = result.get("route", {})
    stops = result.get("stops", [])

    response = format_route_response(origin, destination, route_info, stops, categories)

    state.last_results = stops[:MAX_PLACES]
    state.mode = None
    state.waiting_for_category = False

    # ✅ เก็บข้อมูลเส้นทางไว้ใน state
    state.entities["last_route_data"] = {
        "route": route_info,
        "stops": stops[:5]
    }

    return response, create_review_quick_reply()



def handle_place_search_intent(user_id: str, intent_data: dict) -> tuple:
    """จัดการ Intent: PLACE_SEARCH"""
    state = intent_manager.get_state(user_id)
    entities = state.entities

    province = entities.get("province")
    categories = entities.get("categories", [])

    # ถ้าไม่มีจังหวัด
    if not province:
        return "กรุณาระบุจังหวัดครับ เช่น: 'ที่เที่ยวในเชียงใหม่'", None

    # ✅ ถ้ายังไม่มีหมวดหมู่ ให้ถามก่อน
    if not categories:
        state.mode = "province_search"
        state.waiting_for_category = True
        reply_text = f"🏞️ จังหวัด: {province}\n\nเลือกหมวดหมู่สถานที่:"
        return reply_text, create_category_quick_reply()

    # ✅ ถ้ามีหมวดหมู่แล้วค่อยค้นหา
    result = search_by_province(province, categories_th=categories, limit=10)
    if "error" in result:
        return f"ขอโทษครับ หาข้อมูล {province} ไม่เจอเลย", None

    items = result.get("items", [])
    if not items:
        return f"ไม่เจอสถานที่ใน {province} ตามหมวดหมู่ที่เลือกครับ", None

    response = format_place_response(province, items, categories)

    state.last_results = items[:MAX_PLACES]
    state.mode = None
    state.waiting_for_category = False

    return response, create_review_quick_reply()



def handle_filter_request_intent(user_id: str, intent_data: dict) -> tuple:
    """จัดการ Intent: FILTER_REQUEST"""
    state = intent_manager.get_state(user_id)
    entities = state.entities
    
    new_categories = intent_data.get("entities", {}).get("categories", [])
    
    if new_categories:
        current_cats = entities.get("categories", [])
        
        if "ทั้งหมด" in new_categories:
            updated_cats = list(CATEGORIES.keys())
        else:
            updated_cats = list(set(current_cats + new_categories))
        
        entities["categories"] = updated_cats
        
        selected_text = "ทั้งหมด" if len(updated_cats) == len(CATEGORIES) else ", ".join(updated_cats)
        
        reply_text = (
            f"✅ เลือกแล้ว: {selected_text}\n\n"
            "เลือกเพิ่มหรือกด 'เสร็จแล้ว' เพื่อค้นหา"
        )
        return reply_text, create_category_quick_reply()
    
    return "เลือกหมวดหมู่ที่ต้องการ:", create_category_quick_reply()


def handle_refine_request_intent(user_id: str, intent_data: dict) -> tuple:
    """จัดการ Intent: REFINE_REQUEST"""
    result = intent_manager.handle_refine_request(user_id, intent_data)
    
    reply_text = (
        f"✅ {result['message']}\n\n"
        "พิมพ์ 'ค้นหา' เพื่อดูผลลัพธ์ใหม่"
    )
    return reply_text, None


def handle_review_request_intent(user_id: str, intent_data: dict) -> tuple:
    """จัดการ Intent: REVIEW_REQUEST"""
    state = intent_manager.get_state(user_id)
    entities = intent_data.get("entities", {})
    
    place_name = entities.get("place_name", "")
    place_index = entities.get("place_index")
    last_results = state.last_results
    
    if not last_results:
        return "ยังไม่มีผลการค้นหาครับ กรุณาค้นหาสถานที่ก่อน", None
    
    found_place = None
    
    if place_index:
        try:
            idx = int(place_index) - 1
            if 0 <= idx < len(last_results):
                found_place = last_results[idx]
        except ValueError:
            pass
    
    if not found_place and place_name:
        for place in last_results:
            if place_name.lower() in place.get("name", "").lower():
                found_place = place
                break
    
    if not found_place:
        return f"ไม่พบสถานที่ '{place_name or place_index}' ในผลการค้นหาครับ", None
    
    reviews = found_place.get("reviews", [])
    rating = found_place.get("rating")
    categories = found_place.get("categories", [])
    
    ai_review = summarize_place_reviews(
        place_name=found_place.get("name"),
        reviews=reviews,
        rating=rating,
        categories=categories
    )
    
    response = (
        f"📝 รีวิว: {found_place.get('name')}\n"
        f"⭐ คะแนน: {rating if rating else 'ไม่มีข้อมูล'}\n"
    )
    
    if categories:
        response += f"🏷️ ประเภท: {', '.join(categories[:3])}\n"
    
    response += f"\n🤖 สรุปจาก AI:\n{ai_review}\n\n"
    response += "💡 ถามต่อ: 'ไปต่อไหนดี' หรือ 'รีวิวที่อื่น'"
    
    state.entities["current_place"] = found_place.get("name")
    
    return response, create_review_quick_reply()


def handle_next_place_intent(user_id: str, intent_data: dict) -> tuple:
    """จัดการ Intent: NEXT_PLACE"""
    state = intent_manager.get_state(user_id)
    entities = state.entities
    
    current_place = entities.get("current_place")
    province = entities.get("province")
    
    if not current_place and state.last_results:
        try:
            current_place = state.last_results[0].get("name")
        except:
            pass
    
    if not current_place and not province:
        return "ยังไม่มีข้อมูลสถานที่เริ่มต้นครับ กรุณาค้นหาหรือขอรีวิวสถานที่ก่อน", None
    
    suggestion = ask_next_place_suggestion(
        current_place=current_place,
        province=province,
        categories=entities.get("categories", [])
    )
    
    return suggestion, None


def handle_general_question_intent(user_id: str, intent_data: dict) -> tuple:
    """จัดการ Intent: GENERAL_QUESTION"""
    user_message = intent_data.get("user_message", "")
    
    if user_message.lower().startswith("ถาม ai:"):
        user_message = user_message[len("ถาม AI:"):].strip()
    
    answer = ask_gemini_general(user_message)
    
    return answer, None


def handle_unknown_intent(user_id: str, intent_data: dict) -> tuple:
    """จัดการ Intent: UNKNOWN"""
    if intent_data.get("requires_clarification"):
        reply_text = intent_data.get("clarification_question", "ไม่เข้าใจคำถามครับ")
    else:
        reply_text = (
            "ขอโทษครับ ผมไม่เข้าใจคำถาม\n\n"
            "💡 ลองพิมพ์:\n"
            "• 'ที่เที่ยวในเชียงใหม่'\n"
            "• 'กรุงเทพ ไป เชียงใหม่'\n"
            "• 'รีวิว [ชื่อสถานที่]'\n"
            "• 'ไปต่อไหนดี'"
        )
    
    return reply_text, None


def remove_markdown(text):
    import re
    if not text:
        return ""
    text = re.sub(r'(\*\*|__)(.*?)\1', r'\2', text)
    text = re.sub(r'(\*|_)(.*?)\1', r'\2', text)
    text = re.sub(r'`(.*?)`', r'\1', text)
    text = re.sub(r'^#+\s*(.*)', r'\1', text, flags=re.MULTILINE)  # ✅ เพิ่ม text
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    return text
# ============================================
# Flask Routes
# ============================================

@app.route("/")
def home():
    return render_template("index.html")
@app.route("/api/place_photo")
def place_photo():
    """ดึงภาพสถานที่จาก Google Places API"""
    place_id = request.args.get("place_id")
    if not place_id:
        return jsonify({"error": "missing place_id"}), 400

    # ขอ photo_reference ก่อน
    details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=photo&key={GOOGLE_API_KEY}"
    details = requests.get(details_url).json()
    photos = details.get("result", {}).get("photos", [])

    if not photos:
        return jsonify({"error": "no photos found"}), 404

    ref = photos[0]["photo_reference"]
    photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photo_reference={ref}&key={GOOGLE_API_KEY}"
    img = requests.get(photo_url)

    return send_file(BytesIO(img.content), mimetype="image/jpeg")

def api_route_with_stops():
    """
    API สำหรับคำนวณเส้นทาง + สถานที่แนะนำ 5 แห่ง (พร้อม polyline)
    หลังผู้ใช้เลือกหมวดหมู่เสร็จแล้ว
    """
    try:
        data = request.get_json()
        origin = data.get("origin")
        destination = data.get("destination")
        categories = data.get("categories", [])

        if not origin or not destination:
            return jsonify({"error": "กรุณาระบุ origin และ destination"}), 400

        result = route_suggestions(origin, destination, categories_th=categories)

        if "error" in result:
            return jsonify(result), 400

        # เอาเฉพาะ 5 จุดแรกพอ
        stops = result.get("stops", [])[:5]
        route = result.get("route", {})

        return jsonify({
            "route": route,
            "stops": stops
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ============================================
# Web Chat API with Intent System
# ============================================

@app.route("/api/web_chat", methods=["POST"])
def web_chat():
    """API สำหรับเว็บแชทที่ใช้ Intent System"""
    try:
        data = request.get_json()
        user_id = data.get("user_id", "web_user_default")
        message = data.get("message", "").strip()
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        print(f"\n{'='*60}")
        print(f"🌐 Web Chat User ({user_id}): {message}")
        
        # Classify Intent
        intent_data = intent_manager.classify_intent(user_id, message)
        intent = intent_data.get("intent")
        confidence = intent_data.get("confidence", 0.0)
        state = intent_manager.get_state(user_id)
        
        print(f"🎯 Intent: {intent} (Confidence: {confidence:.2f})")
        print(f"📦 Entities: {json.dumps(intent_data.get('entities', {}), ensure_ascii=False)}")
        
        reply_text = ""
        quick_replies = []
        results = None
        
        # Route to Handler
        try:
            if intent == "GREETING":
                reply_text, qr = handle_greeting_intent(user_id, intent_data)
                quick_replies = extract_quick_replies(qr) if qr else []
            
            elif intent == "ROUTE_REQUEST":
                reply_text, qr = handle_route_request_intent(user_id, intent_data)
                quick_replies = extract_quick_replies(qr) if qr else []
                results = state.last_results
            
            elif intent == "PLACE_SEARCH":
                reply_text, qr = handle_place_search_intent(user_id, intent_data)
                quick_replies = extract_quick_replies(qr) if qr else []
                results = state.last_results
            
            elif intent == "FILTER_REQUEST":
                reply_text, qr = handle_filter_request_intent(user_id, intent_data)
                quick_replies = extract_quick_replies(qr) if qr else []
            
            elif intent == "REFINE_REQUEST":
                reply_text, qr = handle_refine_request_intent(user_id, intent_data)
                quick_replies = extract_quick_replies(qr) if qr else []
            
            elif intent == "REVIEW_REQUEST":
                reply_text, qr = handle_review_request_intent(user_id, intent_data)
                quick_replies = extract_quick_replies(qr) if qr else []
            
            elif intent == "NEXT_PLACE":
                reply_text, qr = handle_next_place_intent(user_id, intent_data)
                quick_replies = extract_quick_replies(qr) if qr else []
            
            elif intent == "GENERAL_QUESTION":
                reply_text, qr = handle_general_question_intent(user_id, intent_data)
                quick_replies = extract_quick_replies(qr) if qr else []
            
            elif intent == "UNKNOWN":
                reply_text, qr = handle_unknown_intent(user_id, intent_data)
                quick_replies = extract_quick_replies(qr) if qr else []
            
            else:
                reply_text = f"กำลังพัฒนาฟีเจอร์สำหรับ Intent '{intent}'"
        
        except Exception as e:
            print(f"❌ Handler Error: {e}")
            import traceback
            traceback.print_exc()
            reply_text = f"เกิดข้อผิดพลาด: {str(e)}"
        
        if not reply_text:
            reply_text = "ไม่สามารถตอบได้ในขณะนี้"
        
        # ✅ ลบ Markdown สำหรับทุก reply
        reply_text = remove_markdown(reply_text)
        
        print(f"🤖 Bot Reply: {reply_text[:100]}...")
        print(f"{'='*60}\n")
        
        response_data = {
            "text": reply_text,
            "intent": intent,
            "confidence": confidence,
            "quickReplies": quick_replies,
            "results": results[:5] if results else None,
            "state": {
                "entities": state.entities,
                "mode": state.mode,
                "waiting_for_category": state.waiting_for_category
            }
        }
        if "last_route_data" in state.entities:
            response_data["routeData"] = state.entities["last_route_data"]
        
        return jsonify(response_data)
    
    except Exception as e:
        print(f"❌ Web Chat Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/gemini_chat", methods=["POST"])
def gemini_chat():
    """API endpoint สำหรับ frontend chat (legacy)"""
    try:
        data = request.get_json()
        user_message = data.get("message", "")

        if not user_message:
            return jsonify({"reply": "⚠️ ไม่พบข้อความจากผู้ใช้"}), 400

        reply = get_gemini_response(user_message)
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": f"❌ เกิดข้อผิดพลาด: {str(e)}"}), 500


@app.route("/api/test_intent", methods=["POST"])
def test_intent():
    """API สำหรับทดสอบ Intent Classification"""
    data = request.get_json()
    user_id = data.get("user_id", "test_user")
    message = data.get("message", "")
    
    if not message:
        return jsonify({"error": "message is required"}), 400
    
    intent_data = intent_manager.classify_intent(user_id, message)
    state = intent_manager.get_state(user_id)
    
    return jsonify({
        "intent": intent_data,
        "current_state": {
            "entities": state.entities,
            "intent_history": state.intent_history[-5:],
            "context_summary": state.get_context_summary()
        }
    })


@app.route("/api/reset_state/<user_id>", methods=["POST"])
def reset_state(user_id):
    """API สำหรับ Reset State ของ User"""
    intent_manager.reset_user_state(user_id)
    return jsonify({"status": "reset", "user_id": user_id})


# ============================================
# LINE Webhook
# ============================================

@app.route("/webhook", methods=["POST"])
def webhook():
    """LINE Webhook Endpoint"""
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """Main Message Handler พร้อม Intent Classification"""
    user_id = event.source.user_id
    user_text = event.message.text.strip()
    
    print(f"\n{'='*60}")
    print(f"👤 User ({user_id}): {user_text}")
    
    # Step 1: Classify Intent
    intent_data = intent_manager.classify_intent(user_id, user_text)
    
    intent = intent_data.get("intent")
    confidence = intent_data.get("confidence", 0.0)
    
    print(f"🎯 Intent: {intent} (Confidence: {confidence:.2f})")
    print(f"📦 Entities: {json.dumps(intent_data.get('entities', {}), ensure_ascii=False)}")
    
    reply_text = ""
    quick_reply = None
    
    # Step 2: Route to Handler
    try:
        if intent == "GREETING":
            reply_text, quick_reply = handle_greeting_intent(user_id, intent_data)
        
        elif intent == "ROUTE_REQUEST":
            reply_text, quick_reply = handle_route_request_intent(user_id, intent_data)
        
        elif intent == "PLACE_SEARCH":
            reply_text, quick_reply = handle_place_search_intent(user_id, intent_data)
        
        elif intent == "FILTER_REQUEST":
            reply_text, quick_reply = handle_filter_request_intent(user_id, intent_data)
        
        elif intent == "REFINE_REQUEST":
            reply_text, quick_reply = handle_refine_request_intent(user_id, intent_data)
        
        elif intent == "REVIEW_REQUEST":
            reply_text, quick_reply = handle_review_request_intent(user_id, intent_data)
        
        elif intent == "NEXT_PLACE":
            reply_text, quick_reply = handle_next_place_intent(user_id, intent_data)
        
        elif intent == "GENERAL_QUESTION":
            reply_text, quick_reply = handle_general_question_intent(user_id, intent_data)
        
        elif intent == "UNKNOWN":
            reply_text, quick_reply = handle_unknown_intent(user_id, intent_data)
        
        else:
            reply_text = f"กำลังพัฒนาฟีเจอร์สำหรับ Intent '{intent}'"
    
    except Exception as e:
        print(f"❌ Handler Error: {e}")
        import traceback
        traceback.print_exc()
        reply_text = f"ขอโทษครับ เกิดข้อผิดพลาด: {str(e)}"
    
    # Step 3: Send Reply
    if not reply_text:
        reply_text = "ขอโทษครับ ไม่สามารถตอบได้ในขณะนี้"
    
    if len(reply_text) > 4800:
        reply_text = reply_text[:4750] + "\n\n... (ข้อความยาวเกินไป)"
    
    print(f"🤖 Bot Reply: {reply_text[:100]}...")
    print(f"{'='*60}\n")
    
    reply_message = TextMessage(text=reply_text)
    if quick_reply:
        reply_message.quick_reply = quick_reply
    
    messaging_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[reply_message]
        )
    )


# ============================================
# Main Entry Point
# ============================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n🚀 Starting LINE Bot + Web Chat with Intent System on port {port}...")
    print(f"📊 Available Intents: {list(INTENT_TYPES.keys())}")
    print(f"🌐 Web Chat: http://localhost:{port}/")
    print(f"✅ Ready!\n")
    
    app.run(host="0.0.0.0", port=port, debug=True)
