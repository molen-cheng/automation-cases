#!/bin/bash
# Download 2024 Vietnam customs PDFs - smart approach
BASE="${VIETNAM_DATA_DIR:-./data/vietnam-customs/2024}"
mkdir -p $BASE/{01..12}

download_if_ok() {
    local url="$1" dest="$2" label="$3"
    local code=$(curl -sI -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    if [ "$code" = "200" ]; then
        local size=$(curl -sI "$url" 2>/dev/null | grep -i content-length | awk '{print $2}' | tr -d '\r')
        if [ "${size:-0}" -gt 5000 ] 2>/dev/null; then
            echo "FOUND: $label -> $url ($size)"
            curl -sS -o "$dest" "$url"
            return 0
        fi
    fi
    return 1
}

# For each month/type, construct likely URLs based on patterns
# Pattern: publish month = data_month + 1, date ~9-11
# 2024 case is mixed: some lowercase (t3-2n(vn-sb)), some uppercase (T6-2X(VN-SB))

for m in $(seq 1 12); do
    month=$(printf "%02d" $m)
    # Publish month
    pm=$((m + 1))
    [ $pm -gt 12 ] && pm=$m
    
    for type in 2x 2n 5x 5n; do
        dest="$BASE/$month/$type.pdf"
        [ -f "$dest" ] && { echo "EXISTS: $month $type"; continue; }
        
        found=0
        # Try various combinations for dates 5-15
        for pd in 5 6 7 8 9 10 11 12; do
            # lowercase
            download_if_ok "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2024/$pm/$pd/2024-t${month}-${type}(vn-sb).pdf" "$dest" "$month $type" && { found=1; break; }
            # uppercase type + VN-SB
            utype=$(echo $type | tr '[:lower:]' '[:upper:]')
            download_if_ok "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2024/$pm/$pd/2024-T${month}-${utype}(VN-SB).pdf" "$dest" "$month $type" && { found=1; break; }
            # mixed cases
            download_if_ok "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2024/$pm/$pd/2024-t${month}-${utype}(VN-SB).pdf" "$dest" "$month $type" && { found=1; break; }
            download_if_ok "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2024/$pm/$pd/2024-T${month}-${type}(VN-SB).pdf" "$dest" "$month $type" && { found=1; break; }
            download_if_ok "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2024/$pm/$pd/2024-T${month}-${type}(TA-SB).pdf" "$dest" "$month $type" && { found=1; break; }
        done
        
        # If not found, try pm+1
        if [ $found -eq 0 ] && [ $pm -lt 12 ]; then
            pm2=$((pm + 1))
            for pd in 5 6 7 8 9 10 11; do
                download_if_ok "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2024/$pm2/$pd/2024-t${month}-${type}(vn-sb).pdf" "$dest" "$month $type" && { found=1; break; }
                utype=$(echo $type | tr '[:lower:]' '[:upper:]')
                download_if_ok "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2024/$pm2/$pd/2024-T${month}-${utype}(VN-SB).pdf" "$dest" "$month $type" && { found=1; break; }
            done
        fi
        
        [ $found -eq 0 ] && echo "MISSING: $month $type"
    done
done
echo "DONE"
