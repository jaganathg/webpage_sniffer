import azure.functions as func
import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import json
import os
import pytz

app = func.FunctionApp()

BASE_URL = "https://www.darmstadt-vhs.de/einbuergerungstest"
GERMAN_TZ = pytz.timezone('Europe/Berlin')

def fetch_page():
    response = requests.get(BASE_URL, timeout=30)
    return response.text

def detect_appointments(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # 1) Appointment-specific keywords (avoid generic page text)
    booking_keywords = [
        'termin anmeldung',
        'anmeldung zum einbürgerungstest',
    ]

    # 2) Find appointment rows/sections that contain booking text
    text_hits = soup.find_all(
        string=lambda t: t and any(k in t.lower() for k in booking_keywords)
    )

    appointment_sections = []
    for t in text_hits:
        node = t if hasattr(t, 'parent') else None
        if not node:
            continue
        container = node.find_parent(['tr', 'li', 'div', 'section'])
        if container and container not in appointment_sections:
            appointment_sections.append(container)

    booking_found = len(appointment_sections) > 0

    # 3) Within those sections, look for appointment-specific cart icons (FontAwesome)
    appointment_carts = []
    for sec in appointment_sections:
        carts = sec.find_all('i', class_=lambda c: c and 'fa-shopping-cart' in ' '.join(c if isinstance(c, list) else [c]))
        if carts:
            appointment_carts.extend(carts)

    # Fallback: cart-like classes inside the same section
    if not appointment_carts:
        for sec in appointment_sections:
            carts = sec.find_all(class_=lambda c: c and any(x in ' '.join(c if isinstance(c, list) else [c]).lower() for x in ['shopping-cart', 'warenkorb']))
            if carts:
                appointment_carts.extend(carts)

    # 4) Final decision: must have BOTH appointment section AND cart inside it
    appointments_available = booking_found and len(appointment_carts) > 0

    return appointments_available

def should_run_check():
    """
    Check if the current time is within the allowed schedule:
    - Days: Monday (0), Tuesday (1), Thursday (3)
    - Time: 07:00 - 16:00 German time
    """
    now = datetime.now(GERMAN_TZ)
    current_day = now.weekday()  # Monday is 0, Sunday is 6
    current_hour = now.hour

    # Check if it's Monday, Tuesday, or Thursday
    allowed_days = [0, 1, 3]
    is_allowed_day = current_day in allowed_days

    # Check if time is between 07:00 and 16:00 (4 PM)
    is_allowed_time = 7 <= current_hour < 16

    logging.info(f'Current time: {now.strftime("%Y-%m-%d %H:%M:%S %Z")} (Day: {current_day}, Hour: {current_hour})')
    logging.info(f'Is allowed day: {is_allowed_day}, Is allowed time: {is_allowed_time}')

    return is_allowed_day and is_allowed_time

def send_logic_app_notification(appointments_data):
    """
    Send notification to Logic App when appointments are found
    """
    logic_app_url = os.environ.get('LOGIC_APP_URL', '')

    if not logic_app_url:
        logging.warning('LOGIC_APP_URL not configured. Skipping notification.')
        return False

    try:
        response = requests.post(
            logic_app_url,
            json=appointments_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )

        if response.status_code in [200, 202]:
            logging.info(f'Successfully sent notification to Logic App. Status: {response.status_code}')
            return True
        else:
            logging.warning(f'Logic App responded with status: {response.status_code}')
            return False

    except Exception as e:
        logging.error(f'Error sending notification to Logic App: {e}')
        return False

@app.timer_trigger(schedule="0 */10 * * * *", arg_name="mytimer", run_on_startup=False, use_monitor=False)
def vhs_appointment_timer(mytimer: func.TimerRequest) -> None:
    """
    Timer trigger function that runs every 10 minutes
    Checks VHS appointments only on Mon/Tue/Thu between 7 AM - 4 PM German time
    """
    logging.info('VHS Appointment Timer triggered')

    # Check if we should run based on schedule
    if not should_run_check():
        logging.info('Outside allowed schedule. Skipping this run.')
        return

    logging.info('Within allowed schedule. Proceeding with appointment check.')

    try:
        html = fetch_page()
        appointments_available = detect_appointments(html)

        result = {
            "appointments_available": appointments_available,
            "timestamp": datetime.now(GERMAN_TZ).isoformat(),
            "url": BASE_URL,
            "status": "success"
        }

        logging.info(f'Appointments available: {appointments_available}')

        # If appointments are found, send notification to Logic App
        if appointments_available:
            logging.info('Appointments found! Sending notification...')
            notification_sent = send_logic_app_notification(result)
            result['notification_sent'] = notification_sent

    except Exception as e:
        logging.error(f'Error in VHS monitoring: {e}', exc_info=True)

@app.route(route="vhs-monitor", methods=["GET", "POST"], auth_level=func.AuthLevel.ANONYMOUS)
def vhs_monitor(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger function for manual testing
    Returns JSON response with availability status
    """
    logging.info('VHS Monitor HTTP function triggered')

    try:
        html = fetch_page()
        appointments_available = detect_appointments(html)

        result = {
            "appointments_available": appointments_available,
            "timestamp": datetime.now(GERMAN_TZ).isoformat(),
            "url": BASE_URL,
            "status": "success"
        }

        logging.info(f'Appointments available: {appointments_available}')

        return func.HttpResponse(
            json.dumps(result),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f'Error in VHS monitoring: {e}')

        error_result = {
            "appointments_available": False,
            "timestamp": datetime.now(GERMAN_TZ).isoformat(),
            "url": BASE_URL,
            "status": "error",
            "error": str(e)
        }

        return func.HttpResponse(
            json.dumps(error_result),
            status_code=500,
            mimetype="application/json"
        )

