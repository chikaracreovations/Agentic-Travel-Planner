"""Local Transport, Ride-Hailing & Delivery Apps Guide for Destinations.

Provides practical local context for travelers:
- Ride-hailing & cabs: Uber, Ola, Rapido, BluSmart, GoaMiles, local taxi unions, scooter rentals.
- Food delivery: Zomato, Swiggy, Talabat, GrabFood, GoFood.
- Quick commerce & emergency contacts.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Curated practical local apps and transit intelligence
DESTINATION_GUIDES: Dict[str, Dict[str, Any]] = {
    "goa": {
        "destination": "Goa, India",
        "ride_hailing_and_cabs": {
            "recommended": [
                "GoaMiles App (Official state-backed taxi app; upfront regulated pricing)",
                "Scooter & Bike Rentals (Activa / Dio / Hunter 350; ₹350 - ₹600/day; most convenient way to explore North & South Goa)",
                "Self-Drive Cars (Thar, Swift, Baleno; ₹1,200 - ₹3,500/day via local licensed vendors)",
                "Airport Prepaid Taxi Counters (Available 24x7 at Dabolim GOI and Mopa GOX arrivals)",
            ],
            "crucial_warning": "Uber and Ola do NOT operate standard cab rides across Goa due to local taxi union regulations. Do not rely on Uber/Ola for airport pickups or beach hopping."
        },
        "food_and_quick_commerce": {
            "food_delivery": ["Zomato", "Swiggy"],
            "groceries_and_essentials": ["Blinkit (Active in North Goa hubs like Panaji, Porvorim, Calangute)", "Instamart"],
            "local_dining_tip": "Beach shacks in Anjuna, Vagator, and Baga accept UPI (GPay/PhonePe/Paytm) and cash. Remote South Goa beaches may have patchy network, keep cash handy."
        },
        "local_transit_tips": [
            "Always wear helmets when riding rented two-wheelers; Goa Traffic Police strictly enforce helmet laws.",
            "Take the Mandovi & Zuari River Ro-Ro ferries for scenic shortcuts (often free or ₹5 for two-wheelers).",
            "Kadamba AC electric buses run frequent shuttles between Panaji, Calangute, and Mopa Airport (GOX)."
        ],
        "emergency": {"police": "112", "tourist_helpline": "1364", "ambulance": "108"}
    },
    "delhi": {
        "destination": "New Delhi / NCR, India",
        "ride_hailing_and_cabs": {
            "recommended": [
                "Uber & Ola (Cabs and autos available 24x7)",
                "Rapido (Fastest option for bike taxis and quick auto bookings during peak traffic)",
                "BluSmart (100% Electric cabs; zero driver cancellations, immaculate cars, great for airport transfers)",
                "Namma Yatri / Delhi Metro (The Delhi Metro Airport Express connects IGI Airport to New Delhi Station in 19 mins)",
            ],
            "crucial_warning": "Delhi NCR traffic peaks between 8:30 AM - 11:00 AM and 5:30 PM - 8:30 PM. Use the Delhi Metro for long cross-city journeys."
        },
        "food_and_quick_commerce": {
            "food_delivery": ["Zomato", "Swiggy"],
            "groceries_and_essentials": ["Blinkit (10-minute delivery everywhere in Delhi/NCR)", "Zepto", "Swiggy Instamart"],
            "local_dining_tip": "Chandni Chowk, Connaught Place, and CyberHub accept UPI everywhere. Street vendors widely accept QR code payments."
        },
        "local_transit_tips": [
            "Get a Delhi Metro Smart Card or use the DMRC Momentum 2.0 app for QR tickets.",
            "Prepaid airport taxi booths are right outside Terminals 1, 2, and 3."
        ],
        "emergency": {"police": "112", "ambulance": "102/108", "women_helpline": "1091"}
    },
    "mumbai": {
        "destination": "Mumbai, India",
        "ride_hailing_and_cabs": {
            "recommended": [
                "Uber & Ola (Widely available across city and suburbs)",
                "Rapido (Bike taxis available in suburbs)",
                "Kaali-Peeli (Iconic black and yellow metered taxis in South Mumbai; always run on meter)",
                "Mumbai Local Trains (Western, Central & Harbour lines; use UTS app for unreserved paperless tickets)",
                "Chalo App (Live tracking and digital ticketing for BEST AC electric city buses)",
            ],
            "crucial_warning": "Auto rickshaws are NOT permitted in South Mumbai (Colaba, Fort, Marine Drive). Use Kaali-Peeli taxis or Uber there."
        },
        "food_and_quick_commerce": {
            "food_delivery": ["Zomato", "Swiggy"],
            "groceries_and_essentials": ["Zepto", "Blinkit", "Swiggy Instamart"],
            "local_dining_tip": "Try street food at Girgaon Chowpatty, Mohammed Ali Road, and Khau Gallis; 100% UPI accepted."
        },
        "local_transit_tips": [
            "Use the Mumbai Coastal Road and Atal Setu (MTHL) for quick transit between South Mumbai and Navi Mumbai/suburbs.",
            "Download the UTS app to avoid ticketing queues at local train stations."
        ],
        "emergency": {"police": "112", "ambulance": "108"}
    },
    "bengaluru": {
        "destination": "Bengaluru (Bangalore), India",
        "ride_hailing_and_cabs": {
            "recommended": [
                "Namma Yatri (Dominant community auto app with direct driver payment & zero commission)",
                "Rapido (Bike taxi & auto favorite for tech corridors)",
                "Uber & Ola (Cabs and autos)",
                "BluSmart (Reliable EV cabs for Kempegowda Airport BLR)",
                "BMTC Vayu Vajra (Volvo AC airport buses running 24x7 from airport to every major city hub)",
            ],
            "crucial_warning": "Peak Bengaluru traffic can double transit times between Whitefield, Silk Board, and Indiranagar. Factor in buffer times."
        },
        "food_and_quick_commerce": {
            "food_delivery": ["Swiggy", "Zomato"],
            "groceries_and_essentials": ["Blinkit", "Zepto", "Swiggy Instamart"],
            "local_dining_tip": "Breakfast at Vidyarthi Bhavan or Rameshwaram Cafe; filter coffee and dosas are a must."
        },
        "local_transit_tips": ["Namma Metro connects Purple & Green lines; QR ticketing available on WhatsApp."],
        "emergency": {"police": "112", "ambulance": "108"}
    },
    "himachal": {
        "destination": "Manali, Shimla, Dharamshala (Himachal Pradesh), India",
        "ride_hailing_and_cabs": {
            "recommended": [
                "Local Taxi Union Stands (Fixed government-approved rate charts for Rohtang Pass, Solang Valley, Manikaran)",
                "Motorcycle & Scooter Rentals (Royal Enfield Bullet, Himalayan, Activa; ₹800 - ₹1,800/day in Old Manali & Mall Road)",
                "HPTDC (Himachal Tourism) Luxury Volvo Coaches (Direct overnight buses from Delhi Kashmiri Gate to Manali/Shimla)",
            ],
            "crucial_warning": "Uber and Ola do NOT operate in Manali, Shimla hills, or Dharamshala. Book union taxis or self-drive."
        },
        "food_and_quick_commerce": {
            "food_delivery": ["Zomato (Active around Manali Mall Road and Shimla)", "Swiggy"],
            "groceries_and_essentials": ["Local grocery stores & chemists along Mall Road"],
            "local_dining_tip": "Enjoy trout fish, Siddu (local steamed bread), and cafes in Old Manali."
        },
        "local_transit_tips": [
            "A special Rohtang Pass permit (Green Card) is mandatory for private vehicles visiting Rohtang; union cabs have pre-cleared access.",
            "Carry cash as mountain network can drop during heavy snowfall or rain."
        ],
        "emergency": {"police": "112", "ambulance": "108"}
    },
    "kerala": {
        "destination": "Kochi, Munnar, Alleppey, Wayanad (Kerala), India",
        "ride_hailing_and_cabs": {
            "recommended": [
                "Uber & Ola (Available in Kochi city, Fort Kochi, and Trivandrum)",
                "Local Auto Rickshaws (Metered in Kochi; fixed rates in Munnar/Alleppey hills)",
                "KSRTC Fast Passenger & Swift AC buses (Comfortable state transit connecting cities to tea estates)",
                "Kerala Water Metro & Government Ferries (Scenic and ultra-cheap ₹6 - ₹20 boat transits in Kochi backwaters)",
            ],
            "crucial_warning": "In Munnar and Wayanad, ride-hailing apps are unavailable. Hire private cabs for 3-day estate tours."
        },
        "food_and_quick_commerce": {
            "food_delivery": ["Swiggy", "Zomato (In Kochi, Calicut, Trivandrum)"],
            "groceries_and_essentials": ["Instamart & Blinkit (Kochi)"],
            "local_dining_tip": "Try Kerala Sadhya on banana leaf, Appam with Stew, and fresh Karimeen fish."
        },
        "local_transit_tips": ["Houseboats in Alleppey/Kumarakom should be booked through DTPC approved counters."],
        "emergency": {"police": "112", "ambulance": "108"}
    },
    "dubai": {
        "destination": "Dubai, UAE",
        "ride_hailing_and_cabs": {
            "recommended": [
                "Careem App (The super-app of Dubai; book Hala Taxis, private cars, food, and bikes)",
                "Dubai Taxi Corporation (DTC) & RTA Taxi",
                "Dubai Metro (Red and Green lines; buy a Silver Nol Card at any station)",
                "Uber (Widely available for luxury vehicles & Black cabs)",
            ],
            "crucial_warning": "Standard taxis hailed on the street accept credit/debit cards and Nol cards; cash also accepted."
        },
        "food_and_quick_commerce": {
            "food_delivery": ["Talabat", "Deliveroo", "Careem Food", "Noon Food"],
            "groceries_and_essentials": ["Noon Minutes (15-min delivery)", "InstaShop", "Talabat Mart"]
        },
        "emergency": {"police": "999", "ambulance": "998"}
    },
    "bali": {
        "destination": "Bali, Indonesia",
        "ride_hailing_and_cabs": {
            "recommended": [
                "Grab (GrabCar and GrabBike for cheap, transparent rides)",
                "Gojek (The Indonesian super-app for GoCar, GoRide scooter taxis, and GoFood)",
                "Bluebird Taxi App (The most reputable traditional metered taxi)",
                "Scooter Rental (Most popular in Canggu & Seminyak; ~IDR 80,000 - 150,000 / ~₹450 - ₹850/day)",
            ],
            "crucial_warning": "Certain areas in Ubud, Uluwatu, and Canggu are traditional taxi zones where Grab/Gojek pickups are restricted. Walk 100m to the main road for easy app pickups."
        },
        "food_and_quick_commerce": {
            "food_delivery": ["GoFood (Gojek)", "GrabFood"],
            "groceries_and_essentials": ["GrabMart", "Indomaret", "Alfamart"]
        },
        "emergency": {"police": "110", "ambulance": "118"}
    },
    "thailand": {
        "destination": "Bangkok, Phuket, Chiang Mai (Thailand)",
        "ride_hailing_and_cabs": {
            "recommended": [
                "Grab (Dominant ride app for cabs, bikes, and food in Thailand)",
                "Bolt (Often 20-30% cheaper than Grab for car rides in Bangkok and Phuket)",
                "BTS Skytrain & MRT Subway (Fastest way to beat Bangkok traffic; rabbit card)",
                "InDrive (Negotiable fare cab service)",
            ],
            "crucial_warning": "Always ask traditional street taxis to turn on the meter ('Meter please'). If they refuse, use Grab or Bolt."
        },
        "food_and_quick_commerce": {
            "food_delivery": ["GrabFood", "LINE MAN", "Foodpanda"],
            "groceries_and_essentials": ["7-Eleven Delivery", "GrabMart"]
        },
        "emergency": {"tourist_police": "1155", "emergency": "191"}
    }
}


def get_destination_local_guide(destination: str) -> Dict[str, Any]:
    """Retrieve practical on-the-ground intelligence for a travel destination.

    Provides exact ride-hailing apps (Uber, Ola, Rapido, BluSmart, GoaMiles, Grab, etc.),
    food delivery apps (Zomato, Swiggy, Talabat), scooter rental rules, and local transit tips.

    Args:
        destination: City, state, or country name (e.g. 'Goa', 'Delhi', 'Manali', 'Kerala', 'Dubai', 'Bali', 'Thailand')

    Returns:
        Structured guide with ride apps, warnings, food delivery options, and tips.
    """
    dest_lower = destination.strip().lower()
    
    # Match keywords
    matched_key = None
    if "goa" in dest_lower:
        matched_key = "goa"
    elif any(k in dest_lower for k in ["delhi", "ncr", "gurgaon", "noida"]):
        matched_key = "delhi"
    elif "mumbai" in dest_lower or "bombay" in dest_lower:
        matched_key = "mumbai"
    elif any(k in dest_lower for k in ["bengaluru", "bangalore", "blr"]):
        matched_key = "bengaluru"
    elif any(k in dest_lower for k in ["manali", "shimla", "himachal", "dharamshala", "kullu", "spiti"]):
        matched_key = "himachal"
    elif any(k in dest_lower for k in ["kerala", "kochi", "munnar", "alleppey", "wayanad", "trivandrum"]):
        matched_key = "kerala"
    elif any(k in dest_lower for k in ["dubai", "uae", "abu dhabi"]):
        matched_key = "dubai"
    elif any(k in dest_lower for k in ["bali", "denpasar", "indonesia"]):
        matched_key = "bali"
    elif any(k in dest_lower for k in ["thailand", "bangkok", "phuket", "pattaya", "chiang mai"]):
        matched_key = "thailand"

    if matched_key and matched_key in DESTINATION_GUIDES:
        guide = DESTINATION_GUIDES[matched_key]
        return {
            "status": "success",
            "matched_destination": guide["destination"],
            "ride_hailing_and_cabs": guide["ride_hailing_and_cabs"],
            "food_and_delivery": guide["food_and_quick_commerce"],
            "local_transit_tips": guide.get("local_transit_tips", []),
            "emergency_numbers": guide.get("emergency", {"emergency": "112"}),
        }

    # Default fallback for other Indian or international destinations
    is_likely_india = True
    return {
        "status": "success",
        "matched_destination": destination.title(),
        "ride_hailing_and_cabs": {
            "recommended": [
                "Uber & Ola (Available in most Tier-1 & Tier-2 Indian cities)",
                "Rapido (Popular for fast bike taxis and budget auto-rickshaws across India)",
                "Local Autos & Prepaid Taxis (Available at airport terminals and railway junctions)",
            ],
            "crucial_warning": "In remote hill stations or union-governed zones (e.g. Goa, Ladakh, Kashmir), app-based cabs may be restricted. Check local taxi union stands."
        },
        "food_and_delivery": {
            "food_delivery": ["Zomato", "Swiggy"],
            "groceries_and_essentials": ["Blinkit", "Zepto", "Instamart"],
            "local_dining_tip": "UPI (Google Pay, PhonePe, Paytm) is accepted virtually everywhere across India."
        },
        "local_transit_tips": [
            "Keep small change and UPI ready for auto-rickshaws and street vendors.",
            "Always verify fare meters or agree on rates before boarding non-app taxis."
        ],
        "emergency_numbers": {"national_emergency": "112", "police": "100", "ambulance": "108"}
    }
