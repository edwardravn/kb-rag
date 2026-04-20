# Privileged Access Standard

## 1. Purpose
This standard defines controls for the use and management of privileged accounts.

## 2. Scope
Applies to all privileged accounts, including:
- System administrators
- Database administrators
- Service accounts with elevated permissions

## 3. Principles

### 3.1 Least Privilege
- Users must be granted only the minimum level of access required.

### 3.2 Just-in-Time Access
- Privileged access should be time-bound and approved before use.

## 4. Account Types

### 4.1 Named Admin Accounts
- Privileged access must not be performed using standard user accounts
- Separate admin accounts must be used

### 4.2 Service Accounts
- Must not be used for interactive login
- Credentials must be stored securely (e.g., vault)

## 5. Authentication
- MFA is mandatory for all privileged accounts
- Passwords must comply with the Password Policy

## 6. Logging and Monitoring
- All privileged activity must be logged
- Logs must be retained for at least **365 days**
- Alerts must be generated for:
  - Unusual login times
  - Access from new locations
  - Failed login attempts

## 7. Access Reviews
- Privileged access must be reviewed at least **quarterly**

## 8. Prohibited Actions
- Sharing privileged credentials
- Using privileged accounts for non-administrative tasks

## 9. Incident Handling
- Suspicious privileged activity must be reported immediately

## 10. Enforcement
Non-compliance may result in:
- Immediate removal of access
- Disciplinary action