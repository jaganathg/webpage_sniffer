import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime

logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_URL = "https://www.darmstadt-vhs.de/einbuergerungstest"

def fetch_page():
    response = requests.get(BASE_URL, timeout = 30)
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

    # Debug (optional)
    print(f"Booking sections found: {len(appointment_sections)}")
    print(f"Appointment carts found: {len(appointment_carts)}")

    return appointments_available


def main():
    print("Checking VHS appointments...")
    
    try:
        html = fetch_page()
        appointments_available = detect_appointments(html)
        
        if appointments_available:
            print("Appointments Available!")
        else:
            print("No appointments currently available.")
            
    except Exception as e:
        print(f"Error: {e}")
        
if __name__ == "__main__":
    main()