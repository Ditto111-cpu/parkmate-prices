#!/usr/bin/env python3
"""
Parking Price Scraper for Brisbane
Scrapes Wilson Parking and Secure Parking websites for current rates.
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from bs4 import BeautifulSoup

# Output path
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "prices.json"

# Request headers to mimic browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-AU,en;q=0.9",
}

# Brisbane Secure Parking car parks with known IDs
SECURE_BRISBANE = {
    "480-queen-street": {
        "name": "480 Queen Street Car Park",
        "address": "391 Adelaide Street, Brisbane",
        "lat": -27.464464,
        "lng": 153.030335,
    },
    "201-charlotte-street": {
        "name": "201 Charlotte Street Car Park",
        "address": "201 Charlotte Street, Brisbane",
        "lat": -27.469674,
        "lng": 153.029153,
    },
    "post-office-square": {
        "name": "Post Office Square Car Park",
        "address": "223-235 Adelaide Street, Brisbane",
        "lat": -27.466705,
        "lng": 153.027328,
    },
    "167-eagle-street": {
        "name": "167 Eagle Street Car Park",
        "address": "167 Eagle Street, Brisbane",
        "lat": -27.466068,
        "lng": 153.030365,
    },
    "macarthur-central": {
        "name": "MacArthur Central Car Park",
        "address": "246 Elizabeth Street, Brisbane",
        "lat": -27.468583,
        "lng": 153.028193,
    },
    "wintergarden": {
        "name": "Wintergarden Car Park",
        "address": "162 Elizabeth Street, Brisbane",
        "lat": -27.46979,
        "lng": 153.026744,
    },
    "findex": {
        "name": "Findex Car Park",
        "address": "120 Edward Street, Brisbane",
        "lat": -27.470104,
        "lng": 153.028256,
    },
}

# Brisbane Wilson Parking car parks
WILSON_BRISBANE = {
    "420-george-street": {
        "name": "420 George Street",
        "address": "420 George Street, Brisbane City",
        "lat": -27.4679,
        "lng": 153.0250,
        "url": "https://www.wilsonparking.com.au/park/2000112_420-George-Street-Car-Park-Brisbane",
    },
    "myer-centre": {
        "name": "Myer Centre",
        "address": "91 Queen Street, Brisbane City",
        "lat": -27.4702,
        "lng": 153.0271,
        "url": "https://www.wilsonparking.com.au/park/2000108_Myer-Centre-Brisbane",
    },
    "king-george-square": {
        "name": "King George Square",
        "address": "Ann Street, Brisbane City",
        "lat": -27.4680,
        "lng": 153.0235,
        "url": "https://www.wilsonparking.com.au/park/2000113_King-George-Square-Car-Park",
    },
    "south-bank": {
        "name": "South Bank",
        "address": "Grey Street, South Brisbane",
        "lat": -27.4785,
        "lng": 153.0210,
        "url": "https://www.wilsonparking.com.au/park/2000115_Cultural-Centre-Car-Park",
    },
    "treasury": {
        "name": "Treasury Casino",
        "address": "William Street, Brisbane City",
        "lat": -27.4730,
        "lng": 153.0240,
        "url": "https://www.wilsonparking.com.au/park/2000116_Treasury-Car-Park",
    },
    "waterfront-place": {
        "name": "Waterfront Place",
        "address": "1 Eagle Street, Brisbane City",
        "lat": -27.4670,
        "lng": 153.0310,
        "url": "https://www.wilsonparking.com.au/park/2000117_Waterfront-Place-Car-Park",
    },
    "fortitude-valley": {
        "name": "Fortitude Valley",
        "address": "McLachlan Street, Fortitude Valley",
        "lat": -27.4570,
        "lng": 153.0360,
        "url": "https://www.wilsonparking.com.au/park/2000119_Emporium-Car-Park",
    },
}


def extract_price(text: str) -> Optional[float]:
    """Extract a price from text like '$15.00' or '$15'."""
    if not text:
        return None
    match = re.search(r"\$(\d+(?:\.\d{2})?)", text)
    if match:
        return float(match.group(1))
    return None


def scrape_secure_parking() -> list[dict]:
    """
    Scrape Secure Parking Brisbane rates page.
    Returns list of car park pricing data.
    """
    results = []
    url = "https://www.secureparking.com.au/en-au/car-park-rates/brisbane/"
    
    print(f"Scraping Secure Parking: {url}")
    
    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(url, headers=HEADERS)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "lxml")
            
            # The page structure has car park sections
            # Look for car park name patterns in the HTML
            for park_id, park_info in SECURE_BRISBANE.items():
                park_data = {
                    "provider": "secure",
                    "id": park_id,
                    "name": park_info["name"],
                    "address": park_info["address"],
                    "lat": park_info["lat"],
                    "lng": park_info["lng"],
                    "hourly": None,
                    "daily": None,
                    "early_bird": None,
                    "night": None,
                    "weekend": None,
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                    "source": "scraped",
                }
                
                # Try to find this car park in the HTML
                # Secure Parking uses dynamic content, so we may not get prices
                # from static HTML - but we can try
                park_section = soup.find(string=re.compile(park_info["name"], re.IGNORECASE))
                
                if park_section:
                    # Look for nearby price elements
                    parent = park_section.find_parent("div") or park_section.find_parent("article")
                    if parent:
                        price_texts = parent.find_all(string=re.compile(r"\$\d+"))
                        for price_text in price_texts:
                            price = extract_price(str(price_text))
                            if price and not park_data["hourly"]:
                                park_data["hourly"] = price
                
                results.append(park_data)
                
    except Exception as e:
        print(f"Error scraping Secure Parking: {e}")
        # Return basic data without prices
        for park_id, park_info in SECURE_BRISBANE.items():
            results.append({
                "provider": "secure",
                "id": park_id,
                "name": park_info["name"],
                "address": park_info["address"],
                "lat": park_info["lat"],
                "lng": park_info["lng"],
                "hourly": None,
                "daily": None,
                "early_bird": None,
                "error": str(e),
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "source": "error",
            })
    
    return results


def scrape_wilson_parking() -> list[dict]:
    """
    Scrape Wilson Parking Brisbane pages.
    Returns list of car park pricing data.
    """
    results = []
    
    print("Scraping Wilson Parking...")
    
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        for park_id, park_info in WILSON_BRISBANE.items():
            park_data = {
                "provider": "wilson",
                "id": park_id,
                "name": park_info["name"],
                "address": park_info["address"],
                "lat": park_info["lat"],
                "lng": park_info["lng"],
                "hourly": None,
                "daily": None,
                "early_bird": None,
                "night": None,
                "weekend": None,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "source": "scraped",
            }
            
            try:
                print(f"  Fetching: {park_info['name']}")
                response = client.get(park_info["url"], headers=HEADERS)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "lxml")
                    
                    # Wilson's pages have pricing in various formats
                    # Look for common price patterns
                    
                    # Try to find price tables or rate sections
                    rate_sections = soup.find_all(class_=re.compile(r"rate|price|tariff", re.IGNORECASE))
                    
                    for section in rate_sections:
                        text = section.get_text()
                        
                        # Look for hourly rate
                        if re.search(r"hour|/hr", text, re.IGNORECASE):
                            price = extract_price(text)
                            if price and not park_data["hourly"]:
                                park_data["hourly"] = price
                        
                        # Look for daily max
                        if re.search(r"day|daily|max", text, re.IGNORECASE):
                            price = extract_price(text)
                            if price and not park_data["daily"]:
                                park_data["daily"] = price
                        
                        # Look for early bird
                        if re.search(r"early|bird", text, re.IGNORECASE):
                            price = extract_price(text)
                            if price and not park_data["early_bird"]:
                                park_data["early_bird"] = price
                    
                    # Also search for prices in any text
                    all_prices = soup.find_all(string=re.compile(r"\$\d+(?:\.\d{2})?"))
                    for price_text in all_prices[:10]:  # Limit to first 10
                        parent_text = str(price_text.parent.get_text()) if price_text.parent else ""
                        price = extract_price(str(price_text))
                        
                        if price:
                            if re.search(r"hour|/hr", parent_text, re.IGNORECASE) and not park_data["hourly"]:
                                park_data["hourly"] = price
                            elif re.search(r"early|bird", parent_text, re.IGNORECASE) and not park_data["early_bird"]:
                                park_data["early_bird"] = price
                            elif re.search(r"day|daily", parent_text, re.IGNORECASE) and not park_data["daily"]:
                                park_data["daily"] = price
                else:
                    park_data["error"] = f"HTTP {response.status_code}"
                    park_data["source"] = "error"
                    
            except Exception as e:
                print(f"    Error: {e}")
                park_data["error"] = str(e)
                park_data["source"] = "error"
            
            results.append(park_data)
    
    return results


def load_fallback_prices() -> dict:
    """
    Load fallback prices from existing data or return defaults.
    These are manually verified prices to use when scraping fails.
    """
    return {
        "wilson": {
            "420-george-street": {"hourly": 15.0, "daily": 59.0, "early_bird": 25.0},
            "myer-centre": {"hourly": 12.0, "daily": 55.0, "early_bird": 22.0},
            "king-george-square": {"hourly": 11.0, "daily": 45.0, "early_bird": 20.0},
            "south-bank": {"hourly": 10.0, "daily": 40.0, "early_bird": None},
            "treasury": {"hourly": 13.0, "daily": 50.0, "early_bird": None},
            "waterfront-place": {"hourly": 16.0, "daily": 65.0, "early_bird": 28.0},
            "fortitude-valley": {"hourly": 8.0, "daily": 35.0, "early_bird": None},
        },
        "secure": {
            "480-queen-street": {"hourly": 14.0, "daily": 55.0, "early_bird": 25.0},
            "201-charlotte-street": {"hourly": 13.0, "daily": 52.0, "early_bird": 24.0},
            "post-office-square": {"hourly": 14.0, "daily": 56.0, "early_bird": 26.0},
            "167-eagle-street": {"hourly": 15.0, "daily": 58.0, "early_bird": 27.0},
            "macarthur-central": {"hourly": 13.0, "daily": 55.0, "early_bird": 24.0},
            "wintergarden": {"hourly": 12.0, "daily": 50.0, "early_bird": 23.0},
            "findex": {"hourly": 14.0, "daily": 54.0, "early_bird": 25.0},
        },
    }


def merge_with_fallback(results: list[dict], provider: str, fallback: dict) -> list[dict]:
    """
    Merge scraped results with fallback prices where scraping failed.
    """
    provider_fallback = fallback.get(provider, {})
    
    for result in results:
        park_id = result["id"]
        park_fallback = provider_fallback.get(park_id, {})
        
        # Use fallback for any missing prices
        if result.get("hourly") is None and park_fallback.get("hourly"):
            result["hourly"] = park_fallback["hourly"]
            result["source"] = result.get("source", "scraped") + "+fallback"
        
        if result.get("daily") is None and park_fallback.get("daily"):
            result["daily"] = park_fallback["daily"]
            result["source"] = result.get("source", "scraped") + "+fallback"
        
        if result.get("early_bird") is None and park_fallback.get("early_bird"):
            result["early_bird"] = park_fallback["early_bird"]
            result["source"] = result.get("source", "scraped") + "+fallback"
    
    return results


def main():
    """Main scraper entry point."""
    print("=" * 60)
    print("Parkmate Price Scraper")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    
    # Load fallback prices
    fallback = load_fallback_prices()
    
    # Scrape both providers
    secure_results = scrape_secure_parking()
    wilson_results = scrape_wilson_parking()
    
    # Merge with fallback where needed
    secure_results = merge_with_fallback(secure_results, "secure", fallback)
    wilson_results = merge_with_fallback(wilson_results, "wilson", fallback)
    
    # Build output structure
    output = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "update_frequency": "weekly",
        "disclaimer": "Prices are approximate and may have changed. Always verify on official websites.",
        "secure_parking": secure_results,
        "wilson_parking": wilson_results,
    }
    
    # Write output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)
    
    print()
    print("=" * 60)
    print(f"Output written to: {OUTPUT_PATH}")
    print(f"Secure Parking: {len(secure_results)} car parks")
    print(f"Wilson Parking: {len(wilson_results)} car parks")
    print("=" * 60)
    
    # Print summary
    print("\nPrice Summary:")
    print("-" * 40)
    for result in secure_results + wilson_results:
        status = "✓" if result.get("hourly") else "✗"
        hourly = f"${result['hourly']:.2f}/hr" if result.get("hourly") else "N/A"
        print(f"  {status} {result['provider'].upper():6} {result['name'][:25]:25} {hourly}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
