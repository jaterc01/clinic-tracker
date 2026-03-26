#!/bin/bash
# Sync Google Sheets → Firebase
# 用 curl 避免 Python SSL 問題

SHEET_CSV="https://docs.google.com/spreadsheets/d/1c69cWs0pTS4CUVPqBCpprzexThkwp0cWWBmFmsEfb8U/export?format=csv&gid=0"
FIREBASE_DB="https://clinic-tracker-63369-default-rtdb.firebaseio.com"

# Download CSV
CSV=$(curl -sL "$SHEET_CSV")

# Process each data row (skip header and summary)
echo "$CSV" | tail -n +2 | while IFS=',' read -r date sessions herb powder knife other total internal acu push rest1 rest2 rest3 rest4 label1 label2; do
    # Skip empty or summary rows
    [ -z "$date" ] && continue
    [ "$date" = "總和" ] && continue
    
    # Parse date: 3/1 → 2026-03-01
    month=$(echo "$date" | cut -d'/' -f1)
    day=$(echo "$date" | cut -d'/' -f2)
    [ -z "$month" ] || [ -z "$day" ] && continue
    
    # Skip summary labels
    [ "$month" = "牌照稅" ] || [ "$month" = "底薪" ] || [ "$month" = "內科" ] || [ "$month" = "針灸" ] || [ "$month" = "水藥" ] || [ "$month" = "小針刀" ] || [ "$month" = "其他" ] || [ "$month" = "目前診數" ] || [ "$month" = "總診數" ] || [ "$month" = "預計薪水" ] || [ "$month" = "月底估值" ] || [ "$month" = "實際薪水" ] && continue
    
    # Validate numbers
    [[ ! "$month" =~ ^[0-9]+$ ]] && continue
    [[ ! "$day" =~ ^[0-9]+$ ]] && continue
    
    date_str="2026-$(printf '%02d' "$month")-$(printf '%02d' "$day")"
    
    # Build JSON
    sessions=${sessions:-0}
    internal=${internal:-0}
    acu=${acu:-0}
    
    # Build arrays (each value as JSON array)
    herb_arr="[]"
    powder_arr="[]"
    knife_arr="[]"
    other_arr="[]"
    [ -n "$herb" ] && herb_arr="[$herb]"
    [ -n "$powder" ] && powder_arr="[$powder]"
    [ -n "$knife" ] && knife_arr="[$knife]"
    [ -n "$other" ] && other_arr="[$other]"
    
    json="{\"sessions\":$sessions,\"herb\":$herb_arr,\"powder\":$powder_arr,\"knife\":$knife_arr,\"other\":$other_arr,\"internal\":$internal,\"acu\":$acu}"
    
    # Check if record exists
    existing=$(curl -s "${FIREBASE_DB}/records/${date_str}.json")
    
    if [ "$existing" != "null" ] && [ -n "$existing" ]; then
        # Merge: keep existing, update from sheets
        # For simplicity, use PATCH to update specific fields
        echo "  🔄 $date_str (updating)"
        curl -s -X PATCH "${FIREBASE_DB}/records/${date_str}.json" \
            -H "Content-Type: application/json" \
            -d "{\"sessions\":$sessions,\"herb\":$herb_arr,\"powder\":$powder_arr,\"knife\":$knife_arr,\"other\":$other_arr,\"internal\":$internal,\"acu\":$acu}" > /dev/null
    else
        echo "  ✅ $date_str (new)"
        curl -s -X PUT "${FIREBASE_DB}/records/${date_str}.json" \
            -H "Content-Type: application/json" \
            -d "$json" > /dev/null
    fi
done

echo "Done!"
