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

io.on('connection', (socket) => {
  console.log('Um usuário se conectou! (ID: ' + socket.id + ')');

  // --- NOVA SEÇÃO (FASE 3) ---
  // Por padrão, todo usuário entra na sala 'geral'
  const defaultRoom = 'geral';
  socket.join(defaultRoom);
  // Guardamos a sala atual no próprio objeto do socket para referência futura
  socket.currentRoom = defaultRoom; 
  console.log(`Socket ${socket.id} entrou na sala ${defaultRoom}`);

  // Ouve o evento 'join_room' vindo do cliente
  socket.on('join_room', (newRoom) => {
    // Sai da sala antiga
    socket.leave(socket.currentRoom); 
    console.log(`Socket ${socket.id} saiu da sala ${socket.currentRoom}`);
    
    // Entra na nova sala
    socket.join(newRoom); 
    socket.currentRoom = newRoom;
    console.log(`Socket ${socket.id} entrou na sala ${newRoom}`);
  });
  // --- FIM DA NOVA SEÇÃO ---

  // --- SEÇÃO MODIFICADA (FASE 2) ---
  // Agora, 'data' é um objeto: { msg, room }
  socket.on('nova_mensagem', (data) => {
    console.log(`Mensagem: '${data.msg}' na sala '${data.room}'`);
    
    // Retransmite a mensagem APENAS para a sala especificada
    io.to(data.room).emit('mensagem_recebida', data.msg);
  });
  // --- FIM DA SEÇÃO MODIFICADA ---

  socket.on('disconnect', () => {
    console.log('Usuário desconectou (ID: ' + socket.id + ')');
  });
});

server.listen(PORT, () => {
  console.log(`Servidor rodando na porta ${PORT}`);
});