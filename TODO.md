# TODO - Persist psychologist reports under child profile

## Plan steps

1. Create persistent `PsychologistReport` model under `apps/reports/` linked to `Child`.
2. Update `apps/notifications/views.py` to save incoming `type='psychologist_report'` messages into `PsychologistReport` for the given `child_id`.
3. Update `apps/reports/views.py` to return the latest stored `psychologist_report` content to authorized psychologists/parents.
4. Update Flutter psychologist report tab to display stored persisted report (latest) for the selected child.
5. Create and run Django migrations.
6. Sanity test: send report → reload report tab → persisted text shows.

## Progress

- [x] Create TODO tracker
- [x] Create PsychologistReport model
- [x] Persist psychologist_report messages to PsychologistReport
- [x] Return latest psychologist_report in GET child report
