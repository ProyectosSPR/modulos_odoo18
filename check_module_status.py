#!/usr/bin/env python3
"""
Script to check if saas_subscription_payment_auto_start module is installed
"""

import sys
import psycopg2

# Database connection details
DB_NAME = "odoo18"
DB_USER = "odoo"
DB_HOST = "localhost"
DB_PORT = "5432"

try:
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        host=DB_HOST,
        port=DB_PORT
    )
    cursor = conn.cursor()

    # Check module status
    cursor.execute("""
        SELECT name, state, latest_version
        FROM ir_module_module
        WHERE name = 'saas_subscription_payment_auto_start'
    """)

    result = cursor.fetchone()

    if result:
        print(f"Module found:")
        print(f"  Name: {result[0]}")
        print(f"  State: {result[1]}")
        print(f"  Version: {result[2]}")
    else:
        print("Module NOT found in database!")
        print("The module needs to be installed.")

    cursor.close()
    conn.close()

except psycopg2.Error as e:
    print(f"Database error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
