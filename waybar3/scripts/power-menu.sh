#!/usr/bin/env bash

# Define o caminho para o nosso tema
ROFI_CONFIG="$HOME/.config/rofi/power-menu.rasi"

# Opções com ícones e rótulos de texto (usando Pango markup)
LOCK="  LOCK"
SHUTDOWN="  SHUT"
REBOOT="  REB"
SUSPEND="  SUS"
LOGOUT="󰞘  LOG"

options="$LOCK\n$SHUTDOWN\n$REBOOT\n$SUSPEND\n$LOGOUT"

# Função de confirmação
confirm_action() {
    echo -e "Sim\nNão" | rofi -dmenu -i -p "$1" \
        -config "$ROFI_CONFIG" \
        -theme-str 'listview { lines: 2; } element-text { horizontal-align: 0.5; }'
}

# Roda o Rofi com o tema e o título
chosen="$(echo -e "$options" | rofi -dmenu -i -p "Power Menu" -markup-rows -config "$ROFI_CONFIG")"

# Executa a ação correspondente
case "$chosen" in
    "$LOCK")
        swaylock
        ;;
    "$SHUTDOWN")
        if [[ "$(confirm_action 'Tem certeza que quer desligar?')" == "Sim" ]]; then
            systemctl poweroff
        fi
        ;;
    "$REBOOT")
        if [[ "$(confirm_action 'Tem certeza que quer reiniciar?')" == "Sim" ]]; then
            systemctl reboot
        fi
        ;;
    "$SUSPEND")
        # Para suspender, não pedimos confirmação
        systemctl suspend
        ;;
    "$LOGOUT")
        if [[ "$(confirm_action 'Tem certeza que quer sair?')" == "Sim" ]]; then
            loginctl kill-session "$XDG_SESSION_ID"
        fi
        ;;
esac