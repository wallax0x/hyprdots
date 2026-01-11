#!/usr/bin/env bash
#
# Centro de Controlo de Bluetooth funcional para Waybar
# Funcionalidades: Ligar/Desligar, Procurar, Conectar/Desconectar, Remover, Confiar.
# Requisitos: bluez, fzf, dunst (daemon de notificações ativo)

# Função para enviar notificações (sem ícone)
send_notification() {
    if pgrep -x dunst >/dev/null; then
        notify-send "Bluetooth" "$1" -r 9991
    else
        echo "[NOTIFY] $1"
    fi
}

# Liga o adaptador se estiver desligado
power_on() {
    if bluetoothctl show | grep -q "Powered: no"; then
        bluetoothctl power on >> /dev/null
        sleep 1
    fi
}

# Lista dispositivos com status
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
        printf "   %-20s %-17s %-15s\n" "$name" "$mac" "$status"
    done
}

# Menu principal com fzf
main_menu() {
    printf "Ligar/Desligar Bluetooth\n"
    printf "Procurar novos dispositivos\n"
    printf "Remover um dispositivo\n"
    list_devices
}

# Função principal
main() {
    power_on

    choice=$(main_menu | fzf --prompt="Bluetooth: " --height=50% --layout=reverse --border --ansi)

    [[ -z "$choice" ]] && exit 0

    # Detecta ação estática
    if [[ "$choice" == "Ligar/Desligar Bluetooth" ]]; then
        if bluetoothctl show | grep -q "Powered: yes"; then
            bluetoothctl power off >> /dev/null
            send_notification "Bluetooth desligado."
        else
            bluetoothctl power on >> /dev/null
            send_notification "Bluetooth ligado."
        fi
        exit 0
    elif [[ "$choice" == "Procurar novos dispositivos" ]]; then
        # Abre terminal para escanear
        kitty --title "Procura Bluetooth" sh -c "echo 'A procurar por dispositivos... Pressione Ctrl+C para parar.'; bluetoothctl scan on" &
        exit 0
    elif [[ "$choice" == "Remover um dispositivo" ]]; then
        device_to_remove=$(bluetoothctl devices | cut -d' ' -f2- | fzf --prompt="Selecione um dispositivo para remover: " --height=25%)
        [[ -n "$device_to_remove" ]] || exit 0
        mac_to_remove=$(echo "$device_to_remove" | awk '{print $1}')
        name_to_remove=$(echo "$device_to_remove" | cut -d' ' -f2-)
        bluetoothctl remove "$mac_to_remove" >> /dev/null
        send_notification "Dispositivo removido: $name_to_remove"
        exit 0
    fi

    # Para dispositivos específicos selecionados
    mac=$(echo "$choice" | awk '{print $2}')
    name=$(echo "$choice" | awk '{$1=""; $2=""; print $0}' | sed 's/^ *//')

    info=$(bluetoothctl info "$mac")
    if echo "$info" | grep -q "Connected: yes"; then
        bluetoothctl disconnect "$mac" >> /dev/null
        send_notification "Desconectado de: $name"
    else
        send_notification "A conectar a: $name..."
        if bluetoothctl connect "$mac" >> /dev/null; then
            send_notification "Conectado com sucesso!"
        else
            send_notification "Falha ao conectar. Tentando emparelhar..."
            if bluetoothctl pair "$mac" >> /dev/null; then
                sleep 1
                bluetoothctl trust "$mac" >> /dev/null
                bluetoothctl connect "$mac" >> /dev/null
                send_notification "Emparelhado e conectado a: $name"
            else
                send_notification "Erro ao emparelhar com: $name"
            fi
        fi
    fi
}

main
