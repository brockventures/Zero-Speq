# Pacific Time (PT) Invariant & Time Conversion Discipline

1. **Ryan Brock and All Operations are Anchored to Pacific Time (PT):**
   - Ryan and all engineering operations operate strictly in Pacific Time (`America/Los_Angeles`, PT / PDT / PST).

2. **System Clocks and Explicit UTC Metadata:**
   - Raw VM clocks, container logs, and system metadata are often recorded in UTC.
   - **PROVENANCE-GATED CONVERSION:** Convert timestamps that are explicitly identified as UTC (`UTC`, `Z`, `+00:00`) or sourced from raw UTC system metadata into Pacific Time before displaying them.

3. **Double-Conversion & Unmarked Timestamp Safeguards:**
   - **Never Double-Convert:** If a timestamp already carries a Pacific Time label (`PT`, `PDT`, `PST`, `-07:00`, `-08:00`), do NOT convert it again.
   - **Unmarked Conversational Times:** Colloquial times mentioned in chat (e.g. "let's sync at 2:00") are already local Pacific Time.

4. **Output Formatting:**
   - Present all human-facing dates, times, schedules, and digests in Pacific Time (labeled as `PT`).
