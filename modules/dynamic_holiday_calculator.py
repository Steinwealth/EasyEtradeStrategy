#!/usr/bin/env python3
"""
Dynamic Holiday Calculator
=========================

Future-proof US market holiday calculator that works without external libraries.
Calculates holidays for any year using mathematical algorithms.
"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple

def calculate_easter(year: int) -> date:
    """Calculate Easter Sunday for a given year using the Anonymous Gregorian algorithm"""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    n = (h + l - 7 * m + 114) // 31
    p = (h + l - 7 * m + 114) % 31
    return date(year, n, p + 1)

def get_nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> date:
    """Get the nth occurrence of a weekday in a given month"""
    # weekday: 0=Monday, 1=Tuesday, ..., 6=Sunday
    first_day = date(year, month, 1)
    days_ahead = weekday - first_day.weekday()
    if days_ahead < 0:
        days_ahead += 7
    first_weekday = first_day + timedelta(days=days_ahead)
    return first_weekday + timedelta(weeks=n-1)

def calculate_us_holidays(year: int) -> List[Tuple[date, str]]:
    """Calculate all US market holidays for a given year"""
    holidays = []
    
    # Fixed holidays
    holidays.extend([
        (date(year, 1, 1), "New Year's Day"),
        (date(year, 7, 4), "Independence Day"),
        (date(year, 12, 25), "Christmas Day"),
    ])
    
    # Variable holidays
    # Martin Luther King Jr. Day - 3rd Monday of January
    mlk_day = get_nth_weekday_of_month(year, 1, 0, 3)  # 0 = Monday
    holidays.append((mlk_day, "Martin Luther King Jr. Day"))
    
    # Presidents' Day - 3rd Monday of February
    presidents_day = get_nth_weekday_of_month(year, 2, 0, 3)  # 0 = Monday
    holidays.append((presidents_day, "Presidents' Day"))
    
    # Good Friday - Friday before Easter Sunday
    easter = calculate_easter(year)
    good_friday = easter - timedelta(days=2)
    holidays.append((good_friday, "Good Friday"))
    
    # Memorial Day - Last Monday of May
    # Find the last day of May, then work backwards to the last Monday
    last_day_of_may = date(year, 6, 1) - timedelta(days=1)
    days_back = last_day_of_may.weekday()  # 0=Monday, 6=Sunday
    memorial_day = last_day_of_may - timedelta(days=days_back)
    holidays.append((memorial_day, "Memorial Day"))
    
    # Juneteenth - June 19th (fixed since 2021)
    holidays.append((date(year, 6, 19), "Juneteenth"))
    
    # Labor Day - 1st Monday of September
    labor_day = get_nth_weekday_of_month(year, 9, 0, 1)  # 0 = Monday
    holidays.append((labor_day, "Labor Day"))
    
    # Thanksgiving Day - 4th Thursday of November
    thanksgiving = get_nth_weekday_of_month(year, 11, 3, 4)  # 3 = Thursday
    holidays.append((thanksgiving, "Thanksgiving Day"))
    
    return sorted(holidays)

def calculate_early_close_days(year: int) -> List[Tuple[date, str, str]]:
    """Calculate early close days for a given year"""
    early_close_days = []
    
    # Independence Day Eve - July 3rd (if July 4th is not a weekend)
    july_4th = date(year, 7, 4)
    if july_4th.weekday() == 0:  # Monday
        # If July 4th is Monday, July 3rd (Sunday) is early close
        early_close_days.append((date(year, 7, 3), "Independence Day Eve", "13:00"))
    elif july_4th.weekday() in [1, 2, 3, 4]:  # Tuesday through Friday
        # If July 4th is a weekday, July 3rd is early close
        early_close_days.append((date(year, 7, 3), "Independence Day Eve", "13:00"))
    
    # Black Friday - Day after Thanksgiving
    thanksgiving = get_nth_weekday_of_month(year, 11, 3, 4)  # 4th Thursday
    black_friday = thanksgiving + timedelta(days=1)
    early_close_days.append((black_friday, "Black Friday", "13:00"))
    
    # Christmas Eve - December 24th (if December 25th is not a weekend)
    christmas = date(year, 12, 25)
    if christmas.weekday() == 0:  # Monday
        # If Christmas is Monday, December 24th (Sunday) is early close
        early_close_days.append((date(year, 12, 24), "Christmas Eve", "13:00"))
    elif christmas.weekday() in [1, 2, 3, 4]:  # Tuesday through Friday
        # If Christmas is a weekday, December 24th is early close
        early_close_days.append((date(year, 12, 24), "Christmas Eve", "13:00"))
    
    return sorted(early_close_days)

def get_holidays_for_year(year: int) -> Dict:
    """Get all holidays and early close days for a specific year"""
    holidays = calculate_us_holidays(year)
    early_close = calculate_early_close_days(year)
    
    return {
        "year": year,
        "holidays": [(d.strftime("%Y-%m-%d"), name) for d, name in holidays],
        "early_close_days": [(d.strftime("%Y-%m-%d"), name, time) for d, name, time in early_close],
        "total_holidays": len(holidays),
        "total_early_close_days": len(early_close)
    }

if __name__ == "__main__":
    # Test the calculator
    current_year = datetime.now().year
    print(f"Testing holiday calculator for {current_year}...")
    
    result = get_holidays_for_year(current_year)
    print(f"Holidays for {current_year}:")
    for date_str, name in result["holidays"]:
        print(f"  {date_str}: {name}")
    
    print(f"\nEarly close days for {current_year}:")
    for date_str, name, time in result["early_close_days"]:
        print(f"  {date_str}: {name} ({time})")
