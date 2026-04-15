---
name: astro-org-user-lookup
description: Look up Astro product user names and email addresses for a customer org from Snowflake
args: Account name (e.g., "Third Point")
---

# Accessing Astro Product User Names + Emails in Snowflake

## Prerequisites

### 1. Snowflake access
You need a Snowflake account on `fy02423-gp21411.snowflakecomputing.com`. If you don't have one, request it through IT/data team.

### 2. The PII role
Your user needs the role `HQ_MODEL_ASTRO_PII_USERS_READER` granted. This role controls access to `HQ.MODEL_ASTRO_PII.USERS`. Request it from the data/security team (SecurityAdmin owns it). The role is inherited by some roles automatically — check if you already have it:

```sql
SHOW GRANTS TO USER <your_username>;
```

Or just try the `USE ROLE` below — if it errors, you don't have it.

---

## Query

```sql
-- Step 1: switch to the PII role
USE ROLE HQ_MODEL_ASTRO_PII_USERS_READER;

-- Step 2: get the ORG_ID for the account you care about
SELECT ACCT_ID, ACCT_NAME, ORG_ID
FROM HQ.MART_CUST.CURRENT_ASTRO_CUSTS
WHERE ACCT_NAME ILIKE '%<account name>%'
LIMIT 1;

-- Step 3: pull all users in that org
SELECT p.FULL_NAME, p.EMAIL, ou.ROLE_NAME, ou.IS_ORG_OWNER,
       u.LAST_LOGIN_TS, u.LOGINS_COUNT
FROM HQ.MODEL_ASTRO_PII.USERS p
JOIN HQ.MODEL_ASTRO.ORG_USERS ou ON p.USER_ID = ou.USER_ID
JOIN HQ.MODEL_ASTRO.USERS u ON p.USER_ID = u.USER_ID
WHERE ou.ORG_ID = '<ORG_ID from step 2>'
  AND ou.IS_DELETED = FALSE
ORDER BY u.LAST_LOGIN_TS DESC NULLS LAST;
```

---

## Important Notes

- `SF_CONTACTS`, `CONTACT_360_V`, and `MODEL_ASTRO.USERS` all strip PII — `MODEL_ASTRO_PII.USERS` is the **only** table with names and emails
- The `USE ROLE` is per-session — you need to run it at the start of each Snowflake session
- After getting user data, switch back to your default role if needed: `USE ROLE <your_default_role>;`
