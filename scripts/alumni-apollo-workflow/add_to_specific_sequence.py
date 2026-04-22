import csv
import requests
import time
import argparse
from typing import Optional
from apollo_config import APOLLO_API_KEY, APOLLO_API_URL, EMAIL_ACCOUNT_ID

# Try to import rep config for multi-rep support
try:
    from rep_config import get_email_account_id
    SUPPORTS_MULTI_REP = True
except ImportError:
    SUPPORTS_MULTI_REP = False
    print("Warning: rep_config.py not found. Multi-rep support disabled.")

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

def add_contact_to_sequence(contact_id: str, sequence_id: str, first_name: str, last_name: str, email_account_id: str = None) -> dict:
    """Add a contact to a specific sequence."""
    url = f'{APOLLO_API_URL}/emailer_campaigns/{sequence_id}/add_contact_ids'

    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache'
    }

    # Use provided email_account_id or fall back to default
    sender_account_id = email_account_id if email_account_id else EMAIL_ACCOUNT_ID

    payload = {
        'contact_ids': [contact_id],
        'emailer_campaign_id': sequence_id,
        'send_email_from_email_account_id': sender_account_id,
        'api_key': APOLLO_API_KEY
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Check if contact was skipped
        skipped = data.get('skipped_contact_ids', {})
        if contact_id in skipped:
            reason = skipped[contact_id]
            return {
                'success': False,
                'skipped': True,
                'reason': reason,
                'contact_id': contact_id
            }

        # Check if contact was added successfully
        if data.get('contacts'):
            print(f"  ✓ Added {first_name} {last_name} to sequence")
            return {'success': True, 'skipped': False}

        return {
            'success': False,
            'skipped': False,
            'reason': 'Unknown error'
        }

    except requests.exceptions.RequestException as e:
        print(f"  ✗ Error adding {first_name} {last_name}: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"    Response: {e.response.text}")
        return {
            'success': False,
            'skipped': False,
            'reason': str(e)
        }

def activate_sequence(sequence_id: str) -> dict:
    """Activate a sequence so emails will send."""
    url = f'{APOLLO_API_URL}/emailer_campaigns/{sequence_id}'

    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache'
    }

    payload = {
        'api_key': APOLLO_API_KEY,
        'id': sequence_id,
        'active': True
    }

    try:
        response = requests.put(url, json=payload, headers=headers)
        response.raise_for_status()
        return {'success': True}
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': str(e)
        }

def process_csv(csv_file_path: str, sequence_id: str, email_account_id: str = None):
    """Process CSV and add contacts to sequence."""
    stats = {
        'total': 0,
        'added': 0,
        'not_found': 0,
        'skipped_in_other_sequence': 0,
        'skipped_job_change': 0,
        'errors': 0
    }
    skipped_contacts = []

    with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
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

            # Search for contact
            contact_id = search_contact(first_name, last_name, email)

            if not contact_id:
                print(f"  ✗ Contact not found in Apollo")
                stats['not_found'] += 1
                continue

            print(f"  Found contact ID: {contact_id}")

            # Add to sequence
            result = add_contact_to_sequence(contact_id, sequence_id, first_name, last_name, email_account_id)

            if result['success']:
                stats['added'] += 1
            elif result.get('skipped'):
                reason = result.get('reason', 'unknown')
                if reason == 'contacts_active_in_other_campaigns':
                    print(f"  ⚠️  Skipped: Already in another active sequence")
                    stats['skipped_in_other_sequence'] += 1
                    skipped_contacts.append({
                        'name': f"{first_name} {last_name}",
                        'email': email,
                        'reason': reason
                    })
                elif reason == 'contacts_with_job_change':
                    print(f"  ⚠️  Skipped: Recent job change detected")
                    stats['skipped_job_change'] += 1
                    skipped_contacts.append({
                        'name': f"{first_name} {last_name}",
                        'email': email,
                        'reason': reason
                    })
                else:
                    print(f"  ⚠️  Skipped: {reason}")
                    stats['errors'] += 1
            else:
                stats['errors'] += 1

            time.sleep(0.5)

    # Print summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total prospects processed: {stats['total']}")
    print(f"Successfully added to sequence: {stats['added']}")
    print(f"Not found in Apollo: {stats['not_found']}")
    print(f"Already in other sequences: {stats['skipped_in_other_sequence']}")
    print(f"Job change detected: {stats['skipped_job_change']}")
    print(f"Errors: {stats['errors']}")

    if skipped_contacts:
        print("\n" + "="*70)
        print("CONTACTS NEEDING MANUAL INTERVENTION")
        print("="*70)
        for contact in skipped_contacts:
            print(f"  • {contact['name']} ({contact['email']}) - {contact['reason']}")

    # Activate sequence
    if stats['added'] > 0:
        print("\n" + "="*70)
        print("ACTIVATING SEQUENCE")
        print("="*70)
        result = activate_sequence(sequence_id)
        if result['success']:
            print("  ✓ Sequence activated")
        else:
            print(f"  ✗ Failed to activate: {result.get('error', 'Unknown error')}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Add contacts from CSV to Apollo sequence',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default email account
  python3 add_to_specific_sequence.py "Joey_Kenney_Alumni_Prospects.csv" "69e7a4152f0c6000219d6f18"

  # Send on behalf of specific rep
  python3 add_to_specific_sequence.py "Nathan_Cooley_Alumni_Prospects.csv" "69e7a4152f0c6000219d6f18" --rep-name "Nathan Cooley"
        """
    )
    parser.add_argument('csv_file', help='CSV file with contact data')
    parser.add_argument('sequence_id', help='Apollo sequence ID')
    parser.add_argument('--rep-name', help='Rep name for email account lookup (enables sending on behalf of rep)')

    args = parser.parse_args()

    # Determine email account ID
    email_account_id = None
    if args.rep_name:
        if not SUPPORTS_MULTI_REP:
            print("Error: rep_config.py not found. Cannot use --rep-name parameter.")
            print("Create rep_config.py with rep-to-account mappings to enable multi-rep support.")
            exit(1)
        try:
            email_account_id = get_email_account_id(args.rep_name, EMAIL_ACCOUNT_ID)
            print(f"✓ Sending on behalf of: {args.rep_name}")
            print(f"  Email account ID: {email_account_id}")
        except ValueError as e:
            print(f"Error: {e}")
            exit(1)
    else:
        print(f"Using default email account: {EMAIL_ACCOUNT_ID}")

    print("\nApollo Sequence Enrollment")
    print("="*70)
    print(f"CSV File: {args.csv_file}")
    print(f"Sequence ID: {args.sequence_id}")
    print()

    process_csv(args.csv_file, args.sequence_id, email_account_id)
