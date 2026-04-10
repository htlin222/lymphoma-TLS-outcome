# Data Dictionary Template

## Study
- `study_id`: unique identifier
- `record_id`: screening identifier (matches `03_screening` and `04_fulltext`)
- `title`
- `year`
- `doi`
- `pmid`
- `design` (RCT, cohort, case-control, etc.)
- `country`
- `notes`

## Outcomes
- `outcome_id`
- `name`
- `unit`
- `outcome_type` (continuous, binary, time-to-event)

## Arms
- `arm_id`
- `study_id`
- `arm_label`
- `n`

## Measurements
- `measurement_id`
- `study_id`
- `outcome_id`
- `arm_id`
- `timepoint`
- `mean`
- `sd`
- `events`
- `total`
- `effect`
- `se`
- `ci_low`
- `ci_high`
- `notes`

## Sources
- `source_id`
- `study_id`
- `record_id`
- `file_path`
- `page_reference`
- `notes`
