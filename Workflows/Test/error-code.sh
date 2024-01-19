#bash
input_file="$1"

if [ ! -f "$input_file" ]; then
  echo "File not found"
  exit
fi

while IFS=';' read -r error_code domain log_info || [ -n "$error_code" ]; do

    if [ "$error_code" -eq 255 ] && ! grep -q "$domain" <<< "$temp"; then
        echo "CRITICAL :: $domain : $log_info"
    elif [ "$error_code" -eq 255 ]; then
        temp+=" $domain"
        echo "OK :: $domain : $log_info"
    else
        echo "OK :: $domain : $log_info"
    fi
done < "$input_file"
