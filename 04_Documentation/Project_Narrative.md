# Employee Attrition & Compensation Analytics — Project Narrative

## Overview

This project analyzes employee attrition patterns across a 180-employee dataset, combining MySQL for data cleaning and analysis with Excel for visualization and reporting. The goal was to identify *where* attrition is concentrated (by department, role, city, and time) and *why* employees leave (by reason code), and to test whether compensation is a meaningful driver of voluntary exits.

**Tools:** MySQL (data cleaning, analysis), Excel (charts, dashboard reporting)
**Tables:** `employees` (180 rows), `attrition_events` (62 rows)

---

## Data Cleaning Journey

The raw data arrived with a series of realistic, layered quality issues — each one surfaced and resolved in sequence rather than all at once, which is closer to how messy real-world data actually gets cleaned.

**1. Silent import failures.** The initial CSV import silently skipped 6 rows that had blank numeric cells, rather than erroring out. This was caught by comparing expected vs. actual row counts after import, and resolved by placing a `-1` sentinel placeholder in the blank cells of a corrected CSV (`employees_raw_v2.csv`) so those rows would import and then be explicitly identified for follow-up cleaning.

**2. Inconsistent date formats.** Both `hire_date` and `event_date` contained a mix of three formats (YYYY-MM-DD, DD/MM/YYYY, DD-Mon-YYYY) within the same column. A `REGEXP` pattern-match combined with `CASE WHEN` + `STR_TO_DATE()` detected which format each row was in and converted it to a single standard format. The first attempt at applying this fix hit a Safe Update Mode error in MySQL Workbench (a built-in guardrail against accidental mass updates), which led to establishing a standing pattern: toggle `SQL_SAFE_UPDATES` off immediately before, and back on immediately after, any UPDATE that intentionally touches every row.

**3. Duplicate employee records.** 15 `employee_id` values appeared more than once in the raw data. Investigation confirmed these were true duplicates of the same person — re-entered with a different `hire_date` format — rather than different people accidentally sharing an ID. Removing them safely required adding a temporary `AUTO_INCREMENT` surrogate key (`temp_id`) to give every physical row a unique handle, since `employee_id` itself wasn't reliable yet. A `DELETE` using `MIN(temp_id)` per group then kept exactly one copy of each duplicate. This is the one place in the project where a subquery was a deliberate, near-unavoidable choice — there's no clean join-only way to express "keep the first row per group, delete the rest."

**4. Casing and whitespace inconsistencies.** `department` and `city` both had inconsistent casing and stray whitespace across otherwise-identical values (e.g. " sales", "Sales", "SALES "). A combination of `TRIM()`, `UPPER()`, and `CASE WHEN` mapping normalized these down to 7 department values and 8 city values, with blank city entries mapped explicitly to `NULL`. `job_role` was audited with the same pattern but needed no fix — confirmed clean across 21 distinct values.

**5. A dropped table, mid-project.** At one point, `employees_staging` was accidentally dropped when a leftover `DROP TABLE` statement re-executed from an earlier position in the Workbench tab. This led to a standing rule for the rest of the project: run one SQL statement at a time, and clear the query tab between statements, so an old statement can never accidentally re-fire.

**6. Salary data errors.** `base_salary` had two separate problems: 5 rows with negative values (a sign-flip data entry bug, fixed with `ABS()`) and 5 rows with empty strings that an earlier `REGEXP` audit had missed entirely — caught only once the audit pattern was rewritten to explicitly test for `''` and `NULL` as separate conditions, rather than relying on a single catch-all pattern. Empty strings were converted to `NULL` before the column was type-converted to `DECIMAL(10,2)` — the correct fixed-point type for currency, chosen over `INT` (which would truncate cents) or `FLOAT` (which introduces rounding error).

**7. A wrong filter value.** During role-level analysis, a query comparing 'QA Engineer' against 'Digital Marketing' returned suspiciously incomplete results for the second role. A `DISTINCT` check with a `LIKE` wildcard revealed the real value in the data was 'Digital Marketing Specialist' — the filter had simply been missing a word, and `WHERE ... IN (...)` fails silently on a value that doesn't exist rather than throwing an error.

**8. Messy reason codes.** The `reason_code` column for exit events had 12 messy variants — inconsistent casing and whitespace — mapping down to only 9 real categories. A `CASE WHEN` + `TRIM(UPPER())` cleanup resolved this, but because the final `attrition_events` table had already been populated before the issue was found, the fix had to be applied to both the staging table and the final table. One analysis query (Query C, reason code by exit type) had to be re-run after this fix — its logic was correct from the start, but it couldn't produce a trustworthy result while the underlying data was still fragmented across duplicate categories.

---

## Analysis & Key Findings

**Compensation is not a major driver of attrition.** Comparing average salary across voluntary leavers, involuntary leavers, and still-employed staff showed only a ~4% gap — not enough to point to pay as a primary cause of people leaving.

**Attrition is concentrated in specific roles, not whole departments.** At the department level, Operations had the highest voluntary attrition rate (30.8%). But drilling into job roles revealed a sharper pattern: Process Associate (45.5%) and QA Engineer (50%) both had voluntary attrition rates well above their department averages — meaning the risk isn't evenly spread across a department, it's concentrated in a handful of specific roles within it.

**Performance Issues is the top reason for voluntary exits**, accounting for roughly 28% of all voluntary departures — ahead of compensation, career growth, or relocation-related reasons.

**Geography matters.** Kolkata had the highest voluntary attrition rate among cities with meaningful headcount; Delhi had the lowest.

**Attrition has a seasonal pattern.** Voluntary exits cluster noticeably in March, May, and August, rather than being evenly distributed across the year.

**Two roles, opposite attrition profiles.** IT / QA Engineer showed 100% voluntary exits, while Digital Marketing Specialist exits were mostly involuntary — a useful reminder that "attrition rate" alone doesn't tell you *why* people are leaving a given role.

---

## Reporting

Findings were built out into a 6-chart Excel dashboard: attrition timing, department breakdown, pay vs. attrition (combo chart), role breakdown, reason codes, and a city-level combo chart — each with labeled axes for readability.

---

## Reflections

The most valuable part of this project wasn't any single query — it was the debugging path. Several analysis queries (department breakdown, role breakdown, reason codes, city breakdown, timing) were first written against a column called `event_type` using values like 'Resigned'/'Terminated', before a `DESCRIBE` check and a bit of trial and error revealed the correct column for a clean Voluntary/Involuntary split was actually `exit_type`. Rather than discard that first attempt, tracking both versions made clear how much a wrong assumption about a schema can silently produce a technically-running-but-misleading query — and why checking `DESCRIBE table_name` before writing analysis queries against unfamiliar tables is now a standing habit.
