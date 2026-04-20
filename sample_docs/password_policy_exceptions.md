# Password Policy Exceptions

## 1. Purpose
This document defines approved exceptions to the standard Password Policy.

## 2. Scope
Applies to service accounts, legacy systems, and approved technical constraints.

## 3. Service Account Exceptions
- Service accounts may use passwords shorter than 12 characters if:
  - The system does not support longer passwords
  - The account is non-interactive
- Minimum length for such accounts: **8 characters**

## 4. Legacy Systems
- Systems that cannot enforce password complexity may be exempt
- Compensating controls must be implemented:
  - Network restrictions
  - Monitoring
  - Access limitations

## 5. Password Rotation Exceptions
- Service accounts may rotate every **180 days**
- Exception must be documented and approved

## 6. Approval Requirements
- All exceptions must be:
  - Approved by Information Security
  - Documented in the exception register

## 7. Risk Acknowledgment
- Exceptions increase risk and must be reviewed annually