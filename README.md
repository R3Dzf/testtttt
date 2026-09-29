# UC KA171 Notifications Monitor

This repository monitors the **Notifications** section of the University of Cantabria Erasmus+ KA171 Incoming Students Call 2026 page.

Target page:
https://web.unican.es/en/Studying/Pages/KA171-Call-2026.aspx

The GitHub Actions workflow checks the page automatically. When the Notifications section changes, it creates a GitHub issue and mentions `@R3Dzf` so the update appears in GitHub notifications.

The laptop does **not** need to be turned on.

## Current baseline

- No notifications published yet
- Notifications for the 2026-2027 academic year will be published in this section.

## Files

- `monitor.py` — fetches and extracts the Notifications section.
- `state.json` — stores the last known notification state.
- `.github/workflows/monitor.yml` — runs the check automatically.
