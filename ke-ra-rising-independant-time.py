import swisseph as swe
from datetime import datetime, timedelta, timezone
import pytz
from tabulate import tabulate

# Set ephemeris path
swe.set_ephe_path(r'N:\swisseph\ephe')

# Define locations with lat, lon, and timezone
locations = {
    'London': {'lat': 51.5074, 'lon': -0.1278, 'tz': pytz.timezone('Europe/London')},
    'Chicago': {'lat': 41.8781, 'lon': -87.6298, 'tz': pytz.timezone('America/Chicago')},
    'Sydney': {'lat': -33.8688, 'lon': 151.2093, 'tz': pytz.timezone('Australia/Sydney')},
    'India': {'lat': 28.6139, 'lon': 77.2090, 'tz': pytz.timezone('Asia/Kolkata')}
}

# Define UTC start and end datetime
start = datetime(2025, 5, 1, 0, 0, tzinfo=timezone.utc)
end = datetime(2025, 7, 10, 23, 59, tzinfo=timezone.utc)

def get_ayanamsha(jd):
    return swe.get_ayanamsa(jd)

def sidereal_longitude(tropical_long, jd):
    ayan = get_ayanamsha(jd)
    sidereal = tropical_long - ayan
    if sidereal < 0:
        sidereal += 360
    return sidereal

def angle_diff(a, b):
    diff = a - b
    while diff < -180:
        diff += 360
    while diff > 180:
        diff -= 360
    return diff

results = []

for loc_name, loc in locations.items():
    prev_asc = None
    prev_rahu = None
    prev_ketu = None
    prev_time = None
    last_node = None  # Track last node detected to ensure alternation
    current = start
    while current <= end:
        jd = swe.julday(current.year, current.month, current.day, current.hour + current.minute/60)
        rahu_tropical, _ = swe.calc_ut(jd, swe.MEAN_NODE)
        rahu_long = rahu_tropical[0]
        rahu_sidereal = sidereal_longitude(rahu_long, jd)
        ketu_sidereal = (rahu_sidereal + 180) % 360

        cusps, ascmc = swe.houses(jd, loc['lat'], loc['lon'], b'P')
        asc_tropical = ascmc[0]
        asc_sidereal = sidereal_longitude(asc_tropical, jd)

        if prev_asc is not None:
            # Rahu crossing
            rahu_cross = (angle_diff(prev_asc, prev_rahu) * angle_diff(asc_sidereal, rahu_sidereal) < 0)
            # Ketu crossing
            ketu_cross = (angle_diff(prev_asc, prev_ketu) * angle_diff(asc_sidereal, ketu_sidereal) < 0)

            # Only record a crossing if it's not the same as the last detected node
            if rahu_cross and last_node != 'Rahu':
                local_time = current.astimezone(loc['tz'])
                results.append([loc_name, local_time.strftime('%Y-%m-%d %H:%M %Z'), 'Rahu'])
                last_node = 'Rahu'
            elif ketu_cross and last_node != 'Ketu':
                local_time = current.astimezone(loc['tz'])
                results.append([loc_name, local_time.strftime('%Y-%m-%d %H:%M %Z'), 'Ketu'])
                last_node = 'Ketu'

        prev_asc = asc_sidereal
        prev_rahu = rahu_sidereal
        prev_ketu = ketu_sidereal
        prev_time = current
        current += timedelta(minutes=1)

# Sort results by location and time
results.sort(key=lambda x: (x[0], x[1]))

# Display table
print(tabulate(results, headers=['Location', 'Local Time', 'Node'], tablefmt='grid'))
