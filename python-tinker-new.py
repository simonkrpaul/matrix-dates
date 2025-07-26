import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import swisseph as swe
from tkcalendar import DateEntry


# Path to Swiss Ephemeris data files
EPHE_PATH = r'N:\swisseph\ephe'  # Change if needed


# Extended Planets with True Node, Ketu (South Node), Ascendant
PLANETS = [
    ("Sun", swe.SUN),
    ("Moon", swe.MOON),
    ("Mercury", swe.MERCURY),
    ("Venus", swe.VENUS),
    ("Mars", swe.MARS),
    ("Jupiter", swe.JUPITER),
    ("Saturn", swe.SATURN),
    ("Uranus", swe.URANUS),
    ("Neptune", swe.NEPTUNE),
    ("Pluto", swe.PLUTO),
    ("Mean Node (Rahu)", swe.MEAN_NODE),
    ("True Node (Rahu)", swe.TRUE_NODE),
    ("South Node (Ketu)", "Ketu"),  # Special case handled in code
    ("Ascendant (Rising)", "ASC"),  # Special case handled in code
]


AYANAMSAS = [
    ("Lahiri", swe.SIDM_LAHIRI),
    ("Raman", swe.SIDM_RAMAN),
    ("Krishnamurti", swe.SIDM_KRISHNAMURTI),
    ("Fagan/Bradley", swe.SIDM_FAGAN_BRADLEY),
]


def unwrap_longitude(pos):
    # Recursively unwrap nested tuples/lists to get float longitude
    val = pos[0]
    while isinstance(val, (tuple, list)):
        val = val[0]
    return float(val)


def calc_sidereal_longitude(year, month, day, hour_ut, planet, ayanamsa_type, latitude=None, longitude=None):
    jd = swe.julday(year, month, day, hour_ut)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL

    if planet == "Ketu":
        # Ketu is Opposite Mean Node
        rahu_pos = swe.calc_ut(jd, swe.MEAN_NODE, flags)
        rahu_lon = unwrap_longitude(rahu_pos)
        ketu_lon = (rahu_lon + 180.0) % 360.0
        return ketu_lon

    elif planet == "ASC":
        # Ascendant needs latitude, longitude, and ayanamsa
        if latitude is None or longitude is None:
            raise ValueError("Latitude and Longitude required for Ascendant calculation")
        # Calculate houses
        cusps, ascmc = swe.houses(jd, latitude, longitude, b'P')  # Placidus houses
        asc = ascmc[0]
        # Adjust for ayanamsa if sidereal
        if ayanamsa_type != swe.SIDM_FAGAN_BRADLEY:  # generally adjust
            swe.set_sid_mode(ayanamsa_type, 0, 0)
            ayanamsa_value = swe.get_ayanamsa_ut(jd)
            asc = (asc - ayanamsa_value) % 360
        return asc

    else:
        pos = swe.calc_ut(jd, planet, flags)
        return unwrap_longitude(pos)


def generate_dates():
    try:
        # Get dates from DateEntry widgets (already datetime.date objects)
        start_date_dt = start_date_entry.get_date()
        end_date_dt = end_date_entry.get_date()

        hour_local = int(hour_var.get())
        min_local = int(min_var.get())
        timezone_offset = float(timezone_var.get())  # In hours, e.g. 10 or -5

        selected_planet_indexes = [i for i, v in enumerate(planet_vars) if v.get()]
        if not selected_planet_indexes:
            messagebox.showerror("Error", "Select at least one planet.")
            return

        angle = float(angle_var.get())
        ayanamsa_type = AYANAMSAS[ay_var.get()][1]

        latitude = float(latitude_var.get())
        longitude = float(longitude_var.get())

    except Exception as e:
        messagebox.showerror("Input Error", str(e))
        return

    swe.set_ephe_path(EPHE_PATH)
    swe.set_sid_mode(ayanamsa_type, 0, 0)

    # Clear previous tree items
    for row in tree.get_children():
        tree.delete(row)

    prev_longs = {}
    d = start_date_dt
    while d <= end_date_dt:
        # Convert local time to UT datetime
        local_dt = datetime(d.year, d.month, d.day, hour_local, min_local)
        ut_dt = local_dt - timedelta(hours=timezone_offset)
        year, month, day = ut_dt.year, ut_dt.month, ut_dt.day
        hour_ut = ut_dt.hour + ut_dt.minute / 60.0

        longs = []
        try:
            for i in selected_planet_indexes:
                pname, planet_id = PLANETS[i]
                lon = None
                if planet_id == "Ketu" or planet_id == "ASC":
                    lon = calc_sidereal_longitude(year, month, day, hour_ut, planet_id,
                                                 ayanamsa_type, latitude, longitude)
                else:
                    lon = calc_sidereal_longitude(year, month, day, hour_ut, planet_id, ayanamsa_type)
                longs.append(lon)
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Error on date {d.strftime('%Y-%m-%d')}: {e}")
            return

        store_row = False
        if len(longs) == 1:
            if not prev_longs or abs(longs[0] - prev_longs.get(0, 0)) >= angle:
                store_row = True
        else:
            diff = abs(longs[0] - longs[1])
            diff = min(diff, 360 - diff)
            if abs(diff - angle) < 1:  # Within 1 degree
                store_row = True

        if store_row:
            planets_str = ', '.join([PLANETS[i][0] for i in selected_planet_indexes])
            longs_str = ', '.join([f"{v:.2f}" for v in longs])
            tree.insert('', 'end', values=(d.strftime('%Y-%m-%d'), planets_str, longs_str))
            prev_longs = {i: l for i, l in enumerate(longs)}

        d += timedelta(days=1)


