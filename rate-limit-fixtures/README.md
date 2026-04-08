This directory exists only to exercise CodeRabbit file-count rate-limit behavior.

The numbered fixture files under `pro-files-cap/` are intentionally tiny and
non-functional. They are included so the PR touches more than 300 files, which
exceeds the current `filesPerHour` cap used for the paid Pro git surface.
