#!/usr/bin/env python3
"""
PrimeHaul Lead Scraper
Scrapes UK removal company details from public directories for sales outreach.

Usage:
    python scripts/scrape_leads.py --location London --pages 3
    python scripts/scrape_leads.py --all-locations --pages 2
    python scripts/scrape_leads.py --location Manchester --enrich

Output: CSV file in /leads folder with company name, phone, website, location
"""

import argparse
import csv
import json
import re
import time
import random
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, quote

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'requests', 'beautifulsoup4'])
    import requests
    from bs4 import BeautifulSoup


# User agent
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# UK cities to search
UK_LOCATIONS = [
    'London', 'Manchester', 'Birmingham', 'Leeds', 'Glasgow', 'Liverpool',
    'Bristol', 'Sheffield', 'Edinburgh', 'Leicester', 'Coventry', 'Bradford',
    'Cardiff', 'Belfast', 'Nottingham', 'Newcastle', 'Southampton', 'Derby',
    'Portsmouth', 'Brighton', 'Plymouth', 'Northampton', 'Reading', 'Luton',
    'Wolverhampton', 'Bolton', 'Aberdeen', 'Bournemouth', 'Norwich', 'Swindon',
    'Swansea', 'Milton Keynes', 'Middlesbrough', 'Peterborough', 'Sunderland',
    'Oxford', 'York', 'Ipswich', 'Cambridge', 'Dundee', 'Gloucester', 'Blackpool',
    'Cheltenham', 'Maidstone', 'Chelmsford', 'Basildon', 'Doncaster', 'Eastbourne',
    'Worthing', 'Crawley', 'Wigan', 'Rochdale', 'Stockport', 'Lincoln', 'Bath',
    'Slough', 'Preston', 'Bedford', 'Grimsby', 'Harrogate', 'Barnsley', 'Wakefield',
    'Warrington', 'Chester', 'Worcester', 'Carlisle', 'Scarborough', 'Torquay'
]


