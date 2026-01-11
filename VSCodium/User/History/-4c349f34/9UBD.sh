#!/usr/bin/env bash
# ───────────────────────────────────────────────
# Hyprland dynamic wallpaper changer (swww + mpvpaper)
# Com múltiplas transições, shuffle e troca rápida
# ───────────────────────────────────────────────

WALLPAPER_DIR="$HOME/Pictures/Wallpapers"
STATE_FILE="$HOME/.cache/current_wallpaper_index"
mkdir -p "$WALLPAPER_DIR" "$HOME/.cache"

# ──────────────── Configurações ────────────────
TRANSITIONS=(fade grow outer wave any simple left right random)
FPS=75
DURATION=1.2   # menor = mais rápido (recomendo entre 0.7 e 1.5 seg)

# ──────────────── Coleta wallpapers ────────────────
mapfile -t WALLS < <(find "$WALLPAPER_DIR" -type f \
  \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \
  -o -iname "*.mp4" -o -iname "*.webm" -o -iname "*.mkv" \) | shuf)

if [ ${#WALLS[@]} -eq 0 ]; then
  notify-send "❌ Nenhum wallpaper encontrado" "Adicione imagens ou vídeos em $WALLPAPER_DIR"
  exit 1
fi

# ──────────────── Próximo índice ────────────────
if [ -f "$STATE_FILE" ]; then
  CURRENT_INDEX=$(<"$STATE_FILE")
else
  CURRENT_INDEX=-1
fi
NEXT_INDEX=$(( (CURRENT_INDEX + 1) % ${#WALLS[@]} ))
echo "$NEXT_INDEX" > "$STATE_FILE"

FILE="${WALLS[$NEXT_INDEX]}"
EXT="${FILE##*.}"

# ──────────────── Garante que o swww-daemon esteja ativo ────────────────
if ! pgrep -x swww-daemon >/dev/null; then
  swww-daemon --no-daemon &
  sleep 0.5
fi

# ──────────────── Fecha vídeos anteriores ────────────────
pkill mpvpaper 2>/dev/null

# ──────────────── Escolhe transição aleatória ────────────────
TRANSITION=${TRANSITIONS[$((RANDOM % ${#TRANSITIONS[@]}))]}

# ──────────────── Wallpaper de vídeo ────────────────
if [[ "$EXT" =~ ^(mp4|webm|mkv)$ ]]; then
  if command -v mpvpaper >/dev/null 2>&1; then
    mpvpaper -o "--loop --no-audio --no-osd-bar --no-input-default-bindings --speed=1.0" "*" "$FILE" &
    notify-send "🎬 Wallpaper de vídeo" "$(basename "$FILE")"
  else
    notify-send "⚠️ mpvpaper não encontrado" "Instale via overlay guru ou compile manualmente."
  fi

# ──────────────── Wallpaper de imagem ────────────────
else
  swww img "$FILE" \
    --transition-type "$TRANSITION" \
    --transition-fps "$FPS" \
    --transition-duration "$DURATION"
  notify-send "🖼️ Wallpaper alterado" "$(basename "$FILE")  |  Transição: $TRANSITION"
fi
