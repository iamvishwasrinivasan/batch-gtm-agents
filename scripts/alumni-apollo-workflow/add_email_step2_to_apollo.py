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

def generate_followup_email(first_name, old_company, new_company, time_phrase, style_index):
    """Generate follow-up email asking about team differences."""
    old_co = normalize_company_name(old_company)
    new_co = normalize_company_name(new_company)
    booking_link = "https://calendar.app.google/oxLsb1mBTJeNYVEYA"

    styles = [
        # Style 1: Direct team comparison question
        f"""Hey {first_name},

Following up on my last message. I'm curious, what's the biggest difference between the data team at {new_co} versus what you had at {old_co}?

I ask because we work with teams across the spectrum (from lean engineering-heavy shops to larger orgs with analysts and data scientists), and it helps me understand what might be relevant for your setup.

Best""",

        # Style 2: Team maturity focus
        f"""Hi {first_name},

Quick follow-up. Since you moved from {old_co} to {new_co} {time_phrase}, what's the biggest difference you've noticed between the two data teams?

Asking because team composition tends to drive tooling needs (whether folks are writing Python, using SQL, or somewhere in between), and it'd help me understand what makes sense for {new_co}.

Best""",

        # Style 3: Casual comparison
        f"""Hey {first_name},

Wanted to follow up. What's the biggest difference between your team at {new_co} compared to {old_co}?

I'm always curious how teams are structured differently (size, technical backgrounds, tooling preferences) since it shapes what kind of orchestration setup makes sense.

Booking link: {booking_link}

Cheers,
{{{{sender_first_name}}}}""",

        # Style 4: Context-driven
        f"""Hi {first_name},

Following up from my last email. As you've transitioned from {old_co} to {new_co}, what's been the biggest difference in how the data teams operate?

Understanding team dynamics (engineering vs. analyst ratio, workflow preferences, etc.) helps me figure out if something like Blueprint or our AI tooling would actually be useful for your team.

Best""",

        # Style 5: Open-ended team question
        f"""Hey {first_name},

Quick question following up. What's the biggest difference between working with the data team at {new_co} versus {old_co}?

Whether it's team size, technical skills, or how work gets done, I'm curious what changed when you made the move {time_phrase}.

Best""",

        # Style 6: Direct and brief
        f"""Hi {first_name},

Following up. What's the biggest difference between the {new_co} data team and what you had at {old_co}?

Helps me understand if our newer features (AI tooling for developers, Blueprint for analysts) would be relevant for your setup.

Booking link: {booking_link}

{{{{sender_first_name}}}}"""
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
    """Update the 'Email_Step_2' custom field for a contact."""
    url = f'{APOLLO_API_URL}/contacts/{contact_id}'

    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache'
    }

    payload = {
        'api_key': APOLLO_API_KEY,
        'contact_stage_id': None,  # Keep existing stage
        'typed_custom_fields': {
            '69d6b9550c13b10011beee6e': email_draft  # Email_Step_2 field ID
        }
    }

    try:
        response = requests.put(url, json=payload, headers=headers)
        response.raise_for_status()
        print(f"  ✓ Updated {first_name} {last_name} with follow-up email")
        return True
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Error updating {first_name} {last_name}: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"    Response: {e.response.text}")
        return False

def process_csv(csv_file_path: str):
    """Process the CSV file and add follow-up emails to Apollo contacts."""
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

            # Generate follow-up email
            time_phrase = get_time_phrase(months)
            email_draft = generate_followup_email(first_name, old_company, new_company, time_phrase, i)

            # Search for contact in Apollo
            contact_id = search_contact(first_name, last_name, email)

            if not contact_id:
                print(f"  ✗ Contact not found in Apollo")
                stats['not_found'] += 1
                continue

            # Update contact with follow-up email
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
    print(f"Successfully updated with follow-up emails: {stats['updated']}")
    print(f"Not found in Apollo: {stats['not_found']}")
    print(f"Errors: {stats['errors']}")

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = '/Users/vishwasrinivasan/Downloads/Astro Alumni Prospects - Vishwa Owned.csv'

    print("Apollo Follow-Up Email Script - Email Step 2")
    print("="*70)
    print(f"Processing file: {csv_file}")
    print()

    process_csv(csv_file)
