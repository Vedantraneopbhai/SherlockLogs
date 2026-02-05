## Brute Force / Credential Stuffing
- If repeated failed logins from same IP or many users are observed, treat as brute force.
- Actions: throttle IP, block at firewall, review for successful logins, check for lateral movement.

## Isolate Compromised Host
- If evidence of successful login followed by suspicious activity, isolate the host from network immediately.
- Actions: disconnect network, capture memory, preserve disk image, notify IR lead.

## Password Reset / MFA
- If account credential exposure suspected, force password reset and enforce MFA.
