#!/usr/bin/env bash
# ───────────────────────────────────────────────
# Seletor interativo de wallpaper (Rofi + swww/mpvpaper)
# Otimizado para desempenho e qualidade no Hyprland
# ───────────────────────────────────────────────

WALLPAPER_DIR="$HOME/Pictures/Wallpapers"
mkdir -p "$WALLPAPER_DIR"

# Busca wallpapers
mapfile -t WALLS < <(find "$WALLPAPER_DIR" -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.webm" -o -iname "*.mp4" -o -iname "*.mkv" \) | sort)
if [ ${#WALLS[@]} -eq 0 ]; then
    notify-send "❌ Nenhum wallpaper encontrado" "Adicione imagens ou vídeos em $WALLPAPER_DIR"
    exit 1
fi

# Menu Rofi
SELECTED=$(printf '%s\n' "${WALLS[@]}" | rofi -dmenu -i -p "🖼️ Escolha um wallpaper:")
[ -z "$SELECTED" ] && exit 0

EXT="${SELECTED##*.}"

# Garante daemon do swww
if ! pgrep -x swww-daemon >/dev/null; then
    swww-daemon --no-daemon &
    sleep 0.5
fi

# Encerra instâncias antigas
pkill mpvpaper 2>/dev/null

# Função para detectar aceleração disponível
detect_hwdec() {
    if vainfo &>/dev/null; then echo "vaapi"; \
    elif vdpauinfo &>/dev/null; then echo "vdpau"; \
    elif [ -e /dev/dri/renderD128 ]; then echo "drm"; \
    else echo "auto"; fi
}

HWDEC=$(detect_hwdec)

# ─── VÍDEO: usa mpvpaper ───────────────────────
if [[ "$EXT" =~ ^(mp4|webm|mkv)$ ]]; then
    if command -v mpvpaper >/dev/null 2>&1; then
        mpvpaper -o "--loop --no-audio --no-osd-bar --no-input-default-bindings \
            --profile=low-latency --hwdec=$HWDEC \
            --vo=gpu-next --gpu-context=wayland --framedrop=yes \
            --really-quiet --ytdl=no --idle=yes --panscan=1.0 \
            --vd-lavc-skiploopfilter=nonkey --hr-seek=no" "*" "$SELECTED" &
        notify-send "🎬 Wallpaper de vídeo aplicado" "$(basename "$SELECTED")"
    else
        notify-send "⚠️ mpvpaper não encontrado" "Instale via overlay guru ou compile manualmente."
    fi

# ─── IMAGEM: usa swww ───────────────────────────
else
    swww img "$SELECTED" \
        --transition-type grow \
        --transition-fps 60 \
        --transition-duration 0.7
    notify-send "🖼️ Wallpaper aplicado" "$(basename "$SELECTED")"
fi
