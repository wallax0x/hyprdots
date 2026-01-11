#!/usr/bin/env bash
# Centro de Controlo de Bluetooth para Waybar (revisado)
# Requisitos: bluez, fzf, libnotify/dunst

# --- Funções auxiliares ---

# Lista dispositivos Bluetooth com MAC e nome
list_devices() {
    bluetoothctl devices | awk '{print $2 " " substr($0, index($0,$3))}'
}

# Função para enviar notificações seguras
notify() {
    # Verifica se dunst ou outro daemon está ativo
    if pgrep -x dunst >/dev/null; then
        notify-send "Bluetooth" "$1"
    fi
}

# Ativa o agente Bluetooth
start_agent() {
    bluetoothctl agent on >/dev/null 2>&1
    bluetoothctl default-agent >/dev/null 2>&1
}

# --- Menu principal usando fzf ---
main_menu() {
    OPTIONS="Ligar\nDesligar\nEmparelhar\nConectar\nDesconectar\nListar Dispositivos"
    ACTION=$(echo -e "$OPTIONS" | fzf --prompt="Bluetooth: " --height 10 --border)

    case "$ACTION" in
        "Ligar")
            notify "Ligando adaptador..."
            rfkill unblock bluetooth
            systemctl start bluetooth.service
            ;;
        "Desligar")
            notify "Desligando adaptador..."
            rfkill block bluetooth
            systemctl stop bluetooth.service
            ;;
        "Emparelhar")
            start_agent
            device=$(list_devices | fzf --prompt="Escolha dispositivo para emparelhar: " --height 10 --border)
            [ -z "$device" ] && exit
            mac=$(echo "$device" | awk '{print $1}')
            notify "Emparelhando com $mac..."
            bluetoothctl pair $mac
            ;;
        "Conectar")
            start_agent
            device=$(list_devices | fzf --prompt="Escolha dispositivo para conectar: " --height 10 --border)
            [ -z "$device" ] && exit
            mac=$(echo "$device" | awk '{print $1}')
            notify "Conectando a $mac..."
            bluetoothctl connect $mac
            ;;
        "Desconectar")
            device=$(list_devices | fzf --prompt="Escolha dispositivo para desconectar: " --height 10 --border)
            [ -z "$device" ] && exit
            mac=$(echo "$device" | awk '{print $1}')
            notify "Desconectando $mac..."
            bluetoothctl disconnect $mac
            ;;
        "Listar Dispositivos")
            devices=$(list_devices)
            [ -z "$devices" ] && devices="Nenhum dispositivo encontrado"
            notify "$devices"
            ;;
        *)
            exit 0
            ;;
    esac
}

# --- Execução ---
main_menu
