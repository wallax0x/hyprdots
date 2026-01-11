#!/usr/bin/env bash
#
# Centro de Controlo de Bluetooth v2.1 para Waybar (adaptado para dunst)
# Funcionalidades: Ligar/Desligar, Procurar, Conectar/Desconectar, Remover, Confiar.
# Requisitos: bluez, fzf, dunst (daemon de notificações ativo)

# Função para enviar notificações usando dunst
send_notification() {
    # Verifica se o daemon dunst está ativo
    if pgrep -x dunst >/dev/null; then
        notify-send "Bluetooth" "$1" -i "bluetooth" -r 9991
    else
        echo "[NOTIFY] $1" # Fallback: mostra no terminal se dunst não estiver ativo
    fi
}

# Garante que o serviço de Bluetooth está ligado
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
            status="󰂱 Conectado"
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
    printf "   %-45s\n" "󰂯 Ligar/Desligar Bluetooth"
    printf "   %-45s\n" "󰂰 Procurar novos dispositivos"
    printf "   %-45s\n" "󰂲 Remover um dispositivo"
    printf -- "-\n"
    printf "   %-20s %-17s %-15s\n" "Dispositivo" "MAC" "Estado"
    printf -- "-\n"
    list_devices
}

# Função principal
main() {
    power_on

    choice=$(main_menu | fzf --prompt="󰂯 Bluetooth " \
        --height=~50% --layout=reverse --border --margin=1 \
        --ansi --header="Pressione ESC para sair | TAB para selecionar múltiplos")

    [[ -z "$choice" ]] && exit 0

    # Extrai os campos
    action_name=$(echo "$choice" | awk '{print $1" "$2}')
    mac=$(echo "$choice" | awk '{print $3}')
    name=$(echo "$choice" | cut -d ' ' -f 1 --complement | awk '{print $1,$2,$3,$4,$5,$6,$7,$8,$9,$10}')

    # Ações estáticas
    if [[ "$action_name" == "Ligar/Desligar Bluetooth" ]]; then
        if bluetoothctl show | grep -q "Powered: yes"; then
            bluetoothctl power off >> /dev/null
            send_notification "Bluetooth foi desligado."
        else
            bluetoothctl power on >> /dev/null
            send_notification "Bluetooth foi ligado."
        fi
        exit 0
    elif [[ "$action_name" == "Procurar novos" ]]; then
        kitty --title "Procura Bluetooth" sh -c "echo 'A procurar por dispositivos... Pressione Ctrl+C para parar.'; bluetoothctl scan on" &
        exit 0
    elif [[ "$action_name" == "Remover um" ]]; then
        device_to_remove=$(bluetoothctl devices | cut -d' ' -f2- | fzf --prompt="Selecione um dispositivo para REMOVER: " --height=~25%)
        [[ -n "$device_to_remove" ]] || exit 0
        mac_to_remove=$(echo "$device_to_remove" | awk '{print $1}')
        name_to_remove=$(echo "$device_to_remove" | cut -d' ' -f2-)
        bluetoothctl remove "$mac_to_remove" >> /dev/null
        send_notification "Dispositivo removido: $name_to_remove"
        exit 0
    fi

    # Ações para dispositivos específicos
    info=$(bluetoothctl info "$mac")
    if echo "$info" | grep -q "Connected: yes"; then
        bluetoothctl disconnect "$mac" >> /dev/null
        send_notification "Desconectado de: $name"
    else
        send_notification "A conectar a: $name..."
        if bluetoothctl connect "$mac" >> /dev/null; then
            send_notification "Conectado com sucesso!"
        else
            send_notification "Falhou. A tentar emparelhar..."
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
