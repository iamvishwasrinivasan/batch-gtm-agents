#!/usr/bin/env python3
"""
Generic Snowflake query helper - accepts SQL, returns JSON
Usage: python3 snowflake_query.py "SELECT * FROM table LIMIT 5"
"""

import sys
import json
import decimal
import snowflake.connector
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from pathlib import Path

def run_query(sql: str) -> dict:
    """Execute SQL and return results as JSON"""

    # Load private key
    with open(Path.home() / ".ssh/rsa_key_unencrypted.p8", 'rb') as f:
        p_key = serialization.load_pem_private_key(
            f.read(), password=None, backend=default_backend()
        )

    pk_bytes = p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Connect to Snowflake
    conn = snowflake.connector.connect(
        account='GP21411.us-east-1',
        user='VISHWASRINIVASAN',
        private_key=pk_bytes,
        role='GTMADMIN',
        warehouse='HUMANS',
        database='HQ'
    )

    cursor = conn.cursor()

    try:
        cursor.execute(sql)

        # Get column names
        columns = [col[0] for col in cursor.description]

        # Fetch all rows
        rows = cursor.fetchall()

        # Convert to list of dicts
        results = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                val = row[i]
                # Convert datetime to ISO string
                if hasattr(val, 'isoformat'):
                    val = val.isoformat()
                # Convert Decimal to float
                elif isinstance(val, decimal.Decimal):
                    val = float(val)
                row_dict[col] = val
            results.append(row_dict)

        return {
            "success": True,
            "row_count": len(results),
            "columns": columns,
            "results": results
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "error": "Usage: python3 snowflake_query.py \"SELECT * FROM table\""
        }))
        sys.exit(1)

    sql = sys.argv[1]
    result = run_query(sql)
    print(json.dumps(result, indent=2))
