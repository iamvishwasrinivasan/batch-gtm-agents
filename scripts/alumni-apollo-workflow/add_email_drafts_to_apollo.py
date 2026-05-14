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

def get_time_phrase(months):
    """Convert months to appropriate time phrase."""
    try:
        m = int(months)
        if 0 <= m <= 3:
            return "recently"
        elif 4 <= m <= 6:
            return "a few months ago"
        elif 7 <= m <= 18:
            return "last year"
        else:
            return "a couple years ago"
    except:
        return "recently"

def generate_email_draft(first_name, old_company, new_company, time_phrase, style_index):
    """Generate personalized email draft based on style."""
    old_co = normalize_company_name(old_company)
    new_co = normalize_company_name(new_company)
    booking_link = "https://calendar.app.google/oxLsb1mBTJeNYVEYA"

    styles = [
        # Style 1: AI tooling + Blueprint together
        f"""Hey {first_name},

I saw you were using Astro at {old_co} and moved over to {new_co} {time_phrase}. Curious what the Airflow landscape looks like over there?

Astro's changed a lot since you last used it. We've been building AI tooling that plugs into Claude and Cursor for teams that write DAGs, and we actually just released Blueprint this week for teams that want workflows without needing Python experience. Happy to show you what's new if it's relevant.

Best""",

        # Style 2: Question about team composition
        f"""Hey {first_name},

Noticed you were using Astro at {old_co} before joining {new_co} {time_phrase}. What does the data team look like at {new_co}? Similar setup to {old_co}?

Asking because we've shipped a lot since you last worked with Astro. AI tooling for developers building DAGs, and we just released Blueprint this week which lets non-developers create workflows through a visual builder. Worth catching up if either sounds useful.

Booking link: {booking_link}

Best,
{{{{sender_first_name}}}}
{{sender_name}}""",

        # Style 3: Mixed technical backgrounds
        f"""Hi {first_name},

I saw you were an Astro user at {old_co} before moving to {new_co} {time_phrase}. Curious what you're using for orchestration at {new_co}?

We've made a lot of improvements since you last used Astro. On the developer side we built AI tooling for faster DAG development, and we just released Blueprint for teams where analysts want to build workflows without writing Python. If you're working with mixed technical backgrounds it might be worth discussing.

Booking link: {booking_link}

Best,
{{{{sender_first_name}}}}
{{sender_name}}""",

        # Style 4: Brief with both tools
        f"""Hey {first_name},

Quick question. What does the Airflow setup look like at {new_co}?

I noticed you were using Astro back at {old_co} before the move {time_phrase}. A lot's changed since then. We've shipped AI tooling for DAG development and just released Blueprint this week (visual workflow builder for non-developers). If you're still working with Airflow at {new_co} it might be worth catching up.

Best""",

        # Style 5: Team growth focus
        f"""Hi {first_name},

I saw you were using Astro at {old_co} and moved to {new_co} {time_phrase}. What does Airflow look like at {new_co} these days?

The platform's evolved quite a bit since you last used it. We built AI tooling for developers, and just released Blueprint for teams that want to enable analysts and data scientists to create workflows without learning Python. Worth discussing if your team's grown or the makeup has changed.

Best""",

        # Style 6: Direct with team context
        f"""Hey {first_name},

Noticed you were an Astro user at {old_co} before moving to {new_co} {time_phrase}. What's the data team setup at {new_co}?

We've shipped a lot since you last used Astro. AI tooling for teams writing DAGs, and we just released Blueprint which lets less technical users build workflows through a drag-and-drop interface. Might be useful depending on your team composition. Booking link below if you want to chat.

Booking link: {booking_link}

{{sender_name}}"""
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
    """Update the 'email step 1' custom field for a contact."""
    url = f'{APOLLO_API_URL}/contacts/{contact_id}'

    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache'
    }

    payload = {
        'api_key': APOLLO_API_KEY,
        'contact_stage_id': None,  # Keep existing stage
        'typed_custom_fields': {
            '69d6b947814f5d0015ad8d0d': email_draft  # Email_Step_1 field ID
        }
    }

    try:
        response = requests.put(url, json=payload, headers=headers)
        response.raise_for_status()
        print(f"  ✓ Updated {first_name} {last_name} with email draft")
        return True
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Error updating {first_name} {last_name}: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"    Response: {e.response.text}")
        return False

def process_csv(csv_file_path: str):
    """Process the CSV file and add email drafts to Apollo contacts."""
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
            old_company = row.get('Old Company') or row.get('OLD_COMPANY', '')
            old_company = old_company.strip() if old_company else ''
            new_company = row.get('New Company') or row.get('NEW_COMPANY', '')
            new_company = new_company.strip() if new_company else ''
            months = row.get('Months Since Job Change') or row.get('MONTHS_SINCE_JOB_CHANGE', '0')
            months = str(months).strip() if months else '0'

            stats['total'] += 1

            if not first_name or not last_name or not email:
                print(f"Skipping row {stats['total']}: Missing required fields")
                stats['errors'] += 1
                continue

            print(f"\n[{stats['total']}] Processing: {first_name} {last_name} ({email})")

            # Generate personalized email draft
            time_phrase = get_time_phrase(months)
            email_draft = generate_email_draft(first_name, old_company, new_company, time_phrase, i)

            # Search for contact in Apollo
            contact_id = search_contact(first_name, last_name, email)

            if not contact_id:
                print(f"  ✗ Contact not found in Apollo")
                stats['not_found'] += 1
                continue

            # Update contact with email draft
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
    print(f"Successfully updated with email drafts: {stats['updated']}")
    print(f"Not found in Apollo: {stats['not_found']}")
    print(f"Errors: {stats['errors']}")

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = '/Users/vishwasrinivasan/Downloads/Astro Alumni Prospects - Vishwa Owned.csv'

    print("Apollo Email Draft Script - Email Step 1")
    print("="*70)
    print(f"Processing file: {csv_file}")
    print()

    process_csv(csv_file)
