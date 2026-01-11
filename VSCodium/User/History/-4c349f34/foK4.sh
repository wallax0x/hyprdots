#!/bin/bash

# --- CONFIGURAÇÃO ---
# Defina a sua pasta de wallpapers aqui
WALLPAPER_DIR="$HOME/Pictures/Wallpapers"

# --- LÓGICA DO SCRIPT ---

# Espere que o daemon do swww esteja pronto
until swww query; do
    sleep 0.5
done

# Crie uma lista de todos os ficheiros na pasta de wallpapers
# e mostre-a ao utilizador através do Rofi para que ele possa escolher.
choice=$(find "$WALLPAPER_DIR" -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" -o -name "*.gif" -o -name "*.mp4" -o -name "*.webm" \) -printf "%f\n" | rofi -dmenu -i -p " Wallpapers")

# Se o utilizador não escolheu nada (pressionou Esc), saia.
if [ -z "$choice" ]; then
    exit 0
fi

# Crie o caminho completo para o ficheiro escolhido
wallpaper_path="$WALLPAPER_DIR/$choice"

# Obtenha a extensão do ficheiro
extension="${choice##*.}"

# Verifique se algum processo de wallpaper de vídeo (mpv) está a correr e, se estiver, termine-o.
pkill mpv

# Use uma estrutura 'case' para decidir o que fazer com base na extensão do ficheiro
case $extension in
    # Para imagens estáticas e GIFs, use 'swww img'
    jpg|jpeg|png|gif)
        swww img "$wallpaper_path" --transition-type any
        ;;
    # Para ficheiros de vídeo, use o nosso comando 'mpv'
    mp4|webm|mkv)
        mpv --wid=$(swww query | grep -o -E '0x[0-9a-f]+' | head -n 1) \
            --no-audio \
            --loop=inf \
            "$wallpaper_path" &
        ;;
    *)
        # Se for um tipo de ficheiro desconhecido, mostre um erro
        notify-send "Erro de Wallpaper" "Tipo de ficheiro não suportado: $extension"
        ;;
esac
