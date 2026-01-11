const express = require('express');
const http = require('http');
const { Server } = require("socket.io");

const app = express();
const server = http.createServer(app);
const io = new Server(server);
const PORT = 3000;

// 1. Rotas do Servidor
// Serve o HTML principal
app.get('/', (req, res) => {
  res.sendFile(__dirname + '/index.html');
});

// Serve o arquivo CSS
app.get('/style.css', (req, res) => {
  res.sendFile(__dirname + '/style.css');
});

// --- (NOVA ROTA PARA O SVG) ---
app.get('/logo.svg', (req, res) => {
  res.sendFile(__dirname + '/logo.svg', {
    headers: { 'Content-Type': 'image/svg+xml' }
  });
});

// Serve o arquivo JavaScript do cliente
app.get('/client.js', (req, res) => {
  res.sendFile(__dirname + '/client.js');
});

// --- Fim das Rotas ---


// 2. Lógica de Filas de Espera
// Duas filas separadas: uma para texto, uma para vídeo.
let waitingTextSocketId = null;
let waitingVideoSocketId = null;

/**
 * Tenta encontrar um parceiro de TEXTO para o socket.
 * Se encontrar, cria uma sala privada. Se não, coloca na fila.
 */
function findTextPartner(socket) {
  console.log(`Socket ${socket.id} está procurando um parceiro de TEXTO.`);
  
  if (waitingTextSocketId) {
    const partnerId = waitingTextSocketId;
    const partner = io.sockets.sockets.get(partnerId);
    waitingTextSocketId = null; // Limpa a fila

    // Verifica se o parceiro que estava esperando ainda está conectado
    if (!partner) {
      console.log(`Parceiro ${partnerId} não encontrado. Colocando ${socket.id} na fila.`);
      waitingTextSocketId = socket.id;
      socket.emit('status', 'Aguardando um parceiro de texto...');
      return;
    }
    
    console.log(`Pareando (texto) ${socket.id} com ${partner.id}`);
    const room = `${socket.id}#${partner.id}`;
    
    // Coloca os dois na mesma sala
    partner.join(room);
    socket.join(room);
    partner.currentRoom = room;
    socket.currentRoom = room;

    // Avisa os dois que o chat começou
    io.to(room).emit('chat_start', { type: 'text' });

  } else {
    // Ninguém na fila, este socket vai esperar
    waitingTextSocketId = socket.id;
    socket.emit('status', 'Aguardando um parceiro de texto...');
  }
}

/**
 * Tenta encontrar um parceiro de VÍDEO para o socket.
 * Se encontrar, cria uma sala privada. Se não, coloca na fila.
 */
function findVideoPartner(socket) {
  console.log(`Socket ${socket.id} está procurando um parceiro de VÍDEO.`);

  if (waitingVideoSocketId) {
    const partnerId = waitingVideoSocketId;
    const partner = io.sockets.sockets.get(partnerId);
    waitingVideoSocketId = null; // Limpa a fila

    if (!partner) {
      console.log(`Parceiro ${partnerId} não encontrado. Colocando ${socket.id} na fila.`);
      waitingVideoSocketId = socket.id;
      socket.emit('status', 'Aguardando um parceiro de vídeo...');
      return;
    }
    
    console.log(`Pareando (vídeo) ${socket.id} com ${partner.id}`);
    const room = `${socket.id}#${partner.id}`;
    
    partner.join(room);
    socket.join(room);
    partner.currentRoom = room;
    socket.currentRoom = room;
    
    // Avisa os dois, definindo quem será o "chamador" (isCaller)
    // O 'partner' (que estava esperando) é quem inicia a oferta (Offer)
    partner.emit('chat_start', { type: 'video', isCaller: true });
    socket.emit('chat_start', { type: 'video', isCaller: false });

  } else {
    // Ninguém na fila, este socket vai esperar
    waitingVideoSocketId = socket.id;
    socket.emit('status', 'Aguardando um parceiro de vídeo...');
  }
}
// Fim da Lógica de Filas


