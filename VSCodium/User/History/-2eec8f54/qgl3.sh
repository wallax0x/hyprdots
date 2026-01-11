#!/usr/bin/env bash
# Centro de Controlo de Bluetooth para Waybar
# Requisitos: bluez, fzf, libnotify

# Função para listar dispositivos Bluetooth
list_devices() {
    bluetoothctl devices | awk '{print $2 " " substr($0, index($0,$3))}'
}

# Menu principal usando fzf
main_menu() {
    OPTIONS="Ligar\nDesligar\nEmparelhar\nConectar\nDesconectar\nListar"
    ACTION=$(echo -e "$OPTIONS" | fzf --prompt="Bluetooth: " --height 10 --border)

    case "$ACTION" in
        "Ligar")
            notify-send "Bluetooth" "Ligando adaptador..."
            rfkill unblock bluetooth
            systemctl start bluetooth.service
            ;;
        "Desligar")
            notify-send "Bluetooth" "Desligando adaptador..."
            rfkill block bluetooth
            systemctl stop bluetooth.service
            ;;
        "Emparelhar")
            device=$(list_devices | fzf --prompt="Escolha dispositivo para emparelhar: " --height 10 --border)
            [ -z "$device" ] && exit
            mac=$(echo $device | awk '{print $1}')
            notify-send "Bluetooth" "Emparelhando com $mac..."
            bluetoothctl pair $mac
            ;;
        "Conectar")
            device=$(list_devices | fzf --prompt="Escolha dispositivo para conectar: " --height 10 --border)
            [ -z "$device" ] && exit
            mac=$(echo $device | awk '{print $1}')
            notify-send "Bluetooth" "Conectando a $mac..."
            bluetoothctl connect $mac
            ;;
        "Desconectar")
            device=$(list_devices | fzf --prompt="Escolha dispositivo para desconectar: " --height 10 --border)
            [ -z "$device" ] && exit
            mac=$(echo $device | awk '{print $1}')
            notify-send "Bluetooth" "Desconectando $mac..."
            bluetoothctl disconnect $mac
            ;;
        "Listar")
            list_devices | notify-send "Dispositivos Bluetooth"
            ;;
        *)
            exit 0
            ;;
    esac
}

# Execução
main_menu
