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
    
    booking_keywords = [
        'termin buchen', 
        'termin auswählen', 
        'buchen', 
        'termin anmeldung', 
        'anmeldung', 
        'einbürgerungstest'
    ]
    page_text = soup.get_text().lower()
    booking_found = any(keyword in page_text for keyword in booking_keywords)
    
    cart_images = soup.find_all('img', {
        'src': lambda x: x and any(word in x.lower() for word in ['cart', 'warenkorb', 'shopping']),
        'alt': lambda x: x and any(word in x.lower() for word in ['cart', 'warenkorb', 'shopping']),
    })
    
    cart_elements = soup.find_all(class_=lambda x: x and any(word in str(x).lower() for word in  ['cart', 'warenkorb']))
    
    print(f"Cart images found: {len(cart_images)}")
    for i, img in enumerate(cart_images):
        print(f" Image {i+1}: src='{img.get('src')}', alt='{img.get('alt')}'")

    print(f"Cart elements found: {len(cart_elements)}")
    for i, elem in enumerate(cart_elements):
        print(f" Element {i+1}: tag='{elem.name}', class='{elem.get('class')}', text='{elem.get_text()[:50]}...'")
    
    cart_found = len(cart_images) > 0 or len(cart_elements) > 0
    
    return booking_found and cart_found


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