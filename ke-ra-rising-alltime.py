import swisseph as swe
from datetime import datetime, timedelta, timezone
import pytz
from tabulate import tabulate

# Set path to ephemeris files (adjust if needed)
swe.set_ephe_path(r'N:\swisseph\ephe')

# # Location (example: Delhi)
# lat, lon = 28.6139, 77.2090

# Location (Chicago)
lat, lon = 41.8781, -87.6298


# Define the start and end date for the month (UTC-aware)
start = datetime(2025, 5, 1, 0, 0, tzinfo=timezone.utc)
end = datetime(2025, 6, 30, 23, 59, tzinfo=timezone.utc)

# Timezones to display
zones = {
    'London': pytz.timezone('Europe/London'),
    'Chicago': pytz.timezone('America/Chicago'),
    'Sydney': pytz.timezone('Australia/Sydney'),
    'India': pytz.timezone('Asia/Kolkata')
}

# Get Lahiri ayanamsha (Vedic)
def get_ayanamsha(jd):
    return swe.get_ayanamsa(jd)

# Convert tropical longitude to sidereal
def sidereal_longitude(tropical_long, jd):
    ayan = get_ayanamsha(jd)
    sidereal = tropical_long - ayan
    if sidereal < 0:
        sidereal += 360
    return sidereal

# Check if two angles are within orb degrees (default 1°)
def is_within_orb(angle1, angle2, orb=1.0):
    diff = abs(angle1 - angle2)
    diff = min(diff, 360 - diff)
    return diff <= orb

# Loop through the month in 10-minute steps
current = start
results = []

while current <= end:
    jd = swe.julday(current.year, current.month, current.day, current.hour + current.minute/60)
    cusps, ascmc = swe.houses(jd, lat, lon, b'P')
    asc_tropical = ascmc[0]
    asc_sidereal = sidereal_longitude(asc_tropical, jd)
    rahu_tropical, _ = swe.calc_ut(jd, swe.MEAN_NODE)
    rahu_long = rahu_tropical[0]
    rahu_sidereal = sidereal_longitude(rahu_long, jd)
    ketu_sidereal = (rahu_sidereal + 180) % 360
    if is_within_orb(asc_sidereal, rahu_sidereal):
        results.append((current, 'Rahu'))
    if is_within_orb(asc_sidereal, ketu_sidereal):
        results.append((current, 'Ketu'))
    current += timedelta(minutes=10)

# Convert UTC datetime to all specified timezones and prepare table rows
table_rows = []
for dt, node in results:
    row = [
        dt.strftime('%Y-%m-%d %H:%M UTC'),
        node
    ]
    for zone_name, tz in zones.items():
        local_dt = dt.astimezone(tz)
        row.append(local_dt.strftime('%Y-%m-%d %H:%M %Z'))
    table_rows.append(row)

# Table headers
headers = ['UTC', 'Node'] + list(zones.keys())

# Display as table (all rows)
print(tabulate(table_rows, headers=headers, tablefmt='grid'))
