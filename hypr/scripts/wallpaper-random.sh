#!/usr/bin/env bash

# Impede que o script seja executado como root (com sudo)
if [[ $EUID -eq 0 ]]; then
   echo "ERRO: Este script não deve ser executado com sudo." 
   exit 1
fi

# Caminho para o seu diretório de wallpapers
WALLPAPER_DIR="$HOME/wallpapers"

# Lista de animações para sortear
declare -a ANIMATIONS=(
    "grow"
    "outer"
    "wipe"
    "wave"
    "fade"
)

# Sorteia uma animação aleatória da lista
NUM_ANIMATIONS=${#ANIMATIONS[@]}
CHOSEN_ANIMATION=${ANIMATIONS[ $RANDOM % $NUM_ANIMATIONS ]}

# Verifica se o diretório de wallpapers existe
if [ ! -d "$WALLPAPER_DIR" ]; then
    dunstify -u critical "Erro" "Diretório de wallpapers não encontrado: $WALLPAPER_DIR"
    exit 1
fi

# Sorteia um papel de parede aleatório
CHOSEN_WP=$(find "$WALLPAPER_DIR" -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.gif' \) | shuf -n 1)

# Verifica se alguma imagem foi encontrada
if [ -z "$CHOSEN_WP" ]; then
    dunstify -u critical "Erro" "Nenhuma imagem encontrada em $WALLPAPER_DIR"
    exit 1
fi

# Executa o comando swww com a imagem e a animação sorteadas
swww img "$CHOSEN_WP" \
    --transition-type "$CHOSEN_ANIMATION" \
    --transition-duration 1.2 \
    --transition-fps 60 \
    --transition-pos center

# Envia uma notificação informando o que foi feito
dunstify -a "wallpaper" -u low -i "$CHOSEN_WP" "Wallpaper Trocado!" "Animação: ${CHOSEN_ANIMATION}"
