import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import swisseph as swe
from tkcalendar import DateEntry


# Path to Swiss Ephemeris data files
# Windows: r'C:\path\to\ephe'
# EPHE_PATH = r'N:\swisseph\ephe'  # Change if needed
# MacOS/Linux: adjust path as needed
EPHE_PATH = r'/Users/rajanpsi/repos/personal/swisseph/ephe'  # Change if needed

# Planets: All planets, North Node, South Node, Ascendant
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
    ("North Node", swe.MEAN_NODE),
    ("South Node", "Ketu"),  # Special case handled in code
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
    
    # Set sidereal mode based on ayanamsa type
    swe.set_sid_mode(ayanamsa_type, 0, 0)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL

    if planet == "Ketu":
        # South Node is always opposite to North Node (Mean Node)
        north_node_pos = swe.calc_ut(jd, swe.MEAN_NODE, flags)
        north_node_lon = unwrap_longitude(north_node_pos)
        return (north_node_lon + 180.0) % 360.0

    elif planet == "ASC":
        # Ascendant needs latitude, longitude, and ayanamsa
        if latitude is None or longitude is None:
            raise ValueError("Latitude and Longitude required for Ascendant calculation")
        
        # First calculate houses in tropical zodiac
        cusps, ascmc = swe.houses(jd, latitude, longitude, b'P')  # Placidus houses
        asc = ascmc[0]
        
        # Adjust for ayanamsa to get sidereal position
        ayanamsa_value = swe.get_ayanamsa_ut(jd)
        asc = (asc - ayanamsa_value) % 360
        return asc

    else:
        # For regular planets and Rahu
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
            
        # Get angle value from radio buttons or custom entry
        if aspect_var.get() == 'custom':
            angle = float(custom_angle_var.get())
        else:
            angle = float(aspect_var.get())

        # For conjunction, treat angle=0 as special case
        is_conjunction = False
        if angle == 0:
            is_conjunction = True
            angle = 1e-6  # Use a very small angle to avoid division by zero

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
    prev_time = None
    prev_vals = None
    last_output_aspect = None  # for non-conjunctions
    last_output_time = None    # for conjunctions
    # Use finer time step if Ascendant is involved in a conjunction
    step = timedelta(hours=1)
    if is_conjunction and len(selected_planet_indexes) == 2:
        asc_idx = [i for i, (_, pid) in enumerate(PLANETS) if pid == "ASC"]
        if any(idx in selected_planet_indexes for idx in asc_idx):
            step = timedelta(minutes=5)
    d = start_date_dt
    dt = datetime(d.year, d.month, d.day, hour_local, min_local)
    dt_end = datetime(end_date_dt.year, end_date_dt.month, end_date_dt.day, hour_local, min_local)

    # Aspect name logic
    def get_aspect_name(angle, aspect_var_val):
        if aspect_var_val == '0':
            return 'Conjunction (0°)'
        elif aspect_var_val == '180':
            return 'Opposition (180°)'
        elif aspect_var_val == '120':
            return 'Trine (120°)'
        elif aspect_var_val == '90':
            return 'Square (90°)'
        elif aspect_var_val == 'custom':
            return f'Custom ({float(custom_angle_var.get()):.0f}°)'
        else:
            return f'Custom ({angle:.0f}°)'

    aspect_name = get_aspect_name(angle, aspect_var.get())

    while dt <= dt_end:
        ut_dt = dt - timedelta(hours=timezone_offset)
        year, month, day = ut_dt.year, ut_dt.month, ut_dt.day
        hour_ut = ut_dt.hour + ut_dt.minute / 60.0

        longs = []
        try:
            for i in selected_planet_indexes:
                pname, planet_id = PLANETS[i]
                lon = None
                if planet_id == "Ketu":
                    # Ketu is always opposite to Rahu (Mean Node)
                    rahu_lon = calc_sidereal_longitude(year, month, day, hour_ut, swe.MEAN_NODE, ayanamsa_type)
                    lon = (rahu_lon + 180.0) % 360.0
                elif planet_id == "ASC":
                    lon = calc_sidereal_longitude(year, month, day, hour_ut, planet_id, ayanamsa_type, latitude, longitude)
                else:
                    lon = calc_sidereal_longitude(year, month, day, hour_ut, planet_id, ayanamsa_type)
                longs.append(lon)
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Error on date {dt.strftime('%Y-%m-%d %H:%M')} UTC: {e}")
            return

        # Determine suppression window for conjunctions
        suppression_seconds = 12 * 3600  # default 12 hours
        if is_conjunction and len(selected_planet_indexes) == 2:
            asc_idx = [i for i, (_, pid) in enumerate(PLANETS) if pid == "ASC"]
            if any(idx in selected_planet_indexes for idx in asc_idx):
                suppression_seconds = 30 * 60  # 30 minutes if Ascendant involved

        store_row = False
        interp_time = None
        interp_longs = None
        current_aspect = None
        if len(longs) == 1:
            # For single planet, look for aspect crossing (modulo angle wraps from >0 to <0)
            aspect_num = int(longs[0] // angle) if not is_conjunction else 0
            mod_angle = longs[0] % angle if not is_conjunction else longs[0]
            if prev_vals is not None:
                prev_mod = prev_vals[0] % angle if not is_conjunction else prev_vals[0]
                prev_aspect_num = int(prev_vals[0] // angle) if not is_conjunction else 0
                # Crossing zero (from above to below)
                if (not is_conjunction and ((prev_mod > 0 and mod_angle < 1) or (prev_mod < angle-1 and mod_angle < 1))) or (is_conjunction and abs(mod_angle) < 1 and abs(prev_mod) > 1):
                    current_aspect = aspect_num
                    if not is_conjunction:
                        if last_output_aspect != current_aspect:
                            frac = prev_mod / (prev_mod - mod_angle) if (prev_mod - mod_angle) != 0 else 0
                            interp_time = prev_time + (dt - prev_time) * frac
                            interp_longs = [prev_vals[0] + (longs[0] - prev_vals[0]) * frac]
                            store_row = True
                            last_output_aspect = current_aspect
                    else:
                        # For conjunction, only suppress if last event was within suppression_seconds
                        if interp_time is None:
                            frac = prev_mod / (prev_mod - mod_angle) if (prev_mod - mod_angle) != 0 else 0
                            interp_time = prev_time + (dt - prev_time) * frac
                            interp_longs = [prev_vals[0] + (longs[0] - prev_vals[0]) * frac]
                        if last_output_time is None or (interp_time - last_output_time).total_seconds() > suppression_seconds:
                            store_row = True
                            last_output_time = interp_time
            prev_time = dt
            prev_vals = longs.copy()
        elif len(longs) == 2:
            # For two planets, look for aspect crossing (difference crosses target angle)
            diff = abs((longs[0] - longs[1] + 360) % 360)
            diff = min(diff, 360 - diff)
            aspect_num = int(diff // angle) if not is_conjunction else 0
            if prev_vals is not None:
                prev_diff = abs((prev_vals[0] - prev_vals[1] + 360) % 360)
                prev_diff = min(prev_diff, 360 - prev_diff)
                prev_aspect_num = int(prev_diff // angle) if not is_conjunction else 0
                # Crossing the target angle or conjunction
                if (not is_conjunction and (prev_diff - angle) * (diff - angle) < 0) or (is_conjunction and diff < 1 and prev_diff > 1):
                    current_aspect = aspect_num
                    if not is_conjunction:
                        if last_output_aspect != current_aspect:
                            frac = (angle - prev_diff) / (diff - prev_diff) if (diff - prev_diff) != 0 else 0
                            interp_time = prev_time + (dt - prev_time) * frac
                            interp_longs = [prev_vals[0] + (longs[0] - prev_vals[0]) * frac,
                                            prev_vals[1] + (longs[1] - prev_vals[1]) * frac]
                            store_row = True
                            last_output_aspect = current_aspect
                    else:
                        # For conjunction, only suppress if last event was within suppression_seconds
                        if interp_time is None:
                            frac = prev_diff / (prev_diff - diff) if (prev_diff - diff) != 0 else 0
                            interp_time = prev_time + (dt - prev_time) * frac
                            interp_longs = [prev_vals[0] + (longs[0] - prev_vals[0]) * frac,
                                            prev_vals[1] + (longs[1] - prev_vals[1]) * frac]
                        if last_output_time is None or (interp_time - last_output_time).total_seconds() > suppression_seconds:
                            store_row = True
                            last_output_time = interp_time
            prev_time = dt
            prev_vals = longs.copy()

        if store_row:
            planets_str = ', '.join([PLANETS[i][0] for i in selected_planet_indexes])
            if interp_time is not None and interp_longs is not None:
                dt_str = interp_time.strftime('%Y-%m-%d %H:%M UTC')
                longs_str = ', '.join([f"{v:.2f}" for v in interp_longs])
            else:
                dt_str = dt.strftime('%Y-%m-%d %H:%M UTC')
                longs_str = ', '.join([f"{v:.2f}" for v in longs])
            # Add aspect name and degree column
            tree.insert('', 'end', values=(dt_str, planets_str, longs_str, aspect_name))
            last_output_aspect = current_aspect

        dt += step


# --- Tkinter UI ---

root = tk.Tk()
root.title("Sidereal Zodiac Date Generator (Swiss Ephemeris)")

# Start and End Date with DateEntry
ttk.Label(root, text="Start Date:").grid(row=0, column=0, sticky='w')
start_date_entry = DateEntry(root, width=12, background='darkblue', foreground='white', borderwidth=2)
start_date_entry.set_date(datetime(2025, 1, 10))
start_date_entry.grid(row=0, column=1, padx=5, pady=2)

ttk.Label(root, text="End Date:").grid(row=1, column=0, sticky='w')
end_date_entry = DateEntry(root, width=12, background='darkblue', foreground='white', borderwidth=2)
end_date_entry.set_date(datetime(2025, 12, 30))
end_date_entry.grid(row=1, column=1, padx=5, pady=2)

# Time
ttk.Label(root, text='Local Time (24h:Min):').grid(row=2, column=0, sticky='w')
hour_var = tk.StringVar(value='12')
min_var = tk.StringVar(value='00')
ttk.Entry(root, textvariable=hour_var, width=3).grid(row=2, column=1, sticky='w')
ttk.Entry(root, textvariable=min_var, width=3).grid(row=2, column=2, sticky='w')

# Timezone Offset
ttk.Label(root, text='Timezone Offset (hours, e.g. 0 for UTC, 10 or -5):').grid(row=3, column=0, sticky='w')
timezone_var = tk.StringVar(value='0')  # Default to UTC
ttk.Entry(root, textvariable=timezone_var, width=6).grid(row=3, column=1, sticky='w')

# Latitude & Longitude for Ascendant calculation
ttk.Label(root, text='Latitude (deg):').grid(row=4, column=0, sticky='w')
latitude_var = tk.StringVar(value='12.9667')
ttk.Entry(root, textvariable=latitude_var, width=10).grid(row=4, column=1, sticky='w')

ttk.Label(root, text='Longitude (deg):').grid(row=5, column=0, sticky='w')
longitude_var = tk.StringVar(value='77.5667')
ttk.Entry(root, textvariable=longitude_var, width=10).grid(row=5, column=1, sticky='w')

# Planet selections (all planets, North Node, South Node, Ascendant)
ttk.Label(root, text="Select Planets/Points:").grid(row=6, column=0, sticky='w')
planet_vars = [tk.IntVar(value=0) for _ in PLANETS]
for i, (pname, _) in enumerate(PLANETS):
    ttk.Checkbutton(root, text=pname, variable=planet_vars[i]).grid(row=7 + i // 3, column=1 + i % 3, sticky='w')
planet_vars[0].set(1)  # Default select Sun

# Aspect selection (radio buttons for common aspects + custom)
ttk.Label(root, text="Aspect:").grid(row=13, column=0, sticky='w')
aspect_var = tk.StringVar(value='90')  # Default to Square

# Define common aspects
aspects = [
    ("Conjunction (0°)", "0"),
    ("Opposition (180°)", "180"),
    ("Trine (120°)", "120"),
    ("Square (90°)", "90"),
]

# Create radio buttons for each aspect
for i, (label, val) in enumerate(aspects):
    ttk.Radiobutton(root, text=label, variable=aspect_var, value=val).grid(row=13, column=1 + i, sticky='w')

# Custom angle option
ttk.Label(root, text="Custom (deg):").grid(row=13, column=5, sticky='w')
custom_angle_var = tk.StringVar(value='45')
ttk.Entry(root, textvariable=custom_angle_var, width=4).grid(row=13, column=6, sticky='w')
ttk.Radiobutton(root, text="Use Custom", variable=aspect_var, value='custom').grid(row=13, column=7, sticky='w')

# Ayanamsa selection
ttk.Label(root, text="Sidereal Zodiac (Ayanamsa):").grid(row=14, column=0, sticky='w')
ay_var = tk.IntVar(value=0)
for i, (ayname, _) in enumerate(AYANAMSAS):
    ttk.Radiobutton(root, text=ayname, variable=ay_var, value=i).grid(row=14, column=1 + i, sticky='w')


# Export to TXT function
from tkinter import filedialog
def export_to_txt():
    # Ask user for file path
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if not file_path:
        return
    # Get column headers
    headers = [tree.heading(col)["text"] for col in tree["columns"]]
    # Get all rows
    rows = []
    for item in tree.get_children():
        values = tree.item(item)["values"]
        rows.append(values)
    # Write to file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\t".join(headers) + "\n")
        for row in rows:
            f.write("\t".join(str(v) for v in row) + "\n")

# Generate and Export buttons
ttk.Button(root, text="Generate Dates", command=generate_dates).grid(row=15, column=0, pady=10, sticky='w')
ttk.Button(root, text="Export to TXT", command=export_to_txt).grid(row=15, column=1, pady=10, sticky='w')

# Output table with scrollbar (Treeview)
tbl_frame = ttk.Frame(root)
tbl_frame.grid(row=16, column=0, columnspan=4, sticky='nsew')

# Add Aspect column
tree = ttk.Treeview(tbl_frame, columns=("Date", "Planets", "Longitudes", "Aspect"), show="headings", height=15)
tree.heading("Date", text="Date")
tree.heading("Planets", text="Planet(s)")
tree.heading("Longitudes", text="Longitude(s)")
tree.heading("Aspect", text="Aspect")
tree.column("Date", width=100, anchor='w')
tree.column("Planets", width=150, anchor='w')
tree.column("Longitudes", width=250, anchor='w')
tree.column("Aspect", width=120, anchor='w')
tree.pack(side="left", fill="both", expand=True)

scrollbar = ttk.Scrollbar(tbl_frame, orient="vertical", command=tree.yview)
scrollbar.pack(side="right", fill="y")
tree.configure(yscrollcommand=scrollbar.set)

# Configure root to expand table frame with resizing
root.grid_rowconfigure(16, weight=1)
root.grid_columnconfigure(3, weight=1)

root.mainloop()
