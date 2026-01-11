#!/usr/bin/env bash
#
# Script unificado para wallpapers estáticos, GIFs e vídeos

# Impede execução como root
if [[ $EUID -eq 0 ]]; then
   echo "ERRO: Este script não deve ser executado com sudo." 
   exit 1
fi

WALLPAPER_DIR="$HOME/wallpapers"
INDEX_FILE="$HOME/.cache/current_wallpaper_index"

# Animações de transição para imagens estáticas
ANIMATIONS=("grow" "outer" "wipe" "wave" "fade")

# --- Verificações Iniciais ---
if [ ! -d "$WALLPAPER_DIR" ]; then
    notify-send "Erro de Wallpaper" "Diretório não encontrado: $WALLPAPER_DIR"
    exit 1
fi

# --- Lógica Principal ---

# Termina qualquer processo de wallpaper de vídeo que esteja a correr
pkill -f "mpv --wid"

# Lista TODOS os wallpapers (imagens, gifs, vídeos)
mapfile -t WALLPAPERS < <(find "$WALLPAPER_DIR" -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.gif' -o -iname '*.mp4' -o -iname '*.webm' -o -iname '*.mov' \) | sort)

if [ ${#WALLPAPERS[@]} -eq 0 ]; then
    notify-send "Erro de Wallpaper" "Nenhum ficheiro encontrado em $WALLPAPER_DIR"
    exit 1
fi

# Lê o índice do último wallpaper usado
LAST_INDEX=-1
if [ -f "$INDEX_FILE" ]; then
    LAST_INDEX=$(<"$INDEX_FILE")
fi

# Calcula o próximo índice (circular)
NEXT_INDEX=$(( (LAST_INDEX + 1) % ${#WALLPAPERS[@]} ))
CHOSEN_WP="${WALLPAPERS[$NEXT_INDEX]}"

# Guarda o novo índice
echo "$NEXT_INDEX" > "$INDEX_FILE"

# Verifica a extensão do ficheiro e executa a ação correta
file_ext="${CHOSEN_WP##*.}"
case "$file_ext" in
    jpg|jpeg|png|gif)
        # Para imagens e GIFs, use o swww com uma transição aleatória
        CHOSEN_ANIMATION=${ANIMATIONS[ $RANDOM % ${#ANIMATIONS[@]} ]}
        swww img "$CHOSEN_WP" \
            --transition-type "$CHOSEN_ANIMATION" \
            --transition-duration 1.2 \
            --transition-fps 60
        ;;
    mp4|webm|mov)
        # Para vídeos, use o mpv em segundo plano
        mpv --wid=$(swww query | grep -o -E '0x[0-9a-f]+' | head -n 1) \
            --no-audio \
            --loop=inf \
            "$CHOSEN_WP" &
        ;;
    *)
        notify-send "Erro de Wallpaper" "Formato não suportado: $file_ext"
        exit 1
        ;;
esac
