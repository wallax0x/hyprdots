    const socket = io();

    // --- Elementos do Lobby ---
    const lobbyContainer = document.getElementById('lobby-container');
    const lobbyStatus = document.getElementById('lobby-status');
    const findTextChatBtn = document.getElementById('findTextChat');
    const findVideoChatBtn = document.getElementById('findVideoChat');
    
    // --- Elementos da Chamada ---
    const callContainer = document.getElementById('call-container');
    const videoContainer = document.getElementById('video-container');

    // --- Elementos do Chat ---
    const statusDiv = document.getElementById('status');
    const messages = document.getElementById('messages');
    const form = document.getElementById('form');
    const input = document.getElementById('input');

    // --- Elementos de Vídeo ---
    const localVideo = document.getElementById('localVideo');
    const remoteVideo = document.getElementById('remoteVideo');

    // --- Variáveis Globais de WebRTC ---
    let peerConnection;
    let localStream;
    const configuration = {
      iceServers: [ { urls: 'stun:stun.l.google.com:19302' }, { urls: 'stun:stun1.l.google.com:19302' } ]
    };

    // --- Lógica dos Botões do Lobby ---
    
    findTextChatBtn.addEventListener('click', () => {
      socket.emit('find_partner', { type: 'text' });
      lobbyStatus.textContent = 'Procurando um parceiro para chat de texto...';
      disableLobbyButtons();
    });

    findVideoChatBtn.addEventListener('click', async () => {
      try {
        await getLocalMedia();
        lobbyStatus.textContent = 'Procurando um parceiro para vídeo chat...';
        disableLobbyButtons();
        socket.emit('find_partner', { type: 'video' });
      } catch (err) {
        console.error('Erro ao acessar mídia:', err);
        lobbyStatus.textContent = 'Erro: Você precisa permitir o acesso à câmera e ao microfone.';
      }
    });
    
    function disableLobbyButtons() {
      findTextChatBtn.disabled = true;
      findVideoChatBtn.disabled = true;
    }
    
    function enableLobbyButtons() {
      findTextChatBtn.disabled = false;
      findVideoChatBtn.disabled = false;
      lobbyStatus.textContent = '';
    }

    // --- Funções do Chat de Texto ---
    function addMessage(text, type = 'partner') {
      const item = document.createElement('li');
      item.className = type;
      item.textContent = text;
      messages.appendChild(item);
      messages.scrollTop = messages.scrollHeight;
    }
    
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      if (!input.value) return;
      socket.emit('nova_mensagem', input.value);
      addMessage(input.value, 'me'); 
      input.value = '';
    });

    // --- Funções de WebRTC ---

    async function getLocalMedia() {
      if (localStream) return;
      localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      localVideo.srcObject = localStream;
    }

    function initializePeerConnection() {
      peerConnection = new RTCPeerConnection(configuration);

      localStream.getTracks().forEach(track => {
        peerConnection.addTrack(track, localStream);
      });

      peerConnection.ontrack = (event) => {
        remoteVideo.srcObject = event.streams[0];
      };

      peerConnection.onicecandidate = (event) => {
        if (event.candidate) {
          socket.emit('webrtc_ice_candidate', event.candidate);
        }
      };
    }
    
    async function createOffer() {
      const offer = await peerConnection.createOffer();
      await peerConnection.setLocalDescription(offer);
      socket.emit('webrtc_offer', offer);
    }

    function stopChat() {
      addMessage(`--- Desconectado ---`, 'partner');
      
      if (peerConnection) {
        peerConnection.close();
        peerConnection = null;
      }
      if(localStream) {
        localStream.getTracks().forEach(track => track.stop());
        localStream = null;
      }
      localVideo.srcObject = null;
      remoteVideo.srcObject = null;
      
      callContainer.style.display = 'none';
      lobbyContainer.style.display = 'block';
      enableLobbyButtons();
    }

    // --- Lógica de Sinalização via Socket.IO ---
    
    socket.on('status', (msg) => {
      lobbyStatus.textContent = msg;
    });

    socket.on('chat_start', async (data) => {
      lobbyContainer.style.display = 'none';
      callContainer.style.display = 'flex';
      form.classList.remove('disabled');
      messages.innerHTML = '';
      
      if (data.type === 'video') {
        videoContainer.style.display = 'block';
        statusDiv.textContent = 'Conectado com vídeo!';
        
        initializePeerConnection(); 
        if (data.isCaller) {
          await createOffer();
        }
      } else {
        videoContainer.style.display = 'none';
        statusDiv.textContent = 'Conectado (somente texto)!';
      }
    });

    socket.on('partner_disconnected', (msg) => {
      addMessage(`--- ${msg} ---`, 'partner');
      stopChat();
    });

    socket.on('mensagem_recebida', (msg) => { addMessage(msg, 'partner'); });

    socket.on('webrtc_offer', async (offer) => {
      if (!peerConnection) {
        await getLocalMedia();
        initializePeerConnection();
      }
      await peerConnection.setRemoteDescription(new RTCSessionDescription(offer));
      const answer = await peerConnection.createAnswer();
      await peerConnection.setLocalDescription(answer);
      socket.emit('webrtc_answer', answer);
    });

    socket.on('webrtc_answer', async (answer) => {
      await peerConnection.setRemoteDescription(new RTCSessionDescription(answer));
    });

    socket.on('webrtc_ice_candidate', (candidate) => {
      if (peerConnection) {
        peerConnection.addIceCandidate(new RTCIceCandidate(candidate));
      }
    });

  