#!/usr/bin/env bash
# Troca o wallpaper para o próximo da pasta usando swww (imagem) ou mpv (vídeo)

WALLPAPER_DIR="$HOME/Pictures/Wallpapers"
STATE_FILE="$HOME/.cache/current_wallpaper_index"

mkdir -p "$WALLPAPER_DIR" "$HOME/.cache"

# Lista todos os arquivos válidos (ordem alfabética)
mapfile -t WALLS < <(find "$WALLPAPER_DIR" -type f \( -iname "*.jpg" -o -iname "*.png" -o -iname "*.jpeg" -o -iname "*.webm" -o -iname "*.mp4" \) | sort)

if [ ${#WALLS[@]} -eq 0 ]; then
  notify-send "Nenhum wallpaper encontrado em $WALLPAPER_DIR"
  exit 1
fi

# Lê o índice atual
if [ -f "$STATE_FILE" ]; then
  CURRENT_INDEX=$(<"$STATE_FILE")
else
  CURRENT_INDEX=-1
fi

# Próximo índice (com loop)
NEXT_INDEX=$(( (CURRENT_INDEX + 1) % ${#WALLS[@]} ))
echo "$NEXT_INDEX" > "$STATE_FILE"

FILE="${WALLS[$NEXT_INDEX]}"
EXT="${FILE##*.}"

# Para mpv caso esteja rodando
pkill -f "mpv.*wallpaper" 2>/dev/null

if [[ "$EXT" =~ ^(mp4|webm|mkv)$ ]]; then
  # Executa vídeo em loop no fundo (mpv modo wallpaper)
  nohup mpv --loop --no-audio --no-osd-bar --geometry=100%x100% --panscan=1.0 --wid=$(hyprctl activewindow -j | jq -r '.workspace.id') --ontop --panscan=1.0 --script-opts=wallpaper_mode=fill "$FILE" >/dev/null 2>&1 &
  notify-send "🎬 Wallpaper de vídeo iniciado" "$(basename "$FILE")"
else
  # Troca imagem via swww (fade suave)
  swww img "$FILE" --transition-type any --transition-fps 60 --transition-duration 2
  notify-send "🖼️ Wallpaper alterado" "$(basename "$FILE")"
fi
