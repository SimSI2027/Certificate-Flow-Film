# Transcript

Generated from `cff/story/captions.py`. Times are the full-opacity hold of each caption.

## S1 — The connection begins

- 00:00:01.000–00:00:05.000 — Secure RDP connection

## S2 — An identity the client can't verify

- 00:00:08.200–00:00:12.500 — The RDP server needs a trusted identity

## S3 — Keys born locally, request sealed

- 00:00:15.000–00:00:18.200 — The private key stays on the server
- 00:00:20.700–00:00:23.700 — The request is signed, not the key sent

## S4 — Finding the right CA, then evaluation

- 00:00:29.000–00:00:35.000 — Issuing CA 1 verifies, then signs

## S5 — The hierarchy and the trust anchor

- 00:00:41.900–00:00:45.900 — The Root CA signs the issuing CA certificate
- 00:00:47.100–00:00:49.700 — The Root CA is the trust anchor

## S6 — Presentation and validation

- 00:00:53.500–00:01:03.000 — The client validates the whole chain
- 00:01:07.200–00:01:09.700 — Trusted RDP connection established

## S7 — A second workload

- 00:01:16.000–00:01:20.500 — Different templates can use different issuing CAs

## S8 — Issuing CA 2 signs

- 00:01:25.500–00:01:29.100 — Issuing CA 2 signs the TLS certificate

## S9 — Full picture and close

- 00:01:39.000–00:01:43.000 — Different issuing paths. One trusted root.
- 00:01:44.500–00:01:48.200 — Certificate Flow — From request to trust
