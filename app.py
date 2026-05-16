# ============================================================
# app.py — InspireWorks Plivo IVR System
# Phase 1: Route Scaffold (all routes stubbed with placeholder XML)
# ============================================================

import os
import plivo
from flask import Flask, request, Response, render_template, jsonify
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

# ── Config ────────────────────────────────────────────────
PLIVO_AUTH_ID    = os.getenv("PLIVO_AUTH_ID")
PLIVO_AUTH_TOKEN = os.getenv("PLIVO_AUTH_TOKEN")
PLIVO_FROM_NUMBER = os.getenv("PLIVO_FROM_NUMBER")
VALID_OTP        = os.getenv("VALID_OTP", "1503")
ASSOCIATE_NUMBER = os.getenv("ASSOCIATE_NUMBER")
BASE_URL         = os.getenv("BASE_URL")


def xml_response(xml_string):
    """Helper: return a Flask Response with correct Content-Type for Plivo."""
    return Response(xml_string, mimetype="application/xml")


# ── Route: Frontend ───────────────────────────────────────
@app.route("/", methods=["GET"])
def index():
    """Serve the call-trigger frontend page."""
    return render_template("index.html")


# ── Route: Make Call ──────────────────────────────────────
@app.route("/make-call", methods=["POST"])
def make_call():
    """
    Receive phone number from frontend, trigger outbound call via Plivo SDK.
    Expects JSON body: { "to_number": "+91XXXXXXXXXX" }
    """
    data      = request.get_json()
    to_number = data.get("to_number", "").strip() if data else ""

    # Validate input
    if not to_number or not to_number.startswith("+"):
        return jsonify({"error": "Invalid phone number. Must include country code (e.g. +91...)."}), 400

    try:
        client = plivo.RestClient(auth_id=PLIVO_AUTH_ID, auth_token=PLIVO_AUTH_TOKEN)

        # Place the outbound call
        # answer_url is hit when the callee picks up — points to our /answer webhook
        response = client.calls.create(
            from_=PLIVO_FROM_NUMBER,
            to_=to_number,
            answer_url=f"{BASE_URL}/answer",
            answer_method="POST"
        )
        return jsonify({"message": "Call placed successfully", "call_uuid": str(response)}), 200

    except plivo.exceptions.PlivoRestError as e:
        return jsonify({"error": f"Plivo error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


# ── Route: Answer ─────────────────────────────────────────
@app.route("/answer", methods=["POST"])
def answer():
    """
    Entry point when callee answers the call.
    Collects a 4-digit OTP via DTMF using <GetDigits>.
    """
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <GetDigits action="{BASE_URL}/verify-otp" method="POST" numDigits="4" timeout="10" retries="1">
        <Speak voice="WOMAN" language="en-US">
            Welcome to InspireWorks. Please enter your 4-digit O T P.
        </Speak>
    </GetDigits>
    <!-- Fallback if no digits received after timeout -->
    <Redirect method="POST">{BASE_URL}/answer</Redirect>
</Response>"""
    return xml_response(xml)


# ── Route: Verify OTP ─────────────────────────────────────
@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    """
    Receives DTMF digits from OTP entry.
    - Match   → redirect to /language-menu
    - Mismatch → re-prompt with error message
    - No input → silently re-prompt
    """
    digits = request.form.get("Digits", "").strip()

    # No input received — re-prompt silently
    if not digits:
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Redirect method="POST">{BASE_URL}/answer</Redirect>
</Response>"""
        return xml_response(xml)

    # Correct OTP — proceed to language menu
    if digits == VALID_OTP:
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Redirect method="POST">{BASE_URL}/language-menu</Redirect>
</Response>"""
        return xml_response(xml)

    # Wrong OTP — speak error and re-prompt
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <GetDigits action="{BASE_URL}/verify-otp" method="POST" numDigits="4" timeout="10" retries="1">
        <Speak voice="WOMAN" language="en-US">
            Incorrect O T P. Please try again. Enter your 4-digit O T P.
        </Speak>
    </GetDigits>
    <Redirect method="POST">{BASE_URL}/answer</Redirect>
</Response>"""
    return xml_response(xml)


# ── Route: Language Menu ──────────────────────────────────
@app.route("/language-menu", methods=["POST"])
def language_menu():
    """
    Level 1 menu: Press 1 for English, Press 2 for Spanish.
    Reads 'Digits' from form data and routes accordingly.
    Invalid or missing input loops back to this menu.
    """
    digits = request.form.get("Digits", "").strip()

    # Press 1 → English
    if digits == "1":
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Redirect method="POST">{BASE_URL}/action-menu?lang=en</Redirect>
</Response>"""
        return xml_response(xml)

    # Press 2 → Spanish
    if digits == "2":
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Redirect method="POST">{BASE_URL}/action-menu?lang=es</Redirect>
</Response>"""
        return xml_response(xml)

    # Invalid or no input — repeat the menu
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <GetDigits action="{BASE_URL}/language-menu" method="POST" numDigits="1" timeout="10" retries="1">
        <Speak voice="WOMAN" language="en-US">
            Please select your language. Press 1 for English. Press 2 for Spanish.
        </Speak>
    </GetDigits>
    <!-- Fallback if no digits received -->
    <Redirect method="POST">{BASE_URL}/language-menu</Redirect>
</Response>"""
    return xml_response(xml)


# ── Route: Action Menu ────────────────────────────────────
@app.route("/action-menu", methods=["POST", "GET"])
def action_menu():
    """
    Level 2 menu — language-aware.
    Reads ?lang= from query params (en or es).
    Press 1 → play audio message
    Press 2 → connect to live associate
    Invalid / no input → repeat this menu
    """
    lang   = request.args.get("lang", "en")   # carry lang from URL param
    digits = request.form.get("Digits", "").strip()

    # Press 1 → play audio
    if digits == "1":
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Redirect method="POST">{BASE_URL}/handle-action?lang={lang}&amp;choice=1</Redirect>
</Response>"""
        return xml_response(xml)

    # Press 2 → connect to associate
    if digits == "2":
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Redirect method="POST">{BASE_URL}/handle-action?lang={lang}&amp;choice=2</Redirect>
</Response>"""
        return xml_response(xml)

    # Invalid or no input — serve the menu prompt in the correct language
    if lang == "es":
        prompt = "Presione 1 para escuchar un mensaje. Presione 2 para hablar con un asociado."
        speak_lang = "es-ES"
    else:
        prompt = "Press 1 to hear a message. Press 2 to connect to a live associate."
        speak_lang = "en-US"

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <GetDigits action="{BASE_URL}/action-menu?lang={lang}" method="POST" numDigits="1" timeout="10" retries="1">
        <Speak voice="WOMAN" language="{speak_lang}">{prompt}</Speak>
    </GetDigits>
    <!-- Fallback if no digits received -->
    <Redirect method="POST">{BASE_URL}/action-menu?lang={lang}</Redirect>
</Response>"""
    return xml_response(xml)


# ── Route: Handle Action ──────────────────────────────────
@app.route("/handle-action", methods=["POST", "GET"])
def handle_action():
    """
    Reads ?lang= and ?choice= from query params.
    choice=1 → play a royalty-free MP3
    choice=2 → dial the live associate number
    """
    lang   = request.args.get("lang", "en")
    choice = request.args.get("choice", "")

    # Choice 1 — play an audio message
    if choice == "1":
        if lang == "es":
            goodbye = "Gracias por llamar a InspireWorks. Hasta luego."
            speak_lang = "es-ES"
        else:
            goodbye = "Thank you for calling InspireWorks. Goodbye."
            speak_lang = "en-US"

        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>https://s3.amazonaws.com/plivocloud/Trumpet.mp3</Play>
    <Speak voice="WOMAN" language="{speak_lang}">{goodbye}</Speak>
    <Hangup/>
</Response>"""
        return xml_response(xml)

    # Choice 2 — forward call to live associate
    if choice == "2":
        if lang == "es":
            connecting = "Conectando con un asociado. Por favor espere."
            speak_lang = "es-ES"
        else:
            connecting = "Connecting you to a live associate. Please hold."
            speak_lang = "en-US"

        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Speak voice="WOMAN" language="{speak_lang}">{connecting}</Speak>
    <Wait length="1"/>
    <Dial action="{BASE_URL}/call-ended?lang={lang}" method="POST" timeout="30" callerId="{PLIVO_FROM_NUMBER}" dialMusic="real">
        <Number>{ASSOCIATE_NUMBER}</Number>
    </Dial>
</Response>"""
        return xml_response(xml)

    # Unexpected choice — redirect back to action menu
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Redirect method="POST">{BASE_URL}/action-menu?lang={lang}</Redirect>
</Response>"""
    return xml_response(xml)


# ── Entry Point ───────────────────────────────────────────
@app.route("/call-ended", methods=["POST", "GET"])
def call_ended():
    """
    Handles the result of the live-associate Dial attempt.
    Plivo posts DialStatus here after the bridge completes or fails.
    """
    lang = request.args.get("lang", "en")
    status = request.values.get("DialStatus", "").lower()
    cause = request.values.get("DialHangupCause", "")
    ring_status = request.values.get("DialRingStatus", "")

    print(
        f"[LIVE_ASSOCIATE_DIAL] status={status or 'missing'} "
        f"ring_status={ring_status or 'missing'} "
        f"cause={cause or 'missing'}"
    )
    app.logger.info(
        "Live associate dial ended: status=%s ring_status=%s cause=%s",
        status,
        ring_status,
        cause,
    )

    if status == "completed":
        if lang == "es":
            message = "Gracias por llamar a InspireWorks. Hasta luego."
            speak_lang = "es-ES"
        else:
            message = "Thank you for calling InspireWorks. Goodbye."
            speak_lang = "en-US"
    else:
        if lang == "es":
            message = "Lo sentimos. No pudimos conectar con un asociado en este momento. Hasta luego."
            speak_lang = "es-ES"
        else:
            message = "Sorry, we could not connect you to a live associate at this time. Goodbye."
            speak_lang = "en-US"

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Speak voice="WOMAN" language="{speak_lang}">{message}</Speak>
    <Hangup/>
</Response>"""
    return xml_response(xml)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
