"""
generate_data.py
-----------------
Generates two synthetic RAW datasets for the Employee Attrition & Compensation
Analytics project:

    1. employees_raw.csv        -> one row per employee (all employees)
    2. attrition_events_raw.csv -> one row per attrition event
                                    (ONLY for employees who actually left)

WHY two tables instead of one?
This is deliberate. It forces a real, meaningful SQL JOIN later:
  - LEFT JOIN employees -> attrition_events  =>  active employees show NULL
    in the event columns (they never left, so they have no matching row)
  - INNER JOIN                               =>  only employees who left,
    along with their reason/exit type

This mirrors how real HR systems are structured (an "events" or "history"
table separate from the master employee table), and gives genuine practice
with JOIN logic rather than a single flat file.

WHY inject messiness on purpose?
Real-world data is never clean. Demonstrating that you can clean data
(handle missing values, fix casing, remove duplicates, fix data types)
is itself the skill being shown -- so the raw data intentionally contains:
  - ~3% missing values scattered across columns
  - 15 duplicate rows
  - inconsistent text casing (e.g. "sales", "Sales", "SALES")
  - stray leading/trailing whitespace in text fields
  - a handful of negative/impossible salary values (data entry errors)
  - inconsistent date formats for hire_date

This script ONLY generates practice data. It is not part of the actual
analysis -- the real project work happens in MySQL (cleaning + querying
with joins) and Excel (final reporting).
"""

import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Fixed seed so the "random" data is reproducible -- if you or an
# interviewer re-runs this script, you get the exact same dataset.
random.seed(42)
np.random.seed(42)

# ---------------------------------------------------------------------------
# 1. REFERENCE DATA (Indian-context values, since you're job-hunting in India)
# ---------------------------------------------------------------------------

FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Krishna",
    "Ishaan", "Rohan", "Kabir", "Aryan", "Dhruv", "Karan", "Rahul", "Amit",
    "Saanvi", "Ananya", "Diya", "Aadhya", "Kavya", "Ishita", "Priya", "Neha",
    "Riya", "Shreya", "Pooja", "Sneha", "Anjali", "Meera", "Divya", "Nisha",
    "Vikram", "Suresh", "Rajesh", "Manoj", "Sanjay", "Deepak", "Ashok", "Ravi",
    "Kiran", "Lakshmi", "Sunita", "Geeta", "Rekha", "Anita", "Swati", "Pallavi",
]

LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Iyer", "Nair", "Rao", "Reddy", "Patel",
    "Mehta", "Shah", "Joshi", "Kulkarni", "Chavan", "Deshmukh", "Pillai",
    "Menon", "Kapoor", "Malhotra", "Chopra", "Bhatt", "Agarwal", "Bose",
    "Das", "Banerjee", "Mukherjee", "Chatterjee", "Pandey", "Mishra", "Singh",
]

DEPARTMENTS = ["Sales", "Operations", "IT", "HR", "Finance", "Customer Support", "Marketing"]

JOB_ROLES = {
    "Sales": ["Sales Executive", "Sales Manager", "Business Development Associate"],
    "Operations": ["Operations Executive", "Operations Manager", "Process Associate"],
    "IT": ["Software Engineer", "QA Engineer", "IT Support Executive"],
    "HR": ["HR Executive", "HR Manager", "Talent Acquisition Specialist"],
    "Finance": ["Accounts Executive", "Finance Analyst", "Finance Manager"],
    "Customer Support": ["Customer Support Executive", "Team Lead - Support", "Quality Analyst"],
    "Marketing": ["Marketing Executive", "Digital Marketing Specialist", "Marketing Manager"],
}

CITIES = ["Mumbai", "Pune", "Bengaluru", "Delhi", "Hyderabad", "Chennai", "Ahmedabad", "Kolkata"]

EXIT_REASONS = [
    "Better Opportunity", "Relocation", "Personal Reasons",
    "Compensation Dissatisfaction", "Career Growth", "Performance Issues",
    "Work-Life Balance", "Health Reasons",
]

# ---------------------------------------------------------------------------
# 2. GENERATE EMPLOYEES TABLE
# ---------------------------------------------------------------------------

N_EMPLOYEES = 180  # within the 150-200 range decided on

# Observation window: attrition events happen within this 1-year window
WINDOW_START = datetime(2025, 1, 1)
WINDOW_END = datetime(2025, 12, 31)

def random_hire_date():
    """
    Employees must have been hired BEFORE the observation window starts,
    so that attrition events happening in 2025 make logical sense
    (you can't leave a job you joined after the event).
    Hire dates are spread across the past 1-6 years before the window.
    """
    days_before = random.randint(30, 6 * 365)
    return WINDOW_START - timedelta(days=days_before)

def base_salary_for_role(job_role):
    """
    Rough monthly salary bands (INR) by seniority implied in the role title.
    Manager/Specialist roles get a higher band than Executive/Associate roles.
    Some randomness is added so it's not a flat, unrealistic number.
    """
    if "Manager" in job_role:
        return random.randint(70000, 140000)
    elif "Specialist" in job_role or "Analyst" in job_role or "Engineer" in job_role:
        return random.randint(45000, 90000)
    else:
        return random.randint(25000, 55000)

