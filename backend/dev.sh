if [ -f .env ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    # Skip comments and empty lines
    case "$line" in
      '#'* | '') continue ;;
    esac

    # Export the variable
    export "$line"
  done < .env
fi

export CORS_ALLOW_ORIGIN=http://localhost:5173/
PORT="${PORT:-8080}"
uvicorn open_webui.main:app --port $PORT --host 0.0.0.0 --forwarded-allow-ips '*' --reload
