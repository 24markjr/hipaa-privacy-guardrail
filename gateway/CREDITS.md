# Credits & Third-Party Attributions

This gateway adapts patterns and small portions of code from the following
MIT-licensed open-source projects. Each ported function carries an inline
`# adapted from <project>/<file> (MIT)` comment at its definition site.

---

## anon_proxy — https://github.com/KevinXuxuxu/anon_proxy

Patterns/code adapted (Python, ported from Starlette to FastAPI):
- Streaming-safe placeholder flush (`split_at_last_open`) — `app/compliance/streaming.py`
- Overlap resolution for detected spans (`_resolve_overlaps`) — `app/compliance/overlap.py`
- Two-pass mask / JSON-safe unmask design — `app/compliance/masker.py`
- Bidirectional PII store design (re-homed onto Redis) — `app/compliance/vault.py`
- Shared httpx client + 429 retry/backoff, hop-by-hop header hygiene — `app/utils/`

```
MIT License

Copyright (c) 2026 anon-proxy contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## cloakpipe — https://github.com/rohansx/cloakpipe

Patterns/data adapted (Rust → reimplemented in Python; regexes ported verbatim):
- Compliance policy profiles (TOML → YAML) — `gateway/policies/*.yaml`
- Regex patterns for secrets & identity documents — `app/compliance/detectors/`
- Detection ordering rules (most-specific-first) — `app/compliance/detectors/patterns_in.py`
- Encrypted-vault / format-preserving token concepts — `app/compliance/vault.py`

```
MIT License

Copyright (c) 2026 Rohan Sharma

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
