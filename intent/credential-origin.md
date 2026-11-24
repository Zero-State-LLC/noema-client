# Credential origin binding (client-only)

## Problem
The Controller could reuse a stored access/resume credential against a separately selected server, or send it to a cross-origin WebSocket endpoint advertised by discovery. Environment access tokens also inherited unrelated disk identity and resume metadata.

## Outcome
Before gateway binding, compare normalized scheme, hostname, and effective port against the credential server. Reject mismatches without transmitting credentials. Resolve relative WebSocket endpoints against the selected server and reject cross-origin or downgraded destinations before opening the socket, HELLO resume, or AUTH, including automatic transport selection. HTTP/WS and HTTPS/WSS are equivalent transport pairs, not permission to downgrade. Hostname case and explicit default ports do not change origin. Force enrollment remains available on the selected server.

## Users
Controller CLI and Python client users switching servers or providing intentional environment credentials.

## Constraints
No protocol, world, admission, or seal changes. No Admin-as-Player. `NOEMA_TOKEN` intentionally targets the selected server but must not inherit disk identity, world, or resume metadata. Legacy disk credentials without server metadata retain the historical default server, never an environment-selected destination. Invalid origins fail closed. Redirect protections remain the transport layer's responsibility. Tests use synthetic credentials and injected transports.

## Open questions
None for this bounded client fix. Cross-origin credential delegation would require a separately authorized design, not a discovery hint.