# --- Tkinter UI ---

root = tk.Tk()
root.title("Sidereal Zodiac Date Generator (Swiss Ephemeris)")

# Start and End Date with DateEntry
ttk.Label(root, text="Start Date:").grid(row=0, column=0, sticky='w')
start_date_entry = DateEntry(root, width=12, background='darkblue', foreground='white', borderwidth=2)
start_date_entry.set_date(datetime(2025, 7, 26))
start_date_entry.grid(row=0, column=1, padx=5, pady=2)

ttk.Label(root, text="End Date:").grid(row=1, column=0, sticky='w')
end_date_entry = DateEntry(root, width=12, background='darkblue', foreground='white', borderwidth=2)
end_date_entry.set_date(datetime(2025, 8, 5))
end_date_entry.grid(row=1, column=1, padx=5, pady=2)

# Time
ttk.Label(root, text='Local Time (24h:Min):').grid(row=2, column=0, sticky='w')
hour_var = tk.StringVar(value='12')
min_var = tk.StringVar(value='00')
ttk.Entry(root, textvariable=hour_var, width=3).grid(row=2, column=1, sticky='w')
ttk.Entry(root, textvariable=min_var, width=3).grid(row=2, column=2, sticky='w')

# Timezone Offset
ttk.Label(root, text='Timezone Offset (hours, e.g. 10 or -5):').grid(row=3, column=0, sticky='w')
timezone_var = tk.StringVar(value='10')  # AEST default (UTC+10)
ttk.Entry(root, textvariable=timezone_var, width=6).grid(row=3, column=1, sticky='w')

# Latitude & Longitude for Ascendant calculation
ttk.Label(root, text='Latitude (deg):').grid(row=4, column=0, sticky='w')
latitude_var = tk.StringVar(value='12.9667')
ttk.Entry(root, textvariable=latitude_var, width=10).grid(row=4, column=1, sticky='w')

ttk.Label(root, text='Longitude (deg):').grid(row=5, column=0, sticky='w')
longitude_var = tk.StringVar(value='77.5667')
ttk.Entry(root, textvariable=longitude_var, width=10).grid(row=5, column=1, sticky='w')

# Planet selections
ttk.Label(root, text="Select Planets:").grid(row=6, column=0, sticky='w')
planet_vars = [tk.IntVar(value=0) for _ in PLANETS]
for i, (pname, _) in enumerate(PLANETS):
    ttk.Checkbutton(root, text=pname, variable=planet_vars[i]).grid(row=7 + i // 3, column=1 + i % 3, sticky='w')
planet_vars[0].set(1)  # Default select Sun

# Angle difference
ttk.Label(root, text="Angle (deg):").grid(row=13, column=0, sticky='w')  # moved from 11 to 13
angle_var = tk.StringVar(value='90')
ttk.Entry(root, textvariable=angle_var, width=6).grid(row=13, column=1, sticky='w')

# Ayanamsa selection
ttk.Label(root, text="Sidereal Zodiac (Ayanamsa):").grid(row=14, column=0, sticky='w')
ay_var = tk.IntVar(value=0)
for i, (ayname, _) in enumerate(AYANAMSAS):
    ttk.Radiobutton(root, text=ayname, variable=ay_var, value=i).grid(row=14, column=1 + i, sticky='w')

# Generate button
ttk.Button(root, text="Generate Dates", command=generate_dates).grid(row=15, column=0, pady=10, sticky='w')

# Output table with scrollbar (Treeview)
tbl_frame = ttk.Frame(root)
tbl_frame.grid(row=16, column=0, columnspan=4, sticky='nsew')

tree = ttk.Treeview(tbl_frame, columns=("Date", "Planets", "Longitudes"), show="headings", height=15)
tree.heading("Date", text="Date")
tree.heading("Planets", text="Planet(s)")
tree.heading("Longitudes", text="Longitude(s)")
tree.column("Date", width=100, anchor='w')
tree.column("Planets", width=150, anchor='w')
tree.column("Longitudes", width=250, anchor='w')
tree.pack(side="left", fill="both", expand=True)

scrollbar = ttk.Scrollbar(tbl_frame, orient="vertical", command=tree.yview)
scrollbar.pack(side="right", fill="y")
tree.configure(yscrollcommand=scrollbar.set)

# Configure root to expand table frame with resizing
root.grid_rowconfigure(16, weight=1)
root.grid_columnconfigure(3, weight=1)

root.mainloop()
