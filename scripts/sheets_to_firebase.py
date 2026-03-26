#!/usr/bin/env python3
"""
Sync Google Sheets → Firebase (方向2: 每日 0:00 cron)
讀取 Google Sheets CSV，將 2026/03 起的資料寫入 Firebase
"""
import csv, json, urllib.request, re
from datetime import datetime

# Google Sheets CSV URL (public)
SHEET_CSV = "https://docs.google.com/spreadsheets/d/1c69cWs0pTS4CUVPqBCpprzexThkwp0cWWBmFmsEfb8U/export?format=csv&gid=0"

# Firebase
FIREBASE_DB = "https://clinic-tracker-63369-default-rtdb.firebaseio.com"

def read_sheet():
    import subprocess
    result = subprocess.run(
        ['curl', '-sL', SHEET_CSV],
        capture_output=True, text=True
    )
    return list(csv.reader(result.stdout.splitlines()))

def parse_date(raw):
    """Parse '3/1' → '2026-03-01'"""
    raw = raw.strip()
    if not raw:
        return None
    m = re.match(r'(\d{1,2})/(\d{1,2})', raw)
    if not m:
        return None
    month, day = int(m.group(1)), int(m.group(2))
    return f"2026-{month:02d}-{day:02d}"

def get_dow(date_str):
    """Get day of week: 0=Sun ... 6=Sat"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.weekday() + 1 if dt.weekday() < 6 else 0  # Mon=1...Sat=6, Sun=0

def sheets_to_firebase_record(row, date_str):
    """Convert a sheet row to Firebase record format"""
    # row: 日期,診數,水藥,藥粉,小針刀,其他,人數,內,針,推
    sessions = int(row[1]) if row[1] else 0
    herb = [int(row[2])] if row[2] and row[2].strip() else []
    powder = [int(row[3])] if row[3] and row[3].strip() else []
    knife = [int(row[4])] if row[4] and row[4].strip() else []
    other = [int(row[5])] if row[5] and row[5].strip() else []
    # 人數=內+針, split into internal and acu
    internal = int(row[7]) if row[7] and row[7].strip() else 0
    acu = int(row[8]) if row[8] and row[8].strip() else 0
    
    return {
        "sessions": sessions,
        "herb": herb,
        "powder": powder,
        "knife": knife,
        "other": other,
        "internal": internal,
        "acu": acu
    }

def firebase_put(path, data):
    url = f"{FIREBASE_DB}/records/{path}.json"
    payload = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=payload, method='PUT',
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def firebase_get(path):
    url = f"{FIREBASE_DB}/records/{path}.json"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def main():
    rows = read_sheet()
    print(f"Read {len(rows)} rows from Google Sheets")
    
    synced = 0
    skipped = 0
    errors = []
    
    for row in rows:
        if not row or not row[0]:
            continue
        date_str = parse_date(row[0])
        if not date_str:
            continue
        # Only sync 2026-03 onwards
        if not date_str.startswith("2026-03") and date_str < "2026-03-01":
            skipped += 1
            continue
        # Skip summary rows
        if row[0].strip() in ["日期", "總和"]:
            skipped += 1
            continue
        
        try:
            new_data = sheets_to_firebase_record(row, date_str)
            existing = firebase_get(date_str)
            
            if existing:
                # Merge: keep existing data but update from sheets if sheets has more info
                # Prefer sheets data for sessions, internal, acu
                merged = {**existing, **new_data}
                # Keep arrays: use longer ones
                for key in ['herb', 'powder', 'knife', 'other']:
                    if len(merged.get(key, [])) < len(new_data.get(key, [])):
                        merged[key] = new_data[key]
                firebase_put(date_str, merged)
            else:
                firebase_put(date_str, new_data)
            
            synced += 1
            print(f"  ✅ {date_str}: sessions={new_data['sessions']}, internal={new_data['internal']}, acu={new_data['acu']}")
        except Exception as e:
            errors.append(f"  ❌ {date_str}: {e}")
            print(errors[-1])
    
    print(f"\nDone: synced={synced}, skipped={skipped}, errors={len(errors)}")

if __name__ == "__main__":
    main()
