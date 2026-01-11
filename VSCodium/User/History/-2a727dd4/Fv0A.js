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

// Nossa "fila" de espera. Vai guardar o ID do socket que está esperando.
let waitingSocketId = null;

function findPartner(socket) {
  console.log(`Socket ${socket.id} está procurando um parceiro.`);
  
  // Limpa qualquer sala antiga que o socket possa ter
  if (socket.currentRoom) {
    socket.leave(socket.currentRoom);
    socket.currentRoom = null;
  }
  
  if (waitingSocketId) {
    // ACHAMOS UM PAR!
    const partnerId = waitingSocketId;
    const partner = io.sockets.sockets.get(partnerId);
    waitingSocketId = null; // Limpa a fila

    if (!partner) {
      // O parceiro que estava esperando desconectou no meio do caminho
      // Coloca o socket atual na fila
      console.log(`Parceiro ${partnerId} não encontrado. Colocando ${socket.id} na fila.`);
      waitingSocketId = socket.id;
      socket.emit('status', 'Aguardando um parceiro...');
      return;
    }
    
    console.log(`Pareando ${socket.id} com ${partner.id}`);

    // Cria uma sala privada só para eles
    const room = `${socket.id}#${partner.id}`;
    
    partner.join(room);
    socket.join(room);
    
    partner.currentRoom = room;
    socket.currentRoom = room;

    // Avisa os dois que o chat começou
    // O chamador (partner) é quem estava esperando
    partner.emit('chat_start', {
      message: 'Você está conectado! Você iniciará a chamada.',
      isCaller: true // Ele estava na fila, ele vai criar a "oferta"
    });
    // O "chamado" (socket) é quem acabou de entrar
    socket.emit('chat_start', {
      message: 'Você está conectado! Aguardando o parceiro...',
      isCaller: false // Ele vai receber a "oferta"
    });

  } else {
    // NÃO TEM PAR. Coloca o usuário na fila de espera.
    console.log(`Usuário ${socket.id} está esperando na fila.`);
    waitingSocketId = socket.id;
    socket.emit('status', 'Aguardando um parceiro...');
  }
}

io.on('connection', (socket) => {
  console.log(`Um usuário se conectou: ${socket.id}`);

  // O cliente agora pede para encontrar um parceiro
  socket.on('find_partner', () => {
    findPartner(socket);
  });

  // 2. Lógica de Mensagens (sem mudanças)
  socket.on('nova_mensagem', (msg) => {
    if (socket.currentRoom) {
      socket.to(socket.currentRoom).emit('mensagem_recebida', msg);
    }
  });

  // --- (3. Handlers de Sinalização WebRTC - sem mudanças) ---
  // O servidor apenas retransmite os sinais para a sala privada

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
  // --- FIM DOS HANDLERS ---

  // 4. Lógica de Desconexão (MODIFICADA)
  socket.on('disconnect', () => {
    console.log(`Usuário desconectou: ${socket.id}`);
    
    // Se o usuário que desconectou estava na fila, limpa a fila
    if (socket.id === waitingSocketId) {
      waitingSocketId = null;
      console.log('Usuário da fila saiu.');
    }

    // Se o usuário estava em um chat, avisa o parceiro
    const room = socket.currentRoom;
    if (room) {
      console.log(`Parceiro de ${socket.id} foi desconectado.`);
      socket.to(room).emit('partner_disconnected', 'O seu parceiro desconectou.');
    }
  });
});

server.listen(PORT, () => {
  console.log(`Servidor rodando na porta ${PORT}`);
});