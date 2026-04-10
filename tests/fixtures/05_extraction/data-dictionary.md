# Data Dictionary

## Study Identification

| Field       | Description             | Format             |
| ----------- | ----------------------- | ------------------ |
| `study_id`  | Unique study identifier | S1, S2, ...        |
| `record_id` | Database identifier     | PMID or Scopus EID |

## Outcomes

### Primary Outcome: Depression Severity

| Field          | Description                     | Unit |
| -------------- | ------------------------------- | ---- |
| `outcome_id`   | O1 = HDRS, O2 = BDI, O3 = PHQ-9 | -    |
| `outcome_name` | Full outcome name               | text |
| `outcome_type` | continuous or binary            | -    |

### Continuous Outcomes

| Field       | Description         | Unit                    |
| ----------- | ------------------- | ----------------------- |
| `n`         | Sample size per arm | integer                 |
| `mean`      | Mean score          | scale points            |
| `sd`        | Standard deviation  | scale points            |
| `timepoint` | Assessment time     | weeks (w) or months (m) |

### Binary Outcomes

| Field    | Description       | Unit    |
| -------- | ----------------- | ------- |
| `events` | Number with event | integer |
| `total`  | Total in arm      | integer |

## Arms

| Label     | Description                    |
| --------- | ------------------------------ |
| `CBT`     | Cognitive behavioral therapy   |
| `Control` | Treatment as usual or waitlist |

## Effect Measures

- Continuous: Standardized mean difference (SMD, Hedges' g)
- Binary: Risk ratio (RR) or odds ratio (OR)
- Direction: Negative SMD = CBT better (lower depression)
