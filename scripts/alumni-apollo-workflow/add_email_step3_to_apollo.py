import csv
import requests
import time
import re
from typing import Optional
from apollo_config import APOLLO_API_KEY, APOLLO_API_URL

def normalize_company_name(name):
    """Normalize company names by removing legal suffixes and extra info."""
    if not name:
        return name
    name = re.sub(r'\s*\([^)]*\)', '', name)
    suffixes = [
        ', Inc.', ' Inc.', ', LLC', ' LLC', ', Ltd.', ' Ltd.',
        ' Corporation', ', Corporation', ' Corp.', ', Corp.',
        ' L.P.', ', L.P.', ' GmbH', ' S.A.P.I. De C.V.',
        ' US LLC', ' USA Inc.', ' LTD'
    ]
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
    return name.strip()

def generate_final_touchbase(first_name, style_index):
    """Generate brief final touch-base email."""
    booking_link = "https://calendar.app.google/oxLsb1mBTJeNYVEYA"

    styles = [
        # Style 1: Simple thoughts
        f"""Hey {first_name},

Thoughts?

Best""",

        # Style 2: Any thoughts
        f"""Hi {first_name},

Any thoughts on this?

Best""",

        # Style 3: Bumping this
        f"""Hey {first_name},

Bumping this. Any thoughts?

Best""",

        # Style 4: Still curious
        f"""Hi {first_name},

Still curious about this. Thoughts?

Best""",

        # Style 5: Worth discussing
        f"""Hey {first_name},

Worth discussing? Thoughts?

Best""",

        # Style 6: Make sense
        f"""Hi {first_name},

Does this make sense to discuss? Thoughts?

Best"""
    ]

    return styles[style_index % len(styles)]

def search_contact(first_name: str, last_name: str, email: str) -> Optional[str]:
    """Search for a contact in Apollo and return their contact ID."""
    url = f'{APOLLO_API_URL}/people/match'

    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache'
    }

    payload = {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'api_key': APOLLO_API_KEY
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        person = data.get('person', {})

        if person.get('contact') and person['contact'].get('id'):
            return person['contact']['id']

        return None
    except requests.exceptions.RequestException as e:
        print(f"  Error searching for {first_name} {last_name}: {e}")
        return None

def update_contact_custom_field(contact_id: str, email_draft: str, first_name: str, last_name: str) -> bool:
    """Update the 'Email_Step_3' custom field for a contact."""
    url = f'{APOLLO_API_URL}/contacts/{contact_id}'

    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache'
    }

    payload = {
        'api_key': APOLLO_API_KEY,
        'contact_stage_id': None,  # Keep existing stage
        'typed_custom_fields': {
            '69d6b963fd54f60019020cdc': email_draft  # Email_Step_3 field ID
        }
    }

    try:
        response = requests.put(url, json=payload, headers=headers)
        response.raise_for_status()
        print(f"  ✓ Updated {first_name} {last_name} with final touch-base")
        return True
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Error updating {first_name} {last_name}: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"    Response: {e.response.text}")
        return False

def process_csv(csv_file_path: str):
    """Process the CSV file and add final touch-base emails to Apollo contacts."""
    stats = {
        'total': 0,
        'updated': 0,
        'not_found': 0,
        'errors': 0
    }

    with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for i, row in enumerate(reader):
            # Handle both title case and uppercase column names
            first_name = row.get('First Name') or row.get('FIRST_NAME', '')
            first_name = first_name.strip() if first_name else ''
            last_name = row.get('Last Name') or row.get('LAST_NAME', '')
            last_name = last_name.strip() if last_name else ''
            email = row.get('New Email') or row.get('NEW_EMAIL', '')
            email = email.strip() if email else ''

            stats['total'] += 1

            if not first_name or not last_name or not email:
                print(f"Skipping row {stats['total']}: Missing required fields")
                stats['errors'] += 1
                continue

            print(f"\n[{stats['total']}] Processing: {first_name} {last_name} ({email})")

            # Generate final touch-base email
            email_draft = generate_final_touchbase(first_name, i)

            # Search for contact in Apollo
            contact_id = search_contact(first_name, last_name, email)

            if not contact_id:
                print(f"  ✗ Contact not found in Apollo")
                stats['not_found'] += 1
                continue

            # Update contact with final touch-base
            if update_contact_custom_field(contact_id, email_draft, first_name, last_name):
                stats['updated'] += 1
            else:
                stats['errors'] += 1

            # Rate limiting
            time.sleep(0.5)

    # Print summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total prospects processed: {stats['total']}")
    print(f"Successfully updated with final touch-base: {stats['updated']}")
    print(f"Not found in Apollo: {stats['not_found']}")
    print(f"Errors: {stats['errors']}")

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = '/Users/vishwasrinivasan/Downloads/Astro Alumni Prospects - Vishwa Owned.csv'

    print("Apollo Final Touch-Base Script - Email Step 3")
    print("="*70)
    print(f"Processing file: {csv_file}")
    print()

    process_csv(csv_file)
