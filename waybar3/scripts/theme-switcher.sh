#!/usr/bin/env bash

# --- DIRETÓRIOS DE ESTILO (A parte do JSONC foi removida) ---
WAYBAR_CSS_DIR="$HOME/.config/waybar/themes/css"
WAYBAR_CSS_FILE="$HOME/.config/waybar/theme.css"
ROFI_THEMES_DIR="$HOME/.config/rofi/themes"
ROFI_THEME_FILE="$HOME/.config/rofi/theme.rasi"
CURRENT_THEME_FILE="$HOME/.config/waybar/themes/current-theme"

# Verifica se os diretórios de ESTILO existem
for dir in "$WAYBAR_CSS_DIR" "$ROFI_THEMES_DIR"; do
  [[ ! -d "$dir" ]] && echo "Error: $dir not found" && exit 1
done

# Pega todos os temas de estilo
waybar_css=("$WAYBAR_CSS_DIR"/*.css)
rofi_themes=("$ROFI_THEMES_DIR"/*.rasi)

if [[ ${#waybar_css[@]} -eq 0 || ${#rofi_themes[@]} -eq 0 ]]; then
  echo "Error: No style themes found in one of the directories"
  exit 1
fi

# Pega o tema atual
current_theme=$(cat "$CURRENT_THEME_FILE" 2>/dev/null || echo "")

# Encontra o índice do próximo tema na lista
next_theme_index=0
for i in "${!waybar_css[@]}"; do
  [[ "${waybar_css[$i]}" == "$current_theme" ]] && next_theme_index=$(((i + 1) % ${#waybar_css[@]})) && break
done

# Define os novos arquivos de tema de ESTILO
new_waybar_css="${waybar_css[$next_theme_index]}"
new_rofi_theme="${rofi_themes[$next_theme_index]}"

# Salva o novo tema atual para a próxima execução
echo "$new_waybar_css" >"$CURRENT_THEME_FILE"

# Mapeia os arquivos de origem para os de destino (sem o JSONC)
declare -A theme_files=(
  ["$new_waybar_css"]="$WAYBAR_CSS_FILE"
  ["$new_rofi_theme"]="$ROFI_THEME_FILE"
)

# Copia os novos arquivos de estilo
for src in "${!theme_files[@]}"; do
  cp "$src" "${theme_files[$src]}"
done

# Reinicia a Waybar para aplicar as mudanças de estilo
# Ela usará seu config.jsonc permanente
pkill waybar 2>/dev/null || true
nohup waybar >/dev/null 2>&1 &