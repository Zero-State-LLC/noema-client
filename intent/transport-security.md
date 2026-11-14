# Transport security

## Problem

The Controller HTTP transport could forward bearer credentials and sensitive custom headers when following redirects. Importing it also replaced the process-wide DNS resolver with an IPv4-only wrapper.

## Outcome

Protocol HTTP requests fail closed on redirects without contacting the redirect target or accepting a redirect body as success. Importing the client leaves the standard dual-stack resolver untouched.

## Users

Controller client users and applications embedding the Python package.

## Constraints

- Reject redirects, including same-origin redirects, rather than forwarding credentials, admin headers, seals, or request bodies.
- Preserve ordinary standard-library IPv4/IPv6 resolution without global socket patches.
- Exercise security regressions with synthetic credentials and local loopback servers only.
- This is client transport policy, not a change to world semantics, admission, identity, or seal authority.

## Open questions

None for this bounded fix. Any future redirect support requires a separate explicit credential and origin policy.
