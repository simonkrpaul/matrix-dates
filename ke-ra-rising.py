import swisseph as swe
from datetime import datetime, timedelta

# Set path to ephemeris files (adjust if needed)
# swe.set_ephe_path('/usr/share/ephe')
swe.set_ephe_path(r'N:\swisseph\ephe')

# Location (example: Delhi)
lat, lon = 28.6139, 77.2090

# Define the start and end date for the month
start = datetime(2025, 5, 1, 0, 0)
end = datetime(2025, 6, 30, 23, 59)

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
    # Ascendant (Lagna) in tropical
    cusps, ascmc = swe.houses(jd, lat, lon, b'P')
    asc_tropical = ascmc[0]  # Ascendant degree as float
    # Convert Ascendant to sidereal
    asc_sidereal = sidereal_longitude(asc_tropical, jd)
    # Rahu (Mean Node) longitude (tropical)
    rahu_tropical, _ = swe.calc_ut(jd, swe.MEAN_NODE)
    rahu_long = rahu_tropical[0]  # FIX: get the longitude as a float
    rahu_sidereal = sidereal_longitude(rahu_long, jd)
    # Ketu is always opposite Rahu
    ketu_sidereal = (rahu_sidereal + 180) % 360
    # Check conjunctions
    if is_within_orb(asc_sidereal, rahu_sidereal):
        results.append((current.strftime('%Y-%m-%d %H:%M'), 'Rahu'))
    if is_within_orb(asc_sidereal, ketu_sidereal):
        results.append((current.strftime('%Y-%m-%d %H:%M'), 'Ketu'))
    current += timedelta(minutes=10)


# Print results
for dt, node in results:
    print(f"{dt}: {node} rising")
