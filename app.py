\
import os
import math
import requests
from flask import Flask, request, jsonify, render_template
from twilio.rest import Client
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Flask app
app = Flask(__name__, static_folder="static", template_folder="templates")

# Environment variables
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")
TEST_NUMBER = os.getenv("TEST_NUMBER")  # 👈 put your own mobile number in .env
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
FALLBACK_EMERGENCY_NUMBER = os.getenv("FALLBACK_EMERGENCY_NUMBER", TEST_NUMBER)

# Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


# Distance helper
def meters_between(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# For now, keep it simple (later you can hook Google Places)
def resolve_contact_for_category(category, lat, lng):
    return {
        "name": "Demo Emergency Service",
        "address": "123 Main Street",
        "phone": TEST_NUMBER,  # always send to your test number
        "lat": lat,
        "lng": lng,
    }


# Twilio SMS helper
def send_sms(to_number, body):
    return twilio_client.messages.create(
        body=body,
        from_=TWILIO_PHONE,
        to=to_number,
    )


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/sos", methods=["POST"])
def api_sos():
    data = request.get_json(force=True)
    category = data.get("category", "police")
    lat = float(data.get("lat", 0))
    lng = float(data.get("lng", 0))

    contact = resolve_contact_for_category(category, lat, lng)

    maps_link = f"https://www.google.com/maps?q={lat},{lng}"
    subject = {
        "police": "Police",
        "fire": "Fire & Rescue",
        "ambulance": "Ambulance/Hospital",
        "women": "Women Safety",
    }.get(category, "Emergency")

    target_number = TEST_NUMBER  # always YOUR number for testing

    try:
        body = (
            f"🚨 {subject} SOS (GestSOS)\n"
            f"Location: {maps_link}\n"
            f"Nearest: {contact['name']}\n"
            f"Address: {contact['address']}"
        )
        sms = send_sms(target_number, body)
        return jsonify({"ok": True, "twilio_sid": sms.sid, "sent_to": target_number, "nearest": contact})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "nearest": contact}), 500


if __name__ == "__main__":
    app.run(debug=False)
import os, math, requests
from flask import Flask, render_template, request, jsonify
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")

# --- Load ENV variables ---
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")
TEST_PHONE = os.getenv("TEST_PHONE")   # 👈 your personal number for testing

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


# --- Utility functions (still kept for later real version) ---
def meters_between(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dlmb/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def google_nearby(lat, lng, place_type, radius=8000):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {"location": f"{lat},{lng}", "radius": radius, "type": place_type, "key": os.getenv("GOOGLE_MAPS_API_KEY")}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


# --- SMS Sender ---
def send_sms(to_number, body):
    return twilio_client.messages.create(body=body, from_=TWILIO_PHONE, to=to_number)


# --- Routes ---
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/sos", methods=["POST"])
def api_sos():
    data = request.get_json(force=True)
    category = data.get("category", "police")
    lat = float(data.get("lat"))
    lng = float(data.get("lng"))

    maps_link = f"https://www.google.com/maps?q={lat},{lng}"
    subject = {"police":"Police","fire":"Fire & Rescue","ambulance":"Ambulance/Hospital","women":"Women Safety"}.get(category,"Emergency")

    # ✅ Always send to your TEST_PHONE
    target_number = TEST_PHONE  

    try:
        body = f"🚨 {subject} SOS (GestSOS)\nLocation: {maps_link}\n⚠️ [TEST MODE: sent only to your number]"
        sms = send_sms(target_number, body)
        return jsonify({"ok": True, "twilio_sid": sms.sid, "sent_to": target_number})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
