# Security and Sensitive Data Policy

PHAGE Research Preview is a local-first research tool.

## Do not submit publicly

Never include any of the following in GitHub issues, fixtures, pull requests, or failure reports:

- passwords, API keys, tokens, certificates, private keys;
- personally identifiable information (PII);
- customer names or confidential customer data;
- proprietary source code or internal IP without authorization;
- production logs that have not been reviewed and redacted;
- classified, military-sensitive, law-enforcement-sensitive, or national-security-sensitive data;
- sensitive facility layouts, access-control details, credentials, or exploitable operational weaknesses;
- protected medical or financial records.

Use synthetic or carefully redacted fixtures whenever possible.

## Reporting a software security vulnerability

Do not open a public issue containing exploit details or secrets. Until a private security contact is established for the project, prepare a minimal redacted reproduction and contact the maintainers through a private channel listed by the repository owner.

## Research boundary

A PHAGE finding is not proof of misconduct, compromise, illegality, or unsafe operation. Findings describe only the structural state supported by the supplied inputs and implemented checks.
