const express = require('express');
const http = require('http');
const { Server } = require("socket.io");

const app = express();
const server = http.createServer(app);
const io = new Server(server);
const PORT = 3000;

// --- Nossas Rotas ---
app.get('/', (req, res) => {
  res.sendFile(__dirname + '/index.html');
});

app.get('/style.css', (req, res) => {
  res.sendFile(__dirname + '/style.css');
});

// --- (NOVA ROTA PARA O JAVASCRIPT) ---
app.get('/client.js', (req, res) => {
  res.sendFile(__dirname + '/client.js');
});
// --- Fim das Rotas ---


// --- Lógica do Servidor ---
let waitingTextSocketId = null;
let waitingVideoSocketId = null;

function findTextPartner(socket) {
  console.log(`Socket ${socket.id} está procurando um parceiro de TEXTO.`);
  
  if (waitingTextSocketId) {
    const partnerId = waitingTextSocketId;
    const partner = io.sockets.sockets.get(partnerId);
    waitingTextSocketId = null; 

    if (!partner) {
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

    io.to(room).emit('chat_start', { type: 'text' });

  } else {
    waitingTextSocketId = socket.id;
    socket.emit('status', 'Aguardando um parceiro de texto...');
  }
}

function findVideoPartner(socket) {
  console.log(`Socket ${socket.id} está procurando um parceiro de VÍDEO.`);

  if (waitingVideoSocketId) {
    const partnerId = waitingVideoSocketId;
    const partner = io.sockets.sockets.get(partnerId);
    waitingVideoSocketId = null; 

    if (!partner) {
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
    
    partner.emit('chat_start', { type: 'video', isCaller: true });
    socket.emit('chat_start', { type: 'video', isCaller: false });

  } else {
    waitingVideoSocketId = socket.id;
    socket.emit('status', 'Aguardando um parceiro de vídeo...');
  }
}

io.on('connection', (socket) => {
  console.log(`Um usuário se conectou: ${socket.id}`);

  socket.on('find_partner', (data) => {
    
    // --- (CORREÇÃO DO BUG) ---
    // Verifica se 'data' e 'data.type' existem antes de usá-los
    if (!data || !data.type) {
      console.log(`Socket ${socket.id} enviou um pedido inválido de 'find_partner'.`);
      return; // Para a execução para evitar o crash
    }
    // --- (FIM DA CORREÇÃO) ---

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

  socket.on('disconnect', () => {
    console.log(`Usuário desconectou: ${socket.id}`);
    
    if (socket.id === waitingTextSocketId) {
      waitingTextSocketId = null;
      console.log('Usuário da fila de TEXTO saiu.');
    }
    
    if (socket.id === waitingVideoSocketId) {
      waitingVideoSocketId = null;
      console.log('Usuário da fila de VÍDEO saiu.');
    }

    const room = socket.currentRoom;
    if (room) {
      console.log(`Parceiro de ${socket.id} foi desconectado.`);
      socket.to(room).emit('partner_disconnected', 'O seu parceiro desconectou.');
    }
  });

  // --- Handlers de Sinalização e Chat ---
  
  socket.on('nova_mensagem', (msg) => {
    if (socket.currentRoom) {
      socket.to(socket.currentRoom).emit('mensagem_recebida', msg);
    }
  });
  
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

server.listen(PORT, () => {
  console.log(`Servidor rodando na porta ${PORT}`);
});