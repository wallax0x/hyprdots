#!/usr/bin/env bash
# ======================================================
# 🖥️ Hyprland Screen Recorder v2.0 (Corrigido e Melhorado)
# ======================================================
# Baseado no seu script, com correções para:
# - Deteção correta da fonte de áudio PipeWire
# - Verificação de dependências mais robusta
# - Lógica de "toggle" simplificada
# - Notificações mais claras
# ======================================================

# --- Configuração ---
DIR="$HOME/Vídeos/Gravações" # Use ~/Vídeos que é o padrão em PT-BR
FILENAME="record_$(date +'%Y-%m-%d_%H%M%S').mkv"
OUTFILE="$DIR/$FILENAME"
AUDIO=false
FULLSCREEN=false

# --- Funções ---
notify() {
    # Usa notify-send (dependência) para feedback visual
    notify-send -u low -a "Screen Recorder" "$1" "$2"
}

check_deps() {
    # Verifica se todos os comandos necessários existem
    for cmd in wf-recorder slurp notify-send pactl jq hyprctl pgrep pkill; do
        if ! command -v "$cmd" &>/dev/null; then
            notify "❌ Erro Fatal" "Dependência ausente: $cmd\nPor favor, instale-o."
            exit 1
        fi
    done
}

# --- Processamento de Argumentos ---
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --audio) AUDIO=true; shift ;;
        --fullscreen) FULLSCREEN=true; shift ;;
        # Adiciona uma opção explícita para parar, em vez de depender do toggle
        --stop)
            if pgrep -x wf-recorder >/dev/null; then
                pkill -SIGINT wf-recorder
                notify "⏹️ Gravação Encerrada" "Ficheiro salvo em $DIR"
            else
                notify "⚠️ Aviso" "Nenhuma gravação ativa para parar."
            fi
            exit 0
            ;;
        *) echo "Opção desconhecida: $1"; exit 1 ;;
    esac
done

# --- Verificação de Dependências ---
check_deps
mkdir -p "$DIR" # Cria a pasta de gravações se não existir

# --- Lógica Principal: Parar se já estiver a gravar ---
if pgrep -x wf-recorder >/dev/null; then
    notify "⚠️ Aviso" "Já existe uma gravação em curso.\nUse --stop para parar."
    exit 1
fi

# --- Seleção da Geometria ---
if $FULLSCREEN; then
    # Obtém a geometria do primeiro monitor ativo (mais robusto)
    GEOM=$(hyprctl monitors -j | jq -r '.[] | select(.focused) | "\(.x),\(.y) \(.width)x\(.height)"' | head -n 1)
    if [ -z "$GEOM" ]; then
        # Fallback se não encontrar monitor focado (raro)
        GEOM=$(hyprctl monitors -j | jq -r '.[0] | "\(.x),\(.y) \(.width)x\(.height)"')
    fi
else
    # Permite ao utilizador selecionar a área com slurp
    GEOM=$(slurp)
fi

# Se o utilizador cancelou a seleção (pressionou Esc no slurp)
if [ -z "$GEOM" ]; then
    notify "❌ Gravação Cancelada" "Nenhuma área selecionada."
    exit 1
fi

# --- Comando de Gravação ---
REC_CMD="wf-recorder -g \"$GEOM\" -f \"$OUTFILE\""

if $AUDIO; then
    # CORREÇÃO PRINCIPAL: Usa 'pactl get-default-sink' que é mais fiável com PipeWire
    SINK_MONITOR=$(pactl get-default-sink).monitor
    # Você pode querer adicionar a sua fonte de microfone também, se tiver uma:
    # SOURCE=$(pactl get-default-source)
    # REC_CMD+=" --audio=\"$SINK_MONITOR\" --audio=\"$SOURCE\""
    REC_CMD+=" --audio=\"$SINK_MONITOR\"" # Grava apenas o som do sistema por agora
    notify "⏺️ Gravando com ÁUDIO" "$FILENAME"
else
    notify "⏺️ Gravando SEM ÁUDIO" "$FILENAME"
fi

# Executa o comando em segundo plano
eval "$REC_CMD &"

echo "Gravação iniciada (PID: $!): $OUTFILE"
