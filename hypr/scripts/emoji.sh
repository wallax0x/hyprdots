#!/usr/bin/env bash

# =============================================================================
# Seletor de Emojis Minimalista para Hyprland
# Requisitos: rofi, wl-copy (wl-clipboard), wtype
# =============================================================================

# Lista de Emojis (Adicione ou remova conforme desejar)
# Formato: "Emoji Descrição"
EMOJIS="😀 Riso
😃 Riso com olhos abertos
😄 Riso com olhos sorridentes
😁 Riso radiante
😆 Riso fechado
😅 Riso com suor frio
🤣 Rolar de rir
😂 Chorar de rir
🙂 Sorriso leve
🙃 Sorriso invertido
😉 Piscadela
😊 Sorriso com bochechas
😇 Anjo
🥰 Rosto com corações
😍 Olhos de coração
🤩 Estrelas nos olhos
😘 Beijo de coração
😗 Beijo
☺️ Sorriso clássico
😚 Beijo de olhos fechados
😙 Beijo sorridente
😋 Saboreando comida
😛 Língua para fora
😜 Língua e piscadela
🤪 Rosto louco
😝 Língua (fechado)
🤑 Rosto de dinheiro
🤗 Abraço
🤭 Mão na boca
🤫 Silêncio
🤔 Pensativo
🤐 Boca fechada
🤨 Sobrancelha levantada
😐 Neutro
😑 Sem expressão
😶 Sem boca
😏 Sorriso malicioso
😒 Insatisfeito
🙄 Olhos revirados
😬 Careta
🤥 Mentiroso
😌 Aliviado
😔 Pensativo/Triste
😪 Sonolento
🤤 Babando
😴 Dormindo
😷 Máscara
🤒 Termómetro
🤕 Ligadura
🤢 Náuseas
🤮 Vomitar
🤧 Espirro
🥵 Calor
🥶 Frio
🥴 Atordoado
😵 Tonto
🤯 Cabeça explodindo
🤠 Cowboy
🥳 Festa
😎 Óculos de sol
🤓 Nerd
🧐 Monóculo
😕 Confuso
😟 Preocupado
🙁 Triste
😮 Boca aberta
😯 Espanto
😲 Admirado
😳 Envergonhado
🥺 Olhos de súplica
😦 Boquiaberto
😧 Angustiado
😨 Medo
😰 Ansiedade
😥 Triste mas aliviado
😢 Choro suave
😭 Choro forte
😱 Grito de medo
😖 Constrangido
😣 Perseverança
😞 Deceção
😓 Suor frio
😩 Exausto
😫 Cansado
🥱 Bocejo
😤 Triunfo
😡 Raiva
😠 Zangado
🤬 Palavrões
😈 Diabinho
👿 Demónio
💀 Caveira
☠️ Caveira e ossos
💩 Cocó
🤡 Palhaço
👹 Ogro
👺 Goblin
👻 Fantasma
👽 Alien
👾 Monstro de jogo
🤖 Robot
😺 Gato sorridente
😸 Gato risonho
😻 Gato com olhos de coração
👋 Aceno
👌 OK
🤌 Gesto italiano
✌️ Vitória
🤞 Dedos cruzados
🤟 Te amo
🤘 Rock on
🤙 Chamada
👈 Aponta esquerda
👉 Aponta direita
👆 Aponta cima
🖕 Dedo do meio
👇 Aponta baixo
☝️ Um
👍 Fixe / Like
👎 Mau / Dislike
✊ Punho
👊 Soco
👏 Palmas
🙌 Mãos para cima
👐 Mãos abertas
🤲 Oração
🤝 Aperto de mãos
🙏 Rezar
✍️ Escrever
💅 Unhas
🤳 Selfie
💪 Bíceps
🦾 Braço robótico
🦵 Perna
🦿 Perna robótica
🦶 Pé
👂 Orelha
🦻 Aparelho auditivo
👃 Nariz
🧠 Cérebro
🫀 Coração (orgão)
🫁 Pulmões
🦷 Dente
🦴 Osso
👀 Olhos
👁️ Olho
👅 Língua
👄 Boca
💋 Beijo (marca)
🩸 Gota de sangue
❤️ Coração Vermelho
🧡 Coração Laranja
💛 Coração Amarelo
💚 Coração Verde
💙 Coração Azul
💜 Coração Roxo
🖤 Coração Preto
🤍 Coração Branco
🤎 Coração Castanho
💔 Coração Partido
🔥 Fogo
✨ Brilhos
⭐ Estrela
🌟 Estrela brilhante
⚡ Raio
☀️ Sol
☁️ Nuvem
🍎 Maçã
🍕 Pizza
🍔 Hambúrguer
🍺 Cerveja
☕ Café
🚀 Foguete
💻 Computador
💡 Lâmpada
✅ Check
❌ Cruz"

# --- Execução ---

# 1. Mostra o menu Rofi e captura a linha selecionada
SELECTED=$(echo -e "$EMOJIS" | rofi -dmenu -i -p "Emoji " -theme-str 'window {width: 400px;}')

# 2. Se nada foi selecionado (Esc), sai do script
if [ -z "$SELECTED" ]; then
    exit 0
fi

# 3. Extrai apenas o emoji (o primeiro caractere/sequência antes do primeiro espaço)
EMOJI=$(echo "$SELECTED" | awk '{print $1}')

# 4. Copia para a área de transferência (Wayland)
echo -n "$EMOJI" | wl-copy

# 5. Tenta digitar o emoji automaticamente usando wtype
# Adicionamos um pequeno delay para dar tempo de focar a janela anterior
sleep 0.2
wtype "$EMOJI"

# Notificação opcional
# notify-send "Emoji Copiado" "$EMOJI foi inserido e copiado." -t 2000