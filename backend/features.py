"""Feature switches. A switched-off feature is not shown, not run and not charged.

AI_SUMMARIES      : the plain-English AI summary of what changed. When it is OFF, every industry gets the statistical trend
                    flags and sentiment-drift alerts instead (healthcare always does).
INTERNET_MENTIONS : the web-search "internet mentions" pull.

If you turn either back on, also turn it on in frontend/src/content/features.js, and update the Privacy Policy and Terms
(they describe what is sent to outside services)."""
AI_SUMMARIES = False
INTERNET_MENTIONS = False
