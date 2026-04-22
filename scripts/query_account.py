#!/usr/bin/env python3
"""
Helper script to query account information from Snowflake in Claude Desktop.
Usage: python3 query_account.py "Company Name"
"""

import sys
import json
import snowflake.connector
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from pathlib import Path

def get_snowflake_connection():
    """Create Snowflake connection using private key auth"""
    with open(Path.home() / ".ssh/rsa_key_unencrypted.p8", 'rb') as key_file:
        p_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )

    private_key_bytes = p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    return snowflake.connector.connect(
        account='GP21411.us-east-1',
        user='VISHWASRINIVASAN',
        private_key=private_key_bytes,
        role='GTMADMIN',
        warehouse='HUMANS',
        database='HQ'
    )

def query_account(account_name):
    """Get account details and recent calls"""
    conn = get_snowflake_connection()
    cursor = conn.cursor()

    # Get account ID
    cursor.execute("""
        SELECT ACCT_ID, ACCT_NAME, ACCT_TYPE, IS_CURRENT_CUST
        FROM HQ.MODEL_CRM.SF_ACCOUNTS
        WHERE LOWER(ACCT_NAME) LIKE %s
        LIMIT 1
    """, (f'%{account_name.lower()}%',))

    account = cursor.fetchone()

    if not account:
        print(json.dumps({'error': f'Account "{account_name}" not found'}))
        return

    acct_id, acct_name, acct_type, is_customer = account

    # Get contacts
    cursor.execute("""
        SELECT TITLE, PRIMARY_DOMAIN, IS_EMPLOYEE
        FROM HQ.MODEL_CRM.SF_CONTACTS
        WHERE ACCT_ID = %s
        ORDER BY IS_EMPLOYEE DESC
        LIMIT 10
    """, (acct_id,))
    contacts = cursor.fetchall()

    # Get MQLs
    cursor.execute("""
        SELECT CONTACT_ID, MQL_TS, REPORTING_CHANNEL
        FROM HQ.MODEL_CRM.SF_MQLS
        WHERE ACCT_ID = %s
        ORDER BY MQL_TS DESC
        LIMIT 5
    """, (acct_id,))
    mqls = cursor.fetchall()

    # Get most recent Gong call
    cursor.execute("""
        SELECT CALL_TITLE, SCHEDULED_TS, ATTENDEES, LEFT(FULL_TRANSCRIPT, 2000) as preview
        FROM HQ.MODEL_CRM_SENSITIVE.GONG_CALL_TRANSCRIPTS
        WHERE ACCT_ID = %s
        ORDER BY SCHEDULED_TS DESC
        LIMIT 1
    """, (acct_id,))
    recent_call = cursor.fetchone()

    cursor.close()
    conn.close()

    # Format output
    result = {
        'account': {
            'name': acct_name,
            'id': acct_id,
            'type': acct_type,
            'is_customer': bool(is_customer)
        },
        'contacts': [{'title': c[0], 'domain': c[1], 'is_employee': c[2]} for c in contacts],
        'mqls': [{'contact_id': m[0], 'date': str(m[1]), 'channel': m[2]} for m in mqls],
        'recent_call': None
    }

    if recent_call:
        result['recent_call'] = {
            'title': recent_call[0],
            'date': str(recent_call[1]),
            'attendees': recent_call[2],
            'preview': recent_call[3]
        }

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 query_account.py 'Company Name'")
        sys.exit(1)

    query_account(sys.argv[1])
