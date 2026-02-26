"""
Post-processing script to populate the Consultant_Title_History table.

Implements the complex promotion-chain logic:
- Each consultant gets 1-3 rows depending on number of promotions (0-2)
- Initial title assigned with weighted distribution
- Dates are always on the 1st of the month
- Salary follows normal distribution based on title level
- Promotion chains are sequential (Row N+1 starts where Row N ends)
"""

import sqlite3
import random
import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Configuration
DB_PATH = os.environ.get('CONSULTING_DB_PATH', 'output/consulting.db')
RANDOM_SEED = 42

# Title definitions: TitleID -> (name, salary_mean, salary_std)
TITLE_SALARY = {
    1: (100_000, 10_000),   # Consultant (TitleID=1)
    2: (120_000, 10_000),   # Senior Consultant
    3: (140_000, 10_000),   # Manager
    4: (160_000, 20_000),   # Senior Manager
    5: (180_000, 20_000),   # Associate Partner
    6: (200_000, 20_000),   # Partner
}

# Initial title distribution weights (TitleID: probability)
INITIAL_TITLE_WEIGHTS = {
    1: 0.30,  # Consultant
    2: 0.30,  # Senior Consultant
    3: 0.20,  # Manager
    4: 0.10,  # Senior Manager
    5: 0.05,  # Associate Partner
    6: 0.05,  # Partner
}

# Date range
DATE_START = datetime(2020, 1, 1)
DATE_END = datetime(2025, 12, 1)


def first_of_month(dt):
    """Return the first of the month for a given datetime."""
    return dt.replace(day=1)


def random_first_of_month(start, end):
    """Return a random date that is the 1st of some month between start and end."""
    months_between = (end.year - start.year) * 12 + (end.month - start.month)
    if months_between <= 0:
        return first_of_month(start)
    random_months = random.randint(0, months_between)
    return first_of_month(start + relativedelta(months=random_months))


def generate_salary(title_id):
    """Generate a salary based on title-specific normal distribution."""
    mean, std = TITLE_SALARY[title_id]
    salary = random.gauss(mean, std)
    return round(max(salary, mean - 2 * std), 2)  # Floor at mean - 2*std


def weighted_choice(weights_dict):
    """Pick a key from a {key: probability} dict."""
    keys = list(weights_dict.keys())
    probs = list(weights_dict.values())
    return random.choices(keys, weights=probs, k=1)[0]


def generate_title_history(consultant_id, title_ids):
    """
    Generate 1-3 title history rows for a consultant.
    
    Returns list of tuples: (ConsultantID, TitleID, StartDate, EndDate, Salary)
    """
    # Determine number of promotions (0, 1, or 2)
    num_promos = random.choices([0, 1, 2], weights=[0.34, 0.33, 0.33], k=1)[0]
    
    # Pick initial title
    initial_title_id = weighted_choice(INITIAL_TITLE_WEIGHTS)
    
    # Ensure we can actually promote (title must exist at higher levels)
    max_title_id = max(title_ids)
    # Cap promotions so we don't exceed available titles
    num_promos = min(num_promos, max_title_id - initial_title_id)
    num_promos = max(num_promos, 0)
    
    rows = []
    current_title_id = initial_title_id
    
    for i in range(num_promos + 1):
        is_last_row = (i == num_promos)
        
        if i == 0:
            # First row: random start date
            start_date = random_first_of_month(DATE_START, datetime(2025, 1, 1))
        else:
            # Subsequent rows: start where previous ended
            start_date = rows[-1][3]  # Previous EndDate
            if start_date is None:
                # Shouldn't happen for non-last rows, but safeguard
                break
        
        # Determine end date
        if is_last_row:
            # Last row: 75% chance of NULL (still active), 25% chance of end date
            if random.random() < 0.75:
                end_date = None
            else:
                months_ahead = random.randint(6, 24)
                end_date = first_of_month(start_date + relativedelta(months=months_ahead))
                if end_date > DATE_END:
                    end_date = DATE_END
        else:
            # Non-last rows: always have an end date
            months_ahead = random.randint(6, 24)
            end_date = first_of_month(start_date + relativedelta(months=months_ahead))
            if end_date > DATE_END:
                end_date = DATE_END
        
        salary = generate_salary(current_title_id)
        
        rows.append((
            consultant_id,
            current_title_id,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d') if end_date else None,
            salary
        ))
        
        # Promote for next row
        current_title_id = min(current_title_id + 1, max_title_id)
    
    return rows


