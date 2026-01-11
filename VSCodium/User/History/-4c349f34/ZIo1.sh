#!/bin/bash

# --- CONFIGURAÇÃO ---
WALLPAPER_DIR="$HOME/Pictures/Wallpapers"
STATE_FILE="$HOME/.cache/current_wallpaper"

# --- LÓGICA DO SCRIPT ---
mkdir -p ~/.cache

# Espere que o daemon do swww esteja pronto (corrige o erro 'wid')
until swww query &>/dev/null; do
    sleep 0.5
done

# Encontra todos os wallpapers válidos, ordenados por nome
mapfile -d '' wallpapers < <(find "$WALLPAPER_DIR" -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" -o -name "*.gif" -o -name "*.mp4" -o -name "*.webm" \) -print0 | sort -z)

# Se não houver wallpapers, sai com um erro
if [ ${#wallpapers[@]} -eq 0 ]; then
    notify-send "Wallpaper Cycler" "Nenhum wallpaper encontrado em $WALLPAPER_DIR"
    exit 1
fi

# Lê o último wallpaper usado
current_wallpaper=$(cat "$STATE_FILE" 2>/dev/null)

# Encontra o índice do wallpaper atual na lista
current_index=-1
for i in "${!wallpapers[@]}"; do
   if [[ "${wallpapers[$i]}" = "${current_wallpaper}" ]]; then
       current_index=$i
       break
   fi
done

# Calcula o índice do próximo wallpaper (se o atual não for encontrado, começa do primeiro)
next_index=$(( (current_index + 1) % ${#wallpapers[@]} ))
next_wallpaper="${wallpapers[$next_index]}"

# --- APLICA O NOVO WALLPAPER ---
extension="${next_wallpaper##*.}"
pkill mpv # Termina qualquer wallpaper de vídeo antigo

case $extension in
    jpg|jpeg|png|gif)
        swww img "$next_wallpaper" --transition-type wipe --transition-angle 30 --transition-step 90
        ;;
    mp4|webm|mkv)
        mpv --wid=$(swww query | grep -o -E '0x[0-9a-f]+' | head -n 1) \
            --no-audio --loop=inf "$next_wallpaper" &
        ;;
esac

# Guarda o novo wallpaper como o "atual" para a próxima vez
echo "$next_wallpaper" > "$STATE_FILE"