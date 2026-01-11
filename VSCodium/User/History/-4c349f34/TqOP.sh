#!/usr/bin/env bash
# ───────────────────────────────────────────────
# Troca o wallpaper (imagem via swww / vídeo via mpvpaper)
# Compatível com Hyprland + Gentoo
# ───────────────────────────────────────────────

WALLPAPER_DIR="$HOME/Pictures/Wallpapers"
STATE_FILE="$HOME/.cache/current_wallpaper_index"
mkdir -p "$WALLPAPER_DIR" "$HOME/.cache"

# Coleta todos os wallpapers válidos
mapfile -t WALLS < <(find "$WALLPAPER_DIR" -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.mp4" -o -iname "*.webm" -o -iname "*.mkv" \) | sort)

if [ ${#WALLS[@]} -eq 0 ]; then
    notify-send "❌ Nenhum wallpaper encontrado" "Coloque imagens ou vídeos em $WALLPAPER_DIR"
    exit 1
fi

# Lê o último índice usado e define o próximo
if [ -f "$STATE_FILE" ]; then
    CURRENT_INDEX=$(<"$STATE_FILE")
else
    CURRENT_INDEX=-1
fi

NEXT_INDEX=$(( (CURRENT_INDEX + 1) % ${#WALLS[@]} ))
echo "$NEXT_INDEX" > "$STATE_FILE"

FILE="${WALLS[$NEXT_INDEX]}"
EXT="${FILE##*.}"

# Mata wallpapers anteriores
pkill mpvpaper 2>/dev/null

# Se for vídeo ───────────────────────────────────────
if [[ "$EXT" =~ ^(mp4|webm|mkv)$ ]]; then
    if command -v mpvpaper >/dev/null 2>&1; then
        mpvpaper -o "--loop --no-audio --no-osd-bar --no-input-default-bindings" "*" "$FILE" &
        notify-send "🎬 Wallpaper de vídeo" "$(basename "$FILE")"
    else
        notify-send "⚠️ mpvpaper não encontrado" "Instale via overlay guru ou compile manualmente."
    fi

# Se for imagem ───────────────────────────────────────
else
    if ! pgrep -x swww-daemon >/dev/null; then
        swww init
        sleep 0.5
    fi

    swww img "$FILE" \
        --transition-type grow \
        --transition-fps 60 \
        --transition-duration 2 \
        --transition-bezier .43,1.19,1,.4

    notify-send "🖼️ Wallpaper alterado" "$(basename "$FILE")"
fi
