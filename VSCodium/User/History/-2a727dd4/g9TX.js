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

// Nossa "fila" de espera. Vai guardar o socket do usuário que está esperando.
let waitingSocket = null;

io.on('connection', (socket) => {
  console.log(`Um usuário se conectou: ${socket.id}`);

  // 1. Lógica de Matchmaking
  if (waitingSocket) {
    // ACHAMOS UM PAR! (O 'waitingSocket' é o parceiro)
    console.log(`Pareando ${socket.id} com ${waitingSocket.id}`);
    const partner = waitingSocket;
    waitingSocket = null; // Limpa a fila

    // Cria uma sala privada só para eles
    // O nome da sala pode ser a combinação dos IDs
    const room = `${socket.id}#${partner.id}`;
    
    // Coloca os dois na sala
    partner.join(room);
    socket.join(room);
    
    // Guarda a referência da sala em cada socket
    partner.currentRoom = room;
    socket.currentRoom = room;

    // Avisa os dois que o chat começou
    io.to(room).emit('chat_start', 'Você está conectado com um desconhecido!');

  } else {
    // NÃO TEM PAR. Coloca o usuário na fila de espera.
    console.log(`Usuário ${socket.id} está esperando na fila.`);
    waitingSocket = socket;
    socket.emit('status', 'Aguardando um parceiro...');
  }

  // 2. Lógica de Mensagens
  socket.on('nova_mensagem', (msg) => {
    // Envia a mensagem APENAS para a sala privada dele
    // 'socket.to' envia para todos na sala, MENOS para o próprio remetente
    if (socket.currentRoom) {
      socket.to(socket.currentRoom).emit('mensagem_recebida', msg);
    }
  });

  // 3. Lógica de Desconexão (Importante!)
  socket.on('disconnect', () => {
    console.log(`Usuário desconectou: ${socket.id}`);
    
    // Se o usuário que desconectou estava na fila, limpa a fila
    if (socket === waitingSocket) {
      waitingSocket = null;
      console.log('Usuário da fila saiu.');
      return; // Sai da função
    }

    // Se o usuário estava em um chat, avisa o parceiro
    const room = socket.currentRoom;
    if (room) {
      console.log(`Parceiro de ${socket.id} foi desconectado.`);
      // Avisa o outro usuário na sala
      socket.to(room).emit('partner_disconnected', 'O seu parceiro desconectou.');
      // O ideal aqui seria também forçar a saída do outro da sala
    }
  });
});

server.listen(PORT, () => {
  console.log(`Servidor rodando na porta ${PORT}`);
});