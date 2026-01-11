#!/usr/bin/env bash
#
# Gentoo update script
# by mag0 + GPT-5 😎
#
# Atualiza repositórios e pacotes do sistema
# Mostra progresso com cores e notificações
#

green='\033[1;32m'
blue='\033[1;34m'
yellow='\033[1;33m'
red='\033[1;31m'
reset='\033[0m'

LOGFILE="$HOME/.local/share/gentoo-update.log"
mkdir -p "$(dirname "$LOGFILE")"

# Função para mostrar mensagens coloridas
msg() {
    echo -e "${blue}==>${reset} $1"
}

msg_success() {
    echo -e "${green}✔${reset} $1"
}

msg_warn() {
    echo -e "${yellow}⚠${reset} $1"
}

msg_error() {
    echo -e "${red}✖${reset} $1"
}

# Verifica se o usuário é root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        msg_error "Não execute como root! Use sudo apenas quando solicitado."
        exit 1
    fi
}

# Sincroniza repositórios
sync_repos() {
    msg "Sincronizando repositórios..."
    sudo emerge --sync | tee -a "$LOGFILE"
    if [[ ${PIPESTATUS[0]} -eq 0 ]]; then
        msg_success "Repositórios sincronizados com sucesso!"
    else
        msg_error "Falha ao sincronizar repositórios!"
        exit 1
    fi
}

# Verifica atualizações
check_updates() {
    msg "Verificando atualizações disponíveis..."
    updates=$(emerge -puDNav @world 2>/dev/null | grep -c "^\[ebuild")
    echo "$updates"
}

# Atualiza pacotes
update_system() {
    msg "Atualizando sistema..."
    sudo emerge -uDNav @world | tee -a "$LOGFILE"
    msg_success "Atualização concluída!"
}

# Limpa pacotes órfãos e cache
clean_system() {
    msg "Limpando pacotes órfãos e cache..."
    sudo emerge --depclean -a | tee -a "$LOGFILE"
    sudo eclean-dist -d | tee -a "$LOGFILE"
    msg_success "Sistema limpo!"
}

# Mostra tooltip estilo waybar
display-tooltip() {
    local updates=$1
    if (( updates > 0 )); then
        echo "{ \"text\": \" $updates\", \"tooltip\": \"Atualizações disponíveis: $updates\" }"
    else
        echo "{ \"text\": \"󰸟\", \"tooltip\": \"Nenhuma atualização disponível\" }"
    fi
}

main() {
    local action=$1
    check_root

    case "$action" in
        start)
            sync_repos
            updates=$(check_updates)

            if (( updates > 0 )); then
                msg_warn "$updates atualizações disponíveis!"
                read -rp "Deseja atualizar agora? [s/N] " ans
                [[ $ans =~ ^[SsYy]$ ]] && update_system && clean_system
            else
                msg_success "Nenhuma atualização disponível!"
            fi

            notify-send "Gentoo Update" "Atualização concluída com sucesso!" -i software-update-available
            ;;
        *)
            updates=$(check_updates)
            display-tooltip "$updates"
            ;;
    esac
}

main "$@"
