const express = require('express');
const http = require('http');
const { Server } = require("socket.io");

const app = express();
const server = http.createServer(app);
const io = new Server(server);
const PORT = 3000;

app.get('/', (req, res) => {
  res.sendFile(__dirname + '/index.html');
});

// --- (NOVO) Duas filas de espera ---
let waitingTextSocketId = null;
let waitingVideoSocketId = null;

// --- (NOVA) Lógica de pareamento de TEXTO ---
function findTextPartner(socket) {
  console.log(`Socket ${socket.id} está procurando um parceiro de TEXTO.`);
  
  if (waitingTextSocketId) {
    const partnerId = waitingTextSocketId;
    const partner = io.sockets.sockets.get(partnerId);
    waitingTextSocketId = null; // Limpa a fila

    if (!partner) {
      // Parceiro desconectou
      waitingTextSocketId = socket.id;
      socket.emit('status', 'Aguardando um parceiro de texto...');
      return;
    }
    
    console.log(`Pareando (texto) ${socket.id} com ${partner.id}`);
    const room = `${socket.id}#${partner.id}`;
    
    partner.join(room);
    socket.join(room);
    partner.currentRoom = room;
    socket.currentRoom = room;

    // Avisa os dois que o chat de TEXTO começou
    io.to(room).emit('chat_start', { type: 'text' });

  } else {
    // Entra na fila de texto
    waitingTextSocketId = socket.id;
    socket.emit('status', 'Aguardando um parceiro de texto...');
  }
}

// --- (NOVA) Lógica de pareamento de VÍDEO ---
function findVideoPartner(socket) {
  console.log(`Socket ${socket.id} está procurando um parceiro de VÍDEO.`);

  if (waitingVideoSocketId) {
    const partnerId = waitingVideoSocketId;
    const partner = io.sockets.sockets.get(partnerId);
    waitingVideoSocketId = null; // Limpa a fila

    if (!partner) {
      // Parceiro desconectou
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
    
    // Avisa os dois que o chat de VÍDEO começou
    // 'partner' (que estava esperando) é o 'isCaller'
    partner.emit('chat_start', { type: 'video', isCaller: true });
    socket.emit('chat_start', { type: 'video', isCaller: false });

  } else {
    // Entra na fila de vídeo
    waitingVideoSocketId = socket.id;
    socket.emit('status', 'Aguardando um parceiro de vídeo...');
  }
}

io.on('connection', (socket) => {
  console.log(`Um usuário se conectou: ${socket.id}`);

  // --- (MODIFICADO) O cliente agora diz o que quer ---
  socket.on('find_partner', (data) => {
    // Limpa salas antigas (garantia)
    if (socket.currentRoom) {
      socket.leave(socket.currentRoom);
      socket.currentRoom = null;
    }
    
    if (data.type === 'text') {
      findTextPartner(socket);
    } else if (data.type === 'video') {
      findVideoPartner(socket);
    }
  });

  // --- (Lógica de Desconexão - MODIFICADA) ---
  socket.on('disconnect', () => {
    console.log(`Usuário desconectou: ${socket.id}`);
    
    // Se estava na fila de TEXTO
    if (socket.id === waitingTextSocketId) {
      waitingTextSocketId = null;
      console.log('Usuário da fila de TEXTO saiu.');
    }
    
    // Se estava na fila de VÍDEO
    if (socket.id === waitingVideoSocketId) {
      waitingVideoSocketId = null;
      console.log('Usuário da fila de VÍDEO saiu.');
    }

    // Se estava em um chat, avisa o parceiro
    const room = socket.currentRoom;
    if (room) {
      console.log(`Parceiro de ${socket.id} foi desconectado.`);
      socket.to(room).emit('partner_disconnected', 'O seu parceiro desconectou.');
    }
  });

  // --- (Handlers de Sinalização e Chat - SEM MUDANÇAS) ---
  // O servidor não se importa com o tipo de chat para retransmitir
  
  socket.on('nova_mensagem', (msg) => { /* ... (idêntico ao anterior) ... */ });
  socket.on('webrtc_offer', (offer) => { /* ... (idêntico ao anterior) ... */ });
  socket.on('webrtc_answer', (answer) => { /* ... (idêntico ao anterior) ... */ });
  socket.on('webrtc_ice_candidate', (candidate) => { /* ... (idêntico ao anterior) ... */ });
});

server.listen(PORT, () => {
  console.log(`Servidor rodando na porta ${PORT}`);
});