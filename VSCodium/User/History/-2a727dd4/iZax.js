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

  // ---- (Código Antigo da Fase 1) ----
  // socket.emit('bem_vindo', 'Seja bem-vindo ao chat!');
  
  // ---- NOVA SEÇÃO (FASE 2) ----
  // Ouve o evento 'nova_mensagem' vindo do cliente
  socket.on('nova_mensagem', (msg) => {
    console.log('Mensagem recebida:', msg);
    
    // Retransmite a mensagem para TODOS os clientes conectados
    // usando o evento 'mensagem_recebida'
    io.emit('mensagem_recebida', msg);
  });
  // ---- FIM DA NOVA SEÇÃO ----

  socket.on('disconnect', () => {
    console.log('Usuário desconectou (ID: ' + socket.id + ')');
  });
});

server.listen(PORT, () => {
  console.log(`Servidor rodando na porta ${PORT}`);
});