// --- 3. Lógica de Conexão Principal ---
io.on('connection', (socket) => {
  console.log(`Um usuário se conectou: ${socket.id}`);

  // --- Handlers de Gerenciamento de Sala ---
  
  /**
   * Ouve o pedido do cliente para encontrar um parceiro.
   * 'data' deve ser { type: 'text' } ou { type: 'video' }
   */
  socket.on('find_partner', (data) => {
    // Verificação de segurança (correção do bug anterior)
    if (!data || !data.type) {
      console.log(`Socket ${socket.id} enviou um pedido inválido de 'find_partner'.`);
      return;
    }

    // Garante que o socket não esteja em nenhuma sala antiga
    if (socket.currentRoom) {
      socket.leave(socket.currentRoom);
      socket.currentRoom = null;
    }
    
    // Encaminha para a fila correta
    if (data.type === 'text') {
      findTextPartner(socket);
    } else if (data.type === 'video') {
      findVideoPartner(socket);
    }
  });

  /**
   * Ouve o evento "Pular" (botão "Próximo")
   */
  socket.on('leave_room', () => {
    const room = socket.currentRoom;
    if (room) {
      console.log(`Socket ${socket.id} pulou da sala ${room}`);
      // Avisa o parceiro que o usuário pulou
      socket.to(room).emit('partner_disconnected', 'O seu parceiro pulou.');
      socket.leave(room);
      socket.currentRoom = null;
    }
  });

  /**
   * Lida com a desconexão do usuário (fechar a aba)
   */
  socket.on('disconnect', () => {
    console.log(`Usuário desconectou: ${socket.id}`);
    
    // Remove o usuário de qualquer fila de espera em que ele esteja
    if (socket.id === waitingTextSocketId) {
      waitingTextSocketId = null;
      console.log('Usuário da fila de TEXTO saiu.');
    }
    if (socket.id === waitingVideoSocketId) {
      waitingVideoSocketId = null;
      console.log('Usuário da fila de VÍDEO saiu.');
    }

    // Se estava em uma sala, avisa o parceiro
    const room = socket.currentRoom;
    if (room) {
      console.log(`Parceiro de ${socket.id} foi desconectado.`);
      socket.to(room).emit('partner_disconnected', 'O seu parceiro desconectou.');
    }
  });

  // --- Handlers de Chat de Texto ---
  socket.on('nova_mensagem', (msg) => {
    if (socket.currentRoom) {
      // Envia a mensagem para todos na sala, *exceto* o remetente
      socket.to(socket.currentRoom).emit('mensagem_recebida', msg);
    }
  });
  
  // --- (NOVO) Handlers de Mídia ---
  /**
   * Ouve o status de mídia (mute/unmute, video on/off)
   * 'data' será algo como { type: 'audio', enabled: false }
   */
  socket.on('media_status_change', (data) => {
    if (socket.currentRoom) {
      console.log(`Socket ${socket.id} mudou status de mídia: ${data.type} = ${data.enabled}`);
      // Retransmite a informação para o parceiro
      socket.to(socket.currentRoom).emit('partner_media_status_changed', data);
    }
  });
  // --- FIM DA NOVA SEÇÃO ---

  // --- Handlers de Sinalização WebRTC (Relay) ---
  // O servidor apenas retransmite essas mensagens de um lado para o outro.
  
  socket.on('webrtc_offer', (offer) => {
    if (socket.currentRoom) {
      socket.to(socket.currentRoom).emit('webrtc_offer', offer);
    }
  });
  
  socket.on('webrtc_answer', (answer) => {
    if (socket.currentRoom) {
      socket.to(socket.currentRoom).emit('webrtc_answer', answer);
    }
  });
  
  socket.on('webrtc_ice_candidate', (candidate) => {
    if (socket.currentRoom) {
      socket.to(socket.currentRoom).emit('webrtc_ice_candidate', candidate);
    }
  });
});
// --- Fim da Lógica de Conexão ---


// --- 4. Iniciar o Servidor ---
server.listen(PORT, () => {
  console.log(`Servidor rodando na porta ${PORT}`);
});