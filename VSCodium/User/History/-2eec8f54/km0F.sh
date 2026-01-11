#!/usr/bin/env bash
#
# Bluetooth Control Center para Waybar - Versão Completa
# Funcionalidades: Ligar/Desligar, Procurar, Conectar/Desconectar, Remover, Emparelhar
# Autor: Adaptado para Gentoo

# =========================
# CONFIGURAÇÃO DE NOTIFICAÇÕES
# =========================
send_notification() {
    # Usa notify-send se dunst/mako estiver rodando
    if pgrep -x dunst >/dev/null; then
        notify-send "Bluetooth" "$1" -r 9991
    else
        echo "[NOTIFY] $1"
    fi
}

# =========================
# LIGA/DESLIGA BLUETOOTH
# =========================
toggle_power() {
    local status
    status=$(bluetoothctl show | grep PowerState | awk '{print $2}')

    if [[ $status == 'on' ]]; then
        bluetoothctl power off >/dev/null
        send_notification "Bluetooth desligado"
    else
        bluetoothctl power on >/dev/null
        send_notification "Bluetooth ligado"
    fi
}

ensure_on() {
    local status
    status=$(bluetoothctl show | grep PowerState | awk '{print $2}')

    if [[ $status == 'off' ]]; then
        bluetoothctl power on >/dev/null
        send_notification "Bluetooth ligado"
    fi
}

# =========================
# LISTA DISPOSITIVOS
# =========================
list_devices() {
    bluetoothctl devices | while read -r line; do
        mac=$(echo "$line" | awk '{print $2}')
        name=$(echo "$line" | cut -d ' ' -f 3-)
        info=$(bluetoothctl info "$mac")

        if echo "$info" | grep -q "Connected: yes"; then
            status="Conectado"
        elif echo "$info" | grep -q "Paired: yes"; then
            status="Emparelhado"
        else
            status="Disponível"
        fi

        printf "%-20s %-17s %-12s\n" "$name" "$mac" "$status"
    done
}

# =========================
# MENU PRINCIPAL INTERATIVO
# =========================
main_menu() {
    printf "Ligar/Desligar Bluetooth\n"
    printf "Procurar novos dispositivos\n"
    printf "Remover um dispositivo\n"
    list_devices
}

# =========================
# SELEÇÃO E AÇÃO SOBRE DISPOSITIVOS
# =========================
select_device_action() {
    local choice="$1"
    mac=$(echo "$choice" | awk '{print $2}')
    name=$(echo "$choice" | awk '{$1=""; $2=""; print $0}' | sed 's/^ *//')

    info=$(bluetoothctl info "$mac")

    if echo "$info" | grep -q "Connected: yes"; then
        # Desconectar
        bluetoothctl disconnect "$mac" >/dev/null
        send_notification "Desconectado de $name"
    else
        # Conectar e emparelhar se necessário
        send_notification "Conectando a $name..."
        if bluetoothctl connect "$mac" >/dev/null; then
            send_notification "Conectado a $name"
        else
            send_notification "Falha ao conectar. Tentando emparelhar..."
            if bluetoothctl pair "$mac" >/dev/null; then
                sleep 1
                bluetoothctl trust "$mac" >/dev/null
                bluetoothctl connect "$mac" >/dev/null
                send_notification "Emparelhado e conectado a $name"
            else
                send_notification "Erro ao emparelhar $name"
            fi
        fi
    fi
}

# =========================
# PROCURAR DISPOSITIVOS
# =========================
scan_devices() {
    send_notification "Iniciando procura de dispositivos... (Ctrl+C para parar)"
    bluetoothctl scan on
}

# =========================
# REMOVER DISPOSITIVO
# =========================
remove_device() {
    device_to_remove=$(bluetoothctl devices | cut -d' ' -f2- | fzf --prompt="Selecione um dispositivo para remover: " --height=25%)
    [[ -n "$device_to_remove" ]] || return
    mac=$(echo "$device_to_remove" | awk '{print $1}')
    name=$(echo "$device_to_remove" | cut -d' ' -f2-)
    bluetoothctl remove "$mac" >/dev/null
    send_notification "Dispositivo removido: $name"
}

# =========================
# LOOP PRINCIPAL
# =========================
main() {
    ensure_on
    tput civis  # Oculta cursor

    while true; do
        choice=$(main_menu | fzf --prompt="Bluetooth: " --height=50% --layout=reverse --border --ansi)
        [[ -z "$choice" ]] && break  # Sai se ESC ou fechar fzf

        case "$choice" in
            "Ligar/Desligar Bluetooth") toggle_power ;;
            "Procurar novos dispositivos") scan_devices ;;
            "Remover um dispositivo") remove_device ;;
            *) select_device_action "$choice" ;;
        esac
    done

    tput cnorm  # Restaura cursor
}

main
