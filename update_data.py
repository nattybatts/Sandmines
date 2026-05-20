#!/usr/bin/env python3
"""
Sand Finder — Data Update Script
=================================
Run this whenever you have fresh CSV exports from your data source.

Usage:
  python update_data.py

Place the three CSV files in the same folder as this script, with these names:
  - Well_Headers_past_3_years_Well_Headers.CSV
  - Permits_and_rigs_Permits_Table.CSV
  - Permits_and_rigs_Rigs.CSV

Output: overwrites the four files in data/
  - data/wells.json
  - data/permits.json
  - data/rigs.json
  - data/meta.json
"""

import pandas as pd
import json
import os
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(SCRIPT_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

WELLS_CSV   = os.path.join(SCRIPT_DIR, 'Well_Headers_past_3_years_Well_Headers.CSV')
PERMITS_CSV = os.path.join(SCRIPT_DIR, 'Permits_and_rigs_Permits_Table.CSV')
RIGS_CSV    = os.path.join(SCRIPT_DIR, 'Permits_and_rigs_Rigs.CSV')

STATUS_MAP = {'ACTIVE': 'A', 'DRILLED': 'D', 'DUC': 'U'}

def clean(v):
    if v is None: return ''
    s = str(v).strip()
    return '' if s in ('nan', 'None', 'NaN') else s

def save_json(obj, path):
    with open(path, 'w') as f:
        json.dump(obj, f, separators=(',', ':'))
    kb = os.path.getsize(path) / 1024
    print(f"  Wrote {os.path.basename(path):20s}  ({kb:.0f} KB)")

def check_file(path):
    if not os.path.exists(path):
        print(f"ERROR: File not found: {path}")
        sys.exit(1)
    print(f"  Found: {os.path.basename(path)}")

print(f"\n{'='*50}")
print(f"  Sand Finder Data Update — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print(f"{'='*50}\n")

print("Checking input files...")
check_file(WELLS_CSV)
check_file(PERMITS_CSV)
check_file(RIGS_CSV)

# ── Wells ─────────────────────────────────────────────────────────────────────
print("\nProcessing wells...")
wells_df = pd.read_csv(WELLS_CSV, usecols=[
    'Well Name', 'Operator Company Name', 'Well Status', 'State',
    'County/Parish', 'DI Basin', 'Target Formation',
    'Surface Hole Latitude (WGS84)', 'Surface Hole Longitude (WGS84)', 'Spud Date'
])
wells_df = wells_df.dropna(subset=['Surface Hole Latitude (WGS84)', 'Surface Hole Longitude (WGS84)'])

wells = []
for _, r in wells_df.iterrows():
    s = STATUS_MAP.get(clean(r['Well Status']).upper(), 'D')
    wells.append([
        s, clean(r['Operator Company Name']), clean(r['State']),
        clean(r['County/Parish']), clean(r['DI Basin']),
        clean(r['Target Formation']),
        round(float(r['Surface Hole Latitude (WGS84)']), 4),
        round(float(r['Surface Hole Longitude (WGS84)']), 4),
        clean(r['Well Name']),
        clean(r['Spud Date'])[:10]
    ])
print(f"  {len(wells):,} wells processed")

# ── Permits ───────────────────────────────────────────────────────────────────
print("\nProcessing permits...")
permits_df = pd.read_csv(PERMITS_CSV, usecols=[
    'State/Province', 'County/Parish', 'DI Basin', 'Operator Company Name',
    'Formation', 'Filed Date',
    'Surface Hole Latitude (WGS84)', 'Surface Hole Longitude (WGS84)',
    'Lease Name', 'Well Number'
])

permits = []
for _, r in permits_df.iterrows():
    name = (clean(r['Lease Name']) + ' ' + clean(r['Well Number'])).strip()
    permits.append([
        'P', clean(r['Operator Company Name']), clean(r['State/Province']),
        clean(r['County/Parish']), clean(r['DI Basin']),
        clean(r['Formation']),
        round(float(r['Surface Hole Latitude (WGS84)']), 4),
        round(float(r['Surface Hole Longitude (WGS84)']), 4),
        name,
        clean(r['Filed Date'])[:10]
    ])
print(f"  {len(permits):,} permits processed")

# ── Rigs ──────────────────────────────────────────────────────────────────────
print("\nProcessing rigs...")
rigs_df = pd.read_csv(RIGS_CSV, usecols=[
    'State/Province', 'County/Parish', 'DI Basin', 'Operator Company Name',
    'Contractor Name', 'Rig Name/Number',
    'Rig Latitude (WGS84)', 'Rig Longitude (WGS84)',
    'Formation', 'Spud Date'
])

rigs = []
for _, r in rigs_df.iterrows():
    rigs.append([
        'R', clean(r['Operator Company Name']), clean(r['State/Province']),
        clean(r['County/Parish']), clean(r['DI Basin']),
        clean(r['Formation']),
        round(float(r['Rig Latitude (WGS84)']), 4),
        round(float(r['Rig Longitude (WGS84)']), 4),
        clean(r['Rig Name/Number']),
        clean(r['Contractor Name'])
    ])
print(f"  {len(rigs):,} rigs processed")

# ── Meta (ops + states lists for filter dropdowns) ────────────────────────────
all_data = wells + permits + rigs
ops    = sorted(set(x[1] for x in all_data if x[1]))
states = sorted(set(x[2] for x in all_data if x[2]))
meta   = {'ops': ops, 'states': states, 'updated': datetime.now().strftime('%Y-%m-%d')}

# ── Write output files ────────────────────────────────────────────────────────
print("\nWriting data files...")
save_json(wells,   os.path.join(DATA_DIR, 'wells.json'))
save_json(permits, os.path.join(DATA_DIR, 'permits.json'))
save_json(rigs,    os.path.join(DATA_DIR, 'rigs.json'))
save_json(meta,    os.path.join(DATA_DIR, 'meta.json'))

total = len(all_data)
print(f"\n✓ Done — {total:,} total records across {len(ops)} operators, {len(states)} states")
print(f"  Wells: {len(wells):,}  Permits: {len(permits):,}  Rigs: {len(rigs):,}")
print(f"\nNext step: push changes to GitHub. Netlify will auto-deploy in ~30 seconds.\n")
