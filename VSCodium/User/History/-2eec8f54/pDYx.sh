#!/usr/bin/env bash
#
# Centro de Controlo de Bluetooth para Waybar
# Usa fzf para criar um menu interativo para gerir dispositivos Bluetooth.
#
# Autor: Adaptado por Gemini para o seu sistema Gentoo
# Requisitos: bluez, fzf, libnotify (para notify-send)
# Permissões: O utilizador deve pertencer ao grupo 'lp'.

# Função para enviar notificações para o desktop
send_notification() {
    notify-send "Bluetooth" "$1" -i "network-bluetooth" -r 9991
}

# Garante que o serviço de Bluetooth está ligado
power_on() {
    if bluetoothctl show | grep -q "Powered: no"; then
        bluetoothctl power on >> /dev/null
        sleep 1
        send_notification "Bluetooth foi ligado."
    fi
}

# Menu principal gerado com fzf
main_menu() {
    # Cabeçalho do menu
    printf "   %-30s\n" "󰂯 Ligar/Desligar Bluetooth"
    printf "   %-30s\n" "󰂰 Procurar novos dispositivos"
    printf -- "-\n"

    # Obtém a lista de dispositivos e o seu estado
    bluetoothctl devices | while read -r line; do
        mac=$(echo "$line" | awk '{print $2}')
        name=$(echo "$line" | cut -d ' ' -f 3-)
        
        # Verifica se o dispositivo está conectado
        if bluetoothctl info "$mac" | grep -q "Connected: yes"; then
            printf "   %-30s %s\n" "󰂱 Desconectar: $name" "$mac"
        else
            printf "   %-30s %s\n" "󰂱 Conectar: $name" "$mac"
        fi
    done
}

# Ação principal
main() {
    power_on

    # Mostra o menu e captura a seleção do utilizador
    choice=$(main_menu | fzf --prompt="󰂯 Bluetooth " \
        --height=~50% --layout=reverse --border --margin=1 \
        --ansi --header="Pressione ESC para sair")

    # Se o utilizador pressionou ESC, sai
    if [[ -z "$choice" ]]; then
        exit 0
    fi

    # Extrai a ação e o MAC da seleção
    action=$(echo "$choice" | awk '{print $2}')
    mac=$(echo "$choice" | awk '{print $NF}')
    name=$(echo "$choice" | sed -e 's/.*: //')

    case "$action" in
        Ligar/Desligar)
            if bluetoothctl show | grep -q "Powered: yes"; then
                bluetoothctl power off >> /dev/null
                send_notification "Bluetooth foi desligado."
            else
                bluetoothctl power on >> /dev/null
                send_notification "Bluetooth foi ligado."
            fi
            ;;
        Procurar)
            # Executa a procura num novo terminal para não bloquear a barra
            kitty --title "Procura Bluetooth" sh -c "bluetoothctl scan on; read" &
            ;;
        Conectar:)
            # Primeiro, tenta conectar
            if bluetoothctl connect "$mac" >> /dev/null; then
                send_notification "Conectado a: $name"
            else
                # Se falhar, tenta emparelhar primeiro e depois conectar
                send_notification "A emparelhar com: $name..."
                if bluetoothctl pair "$mac" >> /dev/null; then
                    sleep 1
                    bluetoothctl connect "$mac" >> /dev/null
                    send_notification "Conectado a: $name"
                else
                    send_notification "Erro ao emparelhar com: $name"
                fi
            fi
            ;;
        Desconectar:)
            bluetoothctl disconnect "$mac" >> /dev/null
            send_notification "Desconectado de: $name"
            ;;
        *)
            send_notification "Ação desconhecida."
            ;;
    esac
}

main
