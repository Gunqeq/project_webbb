# --- START OF FILE common.py ---

import math
from urllib.parse import quote_plus

# ==== CATEGORY MAP (EN+TH) - REFINED VERSION ====
# ปรับปรุงให้แต่ละหมวดหมู่มีความเฉพาะเจาะจงมากขึ้น ลดการทับซ้อน
# ==== CATEGORY MAP (EN+TH) - SMART RELAXED VERSION ====
# ปรับให้ครอบคลุม type ของ Google ที่เจอในไทยจริง ๆ มากขึ้น
CATEGORY_MAP = {
    "ธรรมชาติ": [
        "park", "natural_feature", "campground", "rv_park", "zoo",
        "tourist_attraction", "point_of_interest"
    ],
    "วัด": [
        "place_of_worship", "hindu_temple", "mosque", "church",
        "tourist_attraction"
    ],
    "คาเฟ่": [
        "cafe", "bakery", "restaurant", "food", "point_of_interest"
    ],
    "ร้านอาหาร": [
        "restaurant", "food", "meal_takeaway", "meal_delivery", "point_of_interest"
    ],
    "แหล่งเรียนรู้": [
        "museum", "library", "art_gallery", "book_store", "university", "school"
    ],
    "จุดชมวิว": [
        "tourist_attraction", "natural_feature", "park", "point_of_interest"
    ],
    "ชุมชน/ตลาด": [
        "market", "shopping_mall", "store", "supermarket", "point_of_interest"
    ],
}

# ==== CATEGORY KEYWORDS (เพิ่มคำไทยและคำอังกฤษทั่วไป) ====
CATEGORY_KEYWORDS = {
    "ธรรมชาติ": [
        "national park", "waterfall", "mountain", "beach", "forest", "nature",
        "อุทยาน", "น้ำตก", "ภูเขา", "สวน", "ป่า", "ทะเล", "สวนสาธารณะ"
    ],
    "วัด": [
        "temple", "wat", "วัด", "โบสถ์", "มัสยิด", "ศาลเจ้า", "church"
    ],
    "คาเฟ่": [
        "cafe", "coffee", "bakery", "คาเฟ่", "กาแฟ", "เบเกอรี่", "ร้านกาแฟ"
    ],
    "ร้านอาหาร": [
        "restaurant", "food", "eatery", "dining", "ร้านอาหาร", "อาหาร", "ข้าว", "บุฟเฟต์"
    ],
    "แหล่งเรียนรู้": [
        "museum", "gallery", "หอศิลป์", "พิพิธภัณฑ์", "ห้องสมุด", "ศูนย์การเรียนรู้", "มหาวิทยาลัย"
    ],
    "จุดชมวิว": [
        "viewpoint", "skywalk", "tower", "จุดชมวิว", "ทิวทัศน์", "สกายวอล์ค", "ภูเขา", "ดอย"
    ],
    "ชุมชน/ตลาด": [
        "market", "night market", "shopping", "bazaar", "ตลาด", "ตลาดน้ำ", "ตลาดนัด", "ห้าง"
    ],
}


THAI_PROVINCES = [
    "กระบี่", "กรุงเทพ", "กรุงเทพมหานคร", "กาญจนบุรี", "กาฬสินธุ์", "กำแพงเพชร", "ขอนแก่น", 
    "จันทบุรี", "ฉะเชิงเทรา", "ชลบุรี", "ชัยนาท", "ชัยภูมิ", "ชุมพร", "เชียงราย", "เชียงใหม่", 
    "ตรัง", "ตราด", "ตาก", "นครนายก", "นครปฐม", "นครพนม", "นครราชสีมา", "นครศรีธรรมราช", 
    "นครสวรรค์", "นนทบุรี", "นราธิวาส", "น่าน", "บึงกาฬ", "บุรีรัมย์", "ปทุมธานี", "ประจวบคีรีขันธ์", 
    "ปราจีนบุรี", "ปัตตานี", "พระนครศรีอยุธยา", "พะเยา", "พังงา", "พัทลุง", "พิจิตร", "พิษณุโลก", 
    "เพชรบุรี", "เพชรบูรณ์", "แพร่", "ภูเก็ต", "มหาสารคาม", "มุกดาหาร", "แม่ฮ่องสอน", "ยโสธร", 
    "ยะลา", "ร้อยเอ็ด", "ระนอง", "ระยอง", "ราชบุรี", "ลพบุรี", "ลำปาง", "ลำพูน", "เลย", 
    "ศรีสะเกษ", "สกลนคร", "สงขลา", "สตูล", "สมุทรปราการ", "สมุทรสงคราม", "สมุทรสาคร", 
    "สระแก้ว", "สระบุรี", "สิงห์บุรี", "สุโขทัย", "สุพรรณบุรี", "สุราษฎร์ธานี", "สุรินทร์", 
    "หนองคาย", "หนองบัวลำภู", "อ่างทอง", "อำนาจเจริญ", "อุดรธานี", "อุตรดิตถ์", "อุทัยธานี", 
    "อุบลราชธานี"
]

def validate_province_in_thailand(name: str) -> bool:
    if not name:
        return False
    name = name.strip()
    for province in THAI_PROVINCES:
        if name in province or province in name:
            return True
    return False


def km_between(p1, p2):
    R = 6371.0
    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def build_maps_link_by_place_id(place_id):
    return f"https://www.google.com/maps/place/?q=place_id:{place_id}"

def build_maps_link_by_latlng(lat, lng, name=""):
    label = quote_plus(name) if name else f"{lat},{lng}"
    return f"https://www.google.com/maps/search/?api=1&query={lat}%2C{lng}&query_place_id=&query={label}"

def estimate_detour_minutes(route_points, place_lat, place_lng):
    if not route_points:
        return None
    min_km = min(km_between((place_lat, place_lng), (p["lat"], p["lng"])) for p in route_points)
    minutes = (2 * min_km / 40.0) * 60.0
    return round(minutes)

def categorize_place(place_data):
    place_types = place_data.get("types", [])
    place_name = (place_data.get("name", "") or "").lower()
    categories = []

    # จาก types
    for th_cat, type_list in CATEGORY_MAP.items():
        if any(place_type in type_list for place_type in place_types):
            if th_cat not in categories:
                categories.append(th_cat)

    # จาก keywords ในชื่อสถานที่
    for th_cat, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword.lower() in place_name for keyword in keywords):
            if th_cat not in categories:
                categories.append(th_cat)

    # ถ้ายังไม่มีหมวดหมู่เลย แต่เป็น tourist_attraction ให้เป็น "จุดชมวิว"
    if not categories and "tourist_attraction" in place_types:
        categories.append("จุดชมวิว")
        
    return categories

def filter_places_by_categories(places, selected_categories):
    if not selected_categories:
        return places

    filtered_places = []
    for place in places:
        place_categories = categorize_place(place)
        if any(cat in selected_categories for cat in place_categories):
            filtered_places.append(place)

    return filtered_places