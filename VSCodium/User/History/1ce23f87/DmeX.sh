#!/usr/bin/env bash
# ------------------------------------------------------
# 🖥️ Hyprland Screen Recorder (wf-recorder + slurp)
# ------------------------------------------------------

# Diretório de gravações
DIR="$HOME/Pictures/Recordings"
mkdir -p "$DIR"

# Nome do arquivo de saída
OUTFILE="$DIR/record_$(date +'%Y-%m-%d_%H-%M-%S').mp4"

# Verifica se já há gravação ativa
if pgrep -x wf-recorder >/dev/null; then
    # Encerra gravação atual
    pkill -SIGINT wf-recorder
    notify-send "⏹️ Gravação encerrada" "Arquivo salvo em $DIR"
else
    # Seleciona área e inicia gravação
    AREA=$(slurp)
    if [ -n "$AREA" ]; then
        wf-recorder -g "$AREA" -f "$OUTFILE" &
        notify-send "⏺️ Gravando área selecionada" "$OUTFILE"
    else
        notify-send "❌ Gravação cancelada" "Nenhuma área selecionada"
    fi
fi
