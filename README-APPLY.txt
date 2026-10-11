Review Insights - ALL updates, v24 (the 31% statistic is back)
==============================================================
This zip holds the FINAL version of every file changed by all updates so far, EXCEPT frontend/src/content/stats.js
(your own statistics file, which is yours and is never included). Apply it ONCE.
It includes everything from v5 to v23. NO NEW SQL. No new packages. No router change.

*** BEFORE UNZIPPING: back up your landing page ***
      cp frontend/src/views/LandingView.vue ~/LandingView.backup8.vue

1) From your project root:      unzip -o ~/Downloads/review-insights-all-updates-v24.zip
2) Rebuild:                     docker compose down && docker compose up --build

WHAT CHANGED
- The strip now shows FIVE statistics: the four from before plus the 31% you wanted kept. All are from BrightLocal's
  Local Consumer Review Survey 2026 (1,002 US adults), checked against its own page; each source line links to it.
      97%   of consumers read reviews before choosing a local business
      6     review sites used by the average consumer when choosing a local business
      85%   of consumers are more likely to use a business after reading positive reviews
      77%   of consumers say negative reviews make them less likely to choose a business
      31%   of consumers will only use a business rated 4.5 stars or higher, up from 17% a year earlier
- The stat cards are a little narrower (170px minimum instead of 220px) so all five fit on ONE row on a wide screen,
  instead of leaving a single card alone on a second row. On a narrow screen they wrap as before.

TO SHOW FEWER: delete an entry from the list in frontend/src/content/defaultStats.js (or tell me which).

IF YOU HAVE YOUR OWN frontend/src/content/stats.js
  Your file always wins, so it will not show these. Add them to your file in the same shape (value, label, source, url).
  If you do not have a stats.js you do not need to do anything.