def main():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        print("Please generate the database first, then run this script.")
        return
    
    random.seed(RANDOM_SEED)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all consultant IDs
    try:
        cursor.execute("SELECT ConsultantID FROM Consultant")
        consultant_ids = [row[0] for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        # Try with lowercase
        cursor.execute("SELECT consultantid FROM consultant")
        consultant_ids = [row[0] for row in cursor.fetchall()]
    
    if not consultant_ids:
        print("No consultants found in database.")
        conn.close()
        return
    
    # Get all title IDs
    try:
        cursor.execute("SELECT TitleID FROM Title")
        title_ids = [row[0] for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        cursor.execute("SELECT titleid FROM title")
        title_ids = [row[0] for row in cursor.fetchall()]
    
    if not title_ids:
        print("No titles found in database. Using default IDs 1-6.")
        title_ids = list(range(1, 7))
    
    # Update TITLE_SALARY to use actual title IDs from DB
    actual_salary_map = {}
    sorted_ids = sorted(title_ids)
    default_salaries = list(TITLE_SALARY.values())
    for i, tid in enumerate(sorted_ids):
        if i < len(default_salaries):
            actual_salary_map[tid] = default_salaries[i]
        else:
            actual_salary_map[tid] = (200_000, 20_000)  # Default for extra titles
    
    # Update weights to use actual title IDs
    actual_weights = {}
    default_weights = list(INITIAL_TITLE_WEIGHTS.values())
    for i, tid in enumerate(sorted_ids):
        if i < len(default_weights):
            actual_weights[tid] = default_weights[i]
        else:
            actual_weights[tid] = 0.05
    
    # Temporarily replace module-level dicts
    global TITLE_SALARY, INITIAL_TITLE_WEIGHTS
    TITLE_SALARY = actual_salary_map
    INITIAL_TITLE_WEIGHTS = actual_weights
    
    # Clear existing data
    try:
        cursor.execute("DELETE FROM Consultant_Title_History")
    except sqlite3.OperationalError:
        pass  # Table might not exist yet
    
    # Generate title history for each consultant
    all_rows = []
    for cid in consultant_ids:
        rows = generate_title_history(cid, sorted_ids)
        all_rows.extend(rows)
    
    # Insert rows
    # Check table structure to determine insert format
    try:
        cursor.execute("PRAGMA table_info(Consultant_Title_History)")
        columns = [row[1] for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        columns = ['id', 'ConsultantID', 'TitleID', 'StartDate', 'EndDate', 'Salary', 'event_type']
    
    for idx, (consultant_id, title_id, start_date, end_date, salary) in enumerate(all_rows, 1):
        if 'id' in columns and 'event_type' in columns:
            cursor.execute(
                "INSERT INTO Consultant_Title_History (id, ConsultantID, TitleID, StartDate, EndDate, Salary, event_type) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (idx, consultant_id, title_id, start_date, end_date, salary, 'title_assignment')
            )
        elif 'id' in columns:
            cursor.execute(
                "INSERT INTO Consultant_Title_History (id, ConsultantID, TitleID, StartDate, EndDate, Salary) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (idx, consultant_id, title_id, start_date, end_date, salary)
            )
        else:
            cursor.execute(
                "INSERT INTO Consultant_Title_History (ConsultantID, TitleID, StartDate, EndDate, Salary) "
                "VALUES (?, ?, ?, ?, ?)",
                (consultant_id, title_id, start_date, end_date, salary)
            )
    
    conn.commit()
    conn.close()
    
    print(f"Generated {len(all_rows)} title history records for {len(consultant_ids)} consultants.")
    print(f"  Average records per consultant: {len(all_rows) / len(consultant_ids):.1f}")
    
    # Print distribution summary
    promo_counts = {}
    current_cid = None
    count = 0
    for cid, *_ in all_rows:
        if cid != current_cid:
            if current_cid is not None:
                promo_counts[count] = promo_counts.get(count, 0) + 1
            current_cid = cid
            count = 1
        else:
            count += 1
    if current_cid is not None:
        promo_counts[count] = promo_counts.get(count, 0) + 1
    
    print(f"  Distribution of rows per consultant: {dict(sorted(promo_counts.items()))}")


if __name__ == '__main__':
    main()