def get_session():
    """Create a requests session"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-GB,en;q=0.9',
    })
    return session


def scrape_google_maps_api(location: str, max_results: int = 20) -> list:
    """
    Scrape removal companies using Google Places text search
    (Requires API key - set GOOGLE_PLACES_API_KEY env var)
    """
    import os
    api_key = os.environ.get('GOOGLE_PLACES_API_KEY')
    if not api_key:
        return []

    companies = []
    query = f"removal company {location} UK"

    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        'query': query,
        'key': api_key,
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        for place in data.get('results', [])[:max_results]:
            company = {
                'name': place.get('name', ''),
                'phone': '',
                'website': '',
                'location': location,
                'address': place.get('formatted_address', ''),
                'rating': str(place.get('rating', '')),
                'reviews': str(place.get('user_ratings_total', '')),
                'source': 'Google',
                'place_id': place.get('place_id', ''),
            }
            companies.append(company)

    except Exception as e:
        print(f"Google API error: {e}")

    return companies


def scrape_yelp_uk(location: str, max_pages: int = 2) -> list:
    """Scrape from Yelp UK"""
    companies = []
    session = get_session()

    print(f"  Scraping Yelp UK for '{location}'...")

    for page in range(max_pages):
        try:
            offset = page * 10
            url = f"https://www.yelp.co.uk/search?find_desc=Removal+Company&find_loc={quote(location)}&start={offset}"

            print(f"    Page {page + 1}...", end=" ", flush=True)

            response = session.get(url, timeout=15)
            if response.status_code != 200:
                print(f"Error {response.status_code}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find business cards
            cards = soup.find_all('div', {'data-testid': re.compile(r'serp-ia-card')})
            if not cards:
                # Alternative selectors
                cards = soup.find_all('div', class_=re.compile(r'container.*businessName'))
                if not cards:
                    cards = soup.find_all('h3', class_=re.compile(r'css'))

            page_count = 0
            for card in cards:
                name_elem = card.find('a', href=re.compile(r'/biz/')) or card.find('h3')
                if name_elem:
                    company = {
                        'name': name_elem.get_text(strip=True),
                        'phone': '',
                        'website': '',
                        'location': location,
                        'rating': '',
                        'reviews': '',
                        'source': 'Yelp UK',
                        'profile_url': '',
                    }

                    link = card.find('a', href=re.compile(r'/biz/'))
                    if link:
                        company['profile_url'] = urljoin('https://www.yelp.co.uk', link.get('href', ''))

                    companies.append(company)
                    page_count += 1

            print(f"Found {page_count}")
            time.sleep(random.uniform(2, 4))

        except Exception as e:
            print(f"Error: {e}")

    return companies


def scrape_free_index(location: str) -> list:
    """Scrape from FreeIndex UK"""
    companies = []
    session = get_session()

    print(f"  Scraping FreeIndex for '{location}'...")

    try:
        url = f"https://www.freeindex.co.uk/categories/home_and_garden/removals/{quote(location.lower())}/"

        response = session.get(url, timeout=15)
        if response.status_code != 200:
            print(f"    Error {response.status_code}")
            return companies

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find business listings
        listings = soup.find_all('div', class_=re.compile(r'listing|result'))

        for listing in listings:
            name_elem = listing.find('h2') or listing.find('a', class_=re.compile(r'name'))
            if name_elem:
                company = {
                    'name': name_elem.get_text(strip=True),
                    'phone': '',
                    'website': '',
                    'location': location,
                    'rating': '',
                    'reviews': '',
                    'source': 'FreeIndex',
                    'profile_url': '',
                }

                # Phone
                phone_elem = listing.find(string=re.compile(r'0[0-9]{2,4}\s?[0-9]{3,4}\s?[0-9]{3,4}'))
                if phone_elem:
                    phone_match = re.search(r'0[0-9\s]{9,13}', str(phone_elem))
                    if phone_match:
                        company['phone'] = re.sub(r'\s', '', phone_match.group())

                companies.append(company)

        print(f"    Found {len(companies)}")

    except Exception as e:
        print(f"    Error: {e}")

    return companies


def scrape_thomson_local(location: str) -> list:
    """Scrape from Thomson Local"""
    companies = []
    session = get_session()

    print(f"  Scraping Thomson Local for '{location}'...")

    try:
        url = f"https://www.thomsonlocal.com/search/{quote(location)}/removals-and-storage"

        response = session.get(url, timeout=15)
        if response.status_code != 200:
            print(f"    Error {response.status_code}")
            return companies

        soup = BeautifulSoup(response.text, 'html.parser')

        listings = soup.find_all('article') or soup.find_all('div', class_=re.compile(r'listing'))

        for listing in listings:
            name_elem = listing.find('h2') or listing.find('h3')
            if name_elem:
                company = {
                    'name': name_elem.get_text(strip=True),
                    'phone': '',
                    'website': '',
                    'location': location,
                    'rating': '',
                    'reviews': '',
                    'source': 'Thomson Local',
                    'profile_url': '',
                }

                # Try to find phone
                phone_link = listing.find('a', href=re.compile(r'^tel:'))
                if phone_link:
                    company['phone'] = phone_link.get('href', '').replace('tel:', '')

                companies.append(company)

        print(f"    Found {len(companies)}")

    except Exception as e:
        print(f"    Error: {e}")

    return companies


def scrape_192_business(location: str) -> list:
    """Scrape from 192.com business directory"""
    companies = []
    session = get_session()

    print(f"  Scraping 192.com for '{location}'...")

    try:
        url = f"https://www.192.com/business-search/q/removals/in/{quote(location.lower())}/"

        response = session.get(url, timeout=15)
        if response.status_code != 200:
            print(f"    Error {response.status_code}")
            return companies

        soup = BeautifulSoup(response.text, 'html.parser')

        listings = soup.find_all('div', class_=re.compile(r'result|listing'))

        for listing in listings:
            name_elem = listing.find('h2') or listing.find('a', class_=re.compile(r'name|title'))
            if name_elem:
                company = {
                    'name': name_elem.get_text(strip=True),
                    'phone': '',
                    'website': '',
                    'location': location,
                    'rating': '',
                    'reviews': '',
                    'source': '192.com',
                    'profile_url': '',
                }
                companies.append(company)

        print(f"    Found {len(companies)}")

    except Exception as e:
        print(f"    Error: {e}")

    return companies


def manual_company_list() -> list:
    """
    Curated list of UK removal companies gathered from research.
    These are real companies that would benefit from PrimeHaul.
    """
    return [
        # London & South East
        {'name': 'Aussie Man & Van', 'location': 'London', 'website': 'aussiemv.com', 'phone': '', 'source': 'Manual'},
        {'name': 'Kiwi Movers', 'location': 'London', 'website': 'kiwimovers.co.uk', 'phone': '', 'source': 'Manual'},
        {'name': 'Fox Moving', 'location': 'London', 'website': 'fox-moving.com', 'phone': '', 'source': 'Manual'},
        {'name': 'Gentleman & A Van', 'location': 'London', 'website': 'gentlemanandavan.co.uk', 'phone': '', 'source': 'Manual'},
        {'name': 'Fantastic Removals', 'location': 'London', 'website': 'fantasticremovals.com', 'phone': '020 3404 1646', 'source': 'Manual'},
        {'name': 'Get A Mover', 'location': 'London', 'website': 'getamover.co.uk', 'phone': '', 'source': 'Manual'},
        {'name': 'We Move Anything', 'location': 'London', 'website': 'wemoveanything.com', 'phone': '', 'source': 'Manual'},
        {'name': 'Big Van World', 'location': 'London', 'website': 'bigvanworld.co.uk', 'phone': '', 'source': 'Manual'},
        {'name': 'Volition Removals', 'location': 'London', 'website': 'volitionremovals.co.uk', 'phone': '', 'source': 'Manual'},
        {'name': 'Easy2Move', 'location': 'London', 'website': 'easy2move.com', 'phone': '', 'source': 'Manual'},
        {'name': 'MTC Removals', 'location': 'London', 'website': 'mtcremovals.com', 'phone': '020 3970 0488', 'source': 'Manual'},
        {'name': 'JamVans', 'location': 'London', 'website': 'jamvans.com', 'phone': '', 'source': 'Manual'},
        {'name': 'Quick Wasters', 'location': 'London', 'website': 'quickwasters.co.uk', 'phone': '', 'source': 'Manual'},

        # Manchester & North West
        {'name': 'Man With A Van Manchester', 'location': 'Manchester', 'website': 'manwithavanremovalsmanchester.co.uk', 'phone': '', 'source': 'Manual'},
        {'name': 'Extra Mile Removals', 'location': 'Manchester', 'website': 'extramileremovals.co.uk', 'phone': '', 'source': 'Manual'},
        {'name': 'Britannia Bradshaw', 'location': 'Manchester', 'website': 'britanniabradshaw.co.uk', 'phone': '', 'source': 'Manual'},
        {'name': 'Burke Bros Moving', 'location': 'Manchester', 'website': 'burkebros.co.uk', 'phone': '', 'source': 'Manual'},
        {'name': 'A Star Removals', 'location': 'Manchester', 'website': 'astarremovals.co.uk', 'phone': '', 'source': 'Manual'},
        {'name': 'Rightway Removals', 'location': 'Manchester', 'website': 'rightwayremovals.co.uk', 'phone': '', 'source': 'Manual'},
        {'name': '1st Move', 'location': 'Manchester', 'website': '1stmove.co.uk', 'phone': '', 'source': 'Manual'},

        # Birmingham & Midlands
        {'name': 'Complete Removals', 'location': 'Birmingham', 'website': 'completeremovals.co.uk', 'phone': '', 'source': 'Manual'},
        {'name': 'Crate Hire UK', 'location': 'Birmingham', 'website': 'cratehireuk.com', 'phone': '', 'source': 'Manual'},
        {'name': 'Squab Removals', 'location': 'Birmingham', 'website': 'squabremovals.com', 'phone': '', 'source': 'Manual'},
        {'name': 'The Removal Company Ltd', 'location': 'Kidderminster', 'website': '', 'phone': '', 'source': 'Manual'},
        {'name': 'Anthony Ward Thomas', 'location': 'London', 'website': 'awt.co.uk', 'phone': '', 'source': 'Manual'},

        # Yorkshire & North East
        {'name': 'Pickfords', 'location': 'Leeds', 'website': 'pickfords.co.uk', 'phone': '', 'source': 'Manual'},
        {'name': 'Near & Far Removals', 'location': 'Nottingham', 'website': 'nearandfarremovals.co.uk', 'phone': '', 'source': 'Manual'},
        {'name': 'Carr & Neave', 'location': 'Hull', 'website': 'carrandneave.co.uk', 'phone': '', 'source': 'Manual'},
        {'name': 'Britannia Leeds', 'location': 'Leeds', 'website': 'britannialeeds.co.uk', 'phone': '', 'source': 'Manual'},
        {'name': 'Andrew Mathers', 'location': 'Newcastle', 'website': 'andrewmathers.co.uk', 'phone': '', 'source': 'Manual'},

        # Scotland
        {'name': 'Clark & Rose', 'location': 'Edinburgh', 'website': 'clarkandrose.co.uk', 'phone': '', 'source': 'Manual'},
        {'name': 'Scotts Removals', 'location': 'Glasgow', 'website': 'scottsremovals.co.uk', 'phone': '', 'source': 'Manual'},
        {'name': 'Buzzmove', 'location': 'Edinburgh', 'website': 'buzzmove.com', 'phone': '', 'source': 'Manual'},

        # Bristol & South West
        {'name': 'Robbins Removals', 'location': 'Bristol', 'website': 'robbinsremovals.co.uk', 'phone': '', 'source': 'Manual'},
        {'name': 'Bournes Moves', 'location': 'Bristol', 'website': 'bournesmoves.com', 'phone': '', 'source': 'Manual'},
        {'name': 'Masons Moving', 'location': 'Cardiff', 'website': 'masonsmoving.co.uk', 'phone': '', 'source': 'Manual'},

        # South Coast
        {'name': 'White & Company', 'location': 'Southampton', 'website': 'whiteandcompany.co.uk', 'phone': '', 'source': 'Manual'},
        {'name': 'Moveme', 'location': 'Brighton', 'website': 'moveme.com', 'phone': '', 'source': 'Manual'},
        {'name': 'Sussex Removals', 'location': 'Brighton', 'website': 'sussexremovals.com', 'phone': '', 'source': 'Manual'},

        # East Anglia
        {'name': 'Abels Moving', 'location': 'Cambridge', 'website': 'abels.co.uk', 'phone': '', 'source': 'Manual'},
        {'name': 'Galleon World', 'location': 'Norwich', 'website': 'galleon-worldwidemovers.co.uk', 'phone': '', 'source': 'Manual'},
    ]


def deduplicate_companies(companies: list) -> list:
    """Remove duplicate companies based on name similarity"""
    seen = {}
    unique = []

    for company in companies:
        name_key = re.sub(r'[^a-z0-9]', '', company.get('name', '').lower())

        if name_key and len(name_key) > 3 and name_key not in seen:
            seen[name_key] = True
            unique.append(company)

    return unique


def enrich_with_website_contact(companies: list) -> list:
    """Visit company websites to find contact email"""
    session = get_session()

    print("\n  Enriching with website contact details...")

    for i, company in enumerate(companies):
        website = company.get('website', '')
        if not website or company.get('email'):
            continue

        if not website.startswith('http'):
            website = f"https://www.{website}"

        try:
            print(f"    [{i+1}/{len(companies)}] {company['name'][:25]}...", end=" ", flush=True)

            response = session.get(website, timeout=8, allow_redirects=True)
            if response.status_code != 200:
                print("Skip")
                continue

            text = response.text

            # Find email
            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
            valid_emails = [e for e in emails if 'example' not in e.lower() and 'test' not in e.lower()
                          and not e.endswith('.png') and not e.endswith('.jpg')]
            if valid_emails:
                company['email'] = valid_emails[0]

            # Find phone if missing
            if not company.get('phone'):
                phones = re.findall(r'(?:0|\+44)[0-9\s]{9,13}', text)
                if phones:
                    company['phone'] = re.sub(r'\s+', '', phones[0])

            print("OK" if company.get('email') else "No email")

            time.sleep(random.uniform(1, 2))

        except Exception as e:
            print("Error")

    return companies


def save_to_csv(companies: list, filename: str):
    """Save companies to CSV file"""
    if not companies:
        print("No companies to save!")
        return None

    output_dir = Path(__file__).parent.parent / 'leads'
    output_dir.mkdir(exist_ok=True)

    filepath = output_dir / filename

    fieldnames = ['name', 'email', 'phone', 'website', 'location', 'rating', 'reviews', 'source', 'profile_url']

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(companies)

    print(f"\n  Saved {len(companies)} companies to: {filepath}")
    return filepath


def save_to_json(companies: list, filename: str):
    """Save companies to JSON file"""
    if not companies:
        return

    output_dir = Path(__file__).parent.parent / 'leads'
    output_dir.mkdir(exist_ok=True)

    filepath = output_dir / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(companies, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description='Scrape UK removal company leads')
    parser.add_argument('--location', type=str, default=None,
                        help='Specific location to search (e.g., "London")')
    parser.add_argument('--all-locations', action='store_true',
                        help='Scrape multiple UK cities')
    parser.add_argument('--pages', type=int, default=2,
                        help='Max pages to scrape per source (default: 2)')
    parser.add_argument('--enrich', action='store_true',
                        help='Visit websites to find email addresses (slower)')
    parser.add_argument('--manual-only', action='store_true',
                        help='Only use curated manual list')
    parser.add_argument('--output', type=str, default=None,
                        help='Output filename (without extension)')

    args = parser.parse_args()

    print("=" * 60)
    print("  PrimeHaul Lead Scraper")
    print("  Gathering UK removal company contacts")
    print("=" * 60)

    all_companies = []

    # Always include manual curated list
    print("\n[1/4] Loading curated company list...")
    manual = manual_company_list()
    all_companies.extend(manual)
    print(f"  Loaded {len(manual)} companies from curated list")

    if not args.manual_only:
        # Determine locations
        if args.all_locations:
            locations = UK_LOCATIONS[:15]
        elif args.location:
            locations = [args.location]
        else:
            locations = ['London', 'Manchester', 'Birmingham', 'Leeds', 'Bristol']

        print(f"\n[2/4] Scraping directories for: {', '.join(locations[:5])}{'...' if len(locations) > 5 else ''}")

        for location in locations:
            print(f"\n  --- {location} ---")

            # Try different sources
            companies = scrape_yelp_uk(location, args.pages)
            all_companies.extend(companies)

            companies = scrape_thomson_local(location)
            all_companies.extend(companies)

            companies = scrape_free_index(location)
            all_companies.extend(companies)

            time.sleep(random.uniform(1, 2))

    # Deduplicate
    print(f"\n[3/4] Processing...")
    print(f"  Total collected: {len(all_companies)}")

    all_companies = deduplicate_companies(all_companies)
    print(f"  After dedup: {len(all_companies)}")

    # Enrich
    if args.enrich:
        print(f"\n[4/4] Enriching with contact details...")
        all_companies = enrich_with_website_contact(all_companies)
    else:
        print(f"\n[4/4] Skipping enrichment (use --enrich to find emails)")

    # Generate output filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    base_filename = args.output or f"removal_leads_{timestamp}"

    # Save results
    csv_path = save_to_csv(all_companies, f"{base_filename}.csv")
    save_to_json(all_companies, f"{base_filename}.json")

    # Summary
    print(f"\n{'='*60}")
    print("  RESULTS SUMMARY")
    print('='*60)
    print(f"  Total companies: {len(all_companies)}")
    print(f"  With phone: {sum(1 for c in all_companies if c.get('phone'))}")
    print(f"  With email: {sum(1 for c in all_companies if c.get('email'))}")
    print(f"  With website: {sum(1 for c in all_companies if c.get('website'))}")

    if all_companies:
        print(f"\n  Sample leads:")
        for company in all_companies[:8]:
            contact = company.get('email') or company.get('phone') or company.get('website') or 'No contact'
            print(f"    - {company['name'][:30]:30} | {company['location']:12} | {contact}")

    print(f"\n  Output: {csv_path}")
    print("=" * 60)


if __name__ == '__main__':
    main()
