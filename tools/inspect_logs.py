# tools/inspect_logs.py
from utils.firebase_client import get_db

def get_recent_logs(limit=10):
    db = get_db()
    docs = (db.collection("user_logs")
              .order_by("timestamp", direction="DESCENDING")
              .limit(limit)
              .stream())
    for d in docs:
        print(d.id, d.to_dict())

if __name__ == "__main__":
    get_recent_logs(20)