employees = []
for i in range(1, N_EMPLOYEES + 1):
    dept = random.choice(DEPARTMENTS)
    role = random.choice(JOB_ROLES[dept])
    gender = random.choice(["Male", "Female"])
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)

    employees.append({
        "employee_id": f"E{1000 + i}",
        "first_name": first,
        "last_name": last,
        "gender": gender,
        "age": random.randint(21, 58),
        "department": dept,
        "job_role": role,
        "city": random.choice(CITIES),
        "hire_date": random_hire_date(),
        "base_salary": base_salary_for_role(role),
    })

employees_df = pd.DataFrame(employees)

# ---------------------------------------------------------------------------
# 3. GENERATE ATTRITION EVENTS TABLE
#    Only ~35% of employees actually leave -- the rest remain active
#    (and therefore will NOT appear in this table at all)
# ---------------------------------------------------------------------------

n_leavers = int(N_EMPLOYEES * 0.35)
leaver_ids = random.sample(list(employees_df["employee_id"]), n_leavers)

events = []
event_counter = 1
for emp_id in leaver_ids:
    hire_date = employees_df.loc[employees_df["employee_id"] == emp_id, "hire_date"].iloc[0]

    # Event date must be after hire_date AND within the observation window
    earliest_possible = max(hire_date, WINDOW_START)
    days_range = (WINDOW_END - earliest_possible).days
    if days_range <= 0:
        continue
    event_date = earliest_possible + timedelta(days=random.randint(0, days_range))

    exit_type = random.choice(["Voluntary", "Involuntary"])
    event_type = "Resigned" if exit_type == "Voluntary" else "Terminated"

    events.append({
        "event_id": f"EV{2000 + event_counter}",
        "employee_id": emp_id,
        "event_date": event_date,
        "event_type": event_type,
        "exit_type": exit_type,
        "reason_code": random.choice(EXIT_REASONS),
    })
    event_counter += 1

attrition_df = pd.DataFrame(events)

# ---------------------------------------------------------------------------
# 4. INJECT REALISTIC MESSINESS (deliberately, for cleaning practice)
# ---------------------------------------------------------------------------

def inject_missing(df, cols, frac=0.03):
    """Randomly blank out ~frac of values in the given columns."""
    df = df.copy()
    n_rows = len(df)
    for col in cols:
        n_missing = int(n_rows * frac)
        idx = np.random.choice(df.index, size=n_missing, replace=False)
        df.loc[idx, col] = np.nan
    return df

def inject_casing_issues(df, col):
    """Randomly change some values to lowercase, UPPERCASE, or add whitespace."""
    df = df.copy()
    def messy(val):
        if pd.isna(val):
            return val
        choice = random.random()
        if choice < 0.15:
            return val.lower()
        elif choice < 0.30:
            return val.upper()
        elif choice < 0.40:
            return f"  {val}  "  # stray whitespace
        return val
    df[col] = df[col].apply(messy)
    return df

def inject_mixed_date_formats(df, col):
    """Represent hire_date/event_date in a few different string formats."""
    df = df.copy()
    def fmt(d):
        if pd.isna(d):
            return d
        style = random.random()
        if style < 0.5:
            return d.strftime("%Y-%m-%d")        # 2023-05-12
        elif style < 0.8:
            return d.strftime("%d/%m/%Y")         # 12/05/2023
        else:
            return d.strftime("%d-%b-%Y")         # 12-May-2023
    df[col] = df[col].apply(fmt)
    return df

# --- employees table messiness ---
employees_df = inject_missing(employees_df, ["age", "base_salary", "city"], frac=0.03)
employees_df = inject_casing_issues(employees_df, "department")
employees_df = inject_casing_issues(employees_df, "city")

# 5 negative salary outliers (data entry errors)
neg_idx = np.random.choice(employees_df.index, size=5, replace=False)
employees_df.loc[neg_idx, "base_salary"] = -employees_df.loc[neg_idx, "base_salary"]

# 15 duplicate rows
dupes = employees_df.sample(15, random_state=1)
employees_df = pd.concat([employees_df, dupes], ignore_index=True)

# mixed date formats for hire_date (convert to string with varied formats)
employees_df = inject_mixed_date_formats(employees_df, "hire_date")

# shuffle row order so duplicates aren't obviously at the bottom
employees_df = employees_df.sample(frac=1, random_state=2).reset_index(drop=True)

# --- attrition_events table messiness ---
attrition_df = inject_missing(attrition_df, ["reason_code"], frac=0.03)
attrition_df = inject_casing_issues(attrition_df, "reason_code")
attrition_df = inject_mixed_date_formats(attrition_df, "event_date")
attrition_df = attrition_df.sample(frac=1, random_state=3).reset_index(drop=True)

# ---------------------------------------------------------------------------
# 5. SAVE RAW CSVs
# ---------------------------------------------------------------------------

employees_df.to_csv("employees_raw.csv", index=False)
attrition_df.to_csv("attrition_events_raw.csv", index=False)

print(f"employees_raw.csv       -> {employees_df.shape[0]} rows, {employees_df.shape[1]} columns")
print(f"attrition_events_raw.csv -> {attrition_df.shape[0]} rows, {attrition_df.shape[1]} columns")
print(f"\nEmployees who left: {n_leavers} out of {N_EMPLOYEES} ({n_leavers/N_EMPLOYEES:.0%})")
print("\nSample employees_raw.csv:")
print(employees_df.head())
print("\nSample attrition_events_raw.csv:")
print(attrition_df.head())