#!/usr/bin/env bash
#
# Centro de Controlo de Bluetooth v2.0 para Waybar
# Usa fzf para criar um menu interativo completo para gerir dispositivos.
#
# Autor: Adaptado e melhorado por Gemini para o seu sistema Gentoo
# Funcionalidades: Ligar/Desligar, Procurar, Conectar/Desconectar, Remover, Confiar.

# Função para enviar notificações para o desktop
send_notification() {
    # Usa um ícone mais padrão para evitar avisos de "not found"
    notify-send "Bluetooth" "$1" -i "bluetooth" -r 9991
}

# Garante que o serviço de Bluetooth está ligado
power_on() {
    if bluetoothctl show | grep -q "Powered: no"; then
        bluetoothctl power on >> /dev/null
        sleep 1
    fi
}

# Menu principal gerado com fzf, agora com mais opções e status
main_menu() {
    # Opções estáticas
    printf "   %-45s\n" "󰂯 Ligar/Desligar Bluetooth"
    printf "   %-45s\n" "󰂰 Procurar novos dispositivos"
    printf "   %-45s\n" "󰂲 Remover um dispositivo"
    printf -- "-\n"
    printf "   %-20s %-17s %-15s\n" "Dispositivo" "MAC" "Estado"
    printf -- "-\n"

    # Obtém a lista de dispositivos e o seu estado
    bluetoothctl devices | while read -r line; do
        mac=$(echo "$line" | awk '{print $2}')
        name=$(echo "$line" | cut -d ' ' -f 3-)
        
        info=$(bluetoothctl info "$mac")
        if echo "$info" | grep -q "Connected: yes"; then
            status="󰂱 Conectado"
        elif echo "$info" | grep -q "Paired: yes"; then
            status="paired Emparelhado"
        else
            status="unpaired Disponível"
        fi
        printf "   %-20s %-17s %-15s\n" "$name" "$mac" "$status"
    done
}

# Ação principal
main() {
    power_on

    choice=$(main_menu | fzf --prompt="󰂯 Bluetooth " \
        --height=~50% --layout=reverse --border --margin=1 \
        --ansi --header="Pressione ESC para sair | TAB para selecionar múltiplos")

    if [[ -z "$choice" ]]; then
        exit 0
    fi

    # Extrai a ação/nome e o MAC da seleção
    action_name=$(echo "$choice" | awk '{print $1" "$2}')
    mac=$(echo "$choice" | awk '{print $3}') # Agora o MAC é a 3ª coluna
    name=$(echo "$choice" | sed -e 's/   \S* \S*//' | sed -e 's/ \S*$//' | sed 's/ *$//g' )

    # Lida com as opções estáticas
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
        # Pede ao utilizador para selecionar um dispositivo para remover
        device_to_remove=$(bluetoothctl devices | cut -d' ' -f2- | fzf --prompt="Selecione um dispositivo para REMOVER: " --height=~25%)
        if [[ -n "$device_to_remove" ]]; then
            mac_to_remove=$(echo "$device_to_remove" | awk '{print $1}')
            name_to_remove=$(echo "$device_to_remove" | cut -d' ' -f2-)
            bluetoothctl remove "$mac_to_remove" >> /dev/null
            send_notification "Dispositivo removido: $name_to_remove"
        fi
        exit 0
    fi
    
    # Lida com as ações para dispositivos específicos
    info=$(bluetoothctl info "$mac")
    if echo "$info" | grep -q "Connected: yes"; then
        # Ação para desconectar
        bluetoothctl disconnect "$mac" >> /dev/null
        send_notification "Desconectado de: $name"
    else
        # Ação para conectar (e emparelhar/confiar se necessário)
        send_notification "A conectar a: $name..."
        if bluetoothctl connect "$mac" >> /dev/null; then
            send_notification "Conectado com sucesso!"
        else
            # Se a conexão direta falhar, tenta emparelhar
            send_notification "Falhou. A tentar emparelhar..."
            if bluetoothctl pair "$mac" >> /dev/null; then
                sleep 1
                # Depois de emparelhar, confia e tenta conectar novamente
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
