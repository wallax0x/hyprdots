 const socket = io();

// Espera o HTML estar 100% carregado
document.addEventListener("DOMContentLoaded", () => {

  // --- Elementos do Lobby ---
  const lobbyContainer = document.getElementById('lobby-container');
  const lobbyStatus = document.getElementById('lobby-status');
  const findTextChatBtn = document.getElementById('findTextChat');
  const findVideoChatBtn = document.getElementById('findVideoChat');
  const loader = document.getElementById('loader'); // (NOVO)

  // --- Elementos da Chamada ---
  const callContainer = document.getElementById('call-container');
  const videoContainer = document.getElementById('video-container');

  // --- Elementos do Chat ---
  const statusDiv = document.getElementById('status');
  const messages = document.getElementById('messages');
  const form = document.getElementById('form');
  const input = document.getElementById('input');
  const sendButton = document.getElementById('sendButton'); // (CORRIGIDO)
  const skipButton = document.getElementById('skipButton');

  // --- Elementos de Vídeo ---
  const localVideo = document.getElementById('localVideo');
  const remoteVideo = document.getElementById('remoteVideo');

  // --- (NOVOS) Controles de Mídia ---
  const muteAudioBtn = document.getElementById('muteAudioBtn');
  const stopVideoBtn = document.getElementById('stopVideoBtn');

  // --- Variáveis Globais ---
  let peerConnection;
  let localStream;
  const configuration = {
    iceServers: [ { urls: 'stun:stun.l.google.com:19302' }, { urls: 'stun:stun1.l.google.com:19302' } ]
  };
  let currentChatType = null; // Guarda 'text' ou 'video'

  // --- Lógica dos Botões do Lobby ---
  
  findTextChatBtn.addEventListener('click', () => {
    currentChatType = 'text';
    socket.emit('find_partner', { type: currentChatType });
    lobbyStatus.textContent = 'Procurando um parceiro para chat de texto...';
    loader.classList.remove('hidden'); // (NOVO) Mostra o loader
    disableLobbyButtons();
  });

  findVideoChatBtn.addEventListener('click', async () => {
    try {
      await getLocalMedia(); // Pede permissão ANTES de procurar
      currentChatType = 'video';
      lobbyStatus.textContent = 'Procurando um parceiro para vídeo chat...';
      loader.classList.remove('hidden'); // (NOVO) Mostra o loader
      disableLobbyButtons();
      socket.emit('find_partner', { type: currentChatType });
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

  // --- LÓGICA DO BOTÃO "PRÓXIMO" ---
  skipButton.addEventListener('click', () => {
    console.log("Botão 'Próximo' clicado! Procurando novo parceiro.");

    socket.emit('leave_room');
    stopChat(); // Limpa a chamada atual
    
    // Volta para o lobby e procura um novo parceiro
    lobbyStatus.textContent = 'Procurando um novo parceiro...';
    loader.classList.remove('hidden'); // (NOVO) Mostra o loader
    disableLobbyButtons();
    socket.emit('find_partner', { type: currentChatType });
  });

  // --- Funções do Chat de Texto ---
  function addMessage(text, type = 'partner') {
    const item = document.createElement('li');
    item.className = type;
    item.textContent = text;
    messages.appendChild(item);
    messages.scrollTop = messages.scrollHeight;
  }
  
  // (CORRIGIDO) Lógica do "Enviar" e "Enter"
  sendButton.addEventListener('click', () => {
    if (!input.value) return; 
    socket.emit('nova_mensagem', input.value);
    addMessage(input.value, 'me'); 
    input.value = ''; 
  });

  input.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault(); 
      sendButton.click(); 
    }
  });
  // --- Fim do Chat de Texto ---


  // --- (NOVOS) Handlers dos Controles de Mídia ---

  muteAudioBtn.addEventListener('click', () => {
    if (!localStream) return;
    const audioTrack = localStream.getTracks().find(track => track.kind === 'audio');
    if (audioTrack) {
      // Inverte o estado (muta ou desmuta)
      audioTrack.enabled = !audioTrack.enabled;
      
      // Atualiza o texto do botão
      muteAudioBtn.textContent = audioTrack.enabled ? 'Mutar' : 'Desmutar';
      
      // Avisa o parceiro
      socket.emit('media_status_change', { type: 'audio', enabled: audioTrack.enabled });
    }
  });

  stopVideoBtn.addEventListener('click', () => {
    if (!localStream) return;
    const videoTrack = localStream.getTracks().find(track => track.kind === 'video');
    if (videoTrack) {
      // Inverte o estado (para ou inicia)
      videoTrack.enabled = !videoTrack.enabled;
      
      // Atualiza o texto do botão
      stopVideoBtn.textContent = videoTrack.enabled ? 'Parar Vídeo' : 'Iniciar Vídeo';
      
      // Avisa o parceiro
      socket.emit('media_status_change', { type: 'video', enabled: videoTrack.enabled });
    }
  });
  // --- Fim dos Controles de Mídia ---


  // --- Funções Principais de WebRTC ---

  async function getLocalMedia() {
    if (localStream) return; // Evita pedir permissão de novo
    localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    localVideo.srcObject = localStream;
  }

  function initializePeerConnection() {
    peerConnection = new RTCPeerConnection(configuration);

    // Adiciona as tracks (áudio/vídeo) à conexão
    localStream.getTracks().forEach(track => {
      peerConnection.addTrack(track, localStream);
    });

    // Ouve quando o parceiro envia as tracks dele
    peerConnection.ontrack = (event) => {
      remoteVideo.srcObject = event.streams[0];
    };

    // Ouve os "endereços de rede" (ICE) e os envia ao parceiro
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

  /**
   * Função "Mestra" de Limpeza.
   * Chamada ao desconectar, pular, ou dar erro.
   */
  function stopChat() {
    if (peerConnection) {
      peerConnection.close();
      peerConnection = null;
    }
    // Para a câmera e o microfone (libera o hardware)
    if(localStream) {
      localStream.getTracks().forEach(track => track.stop());
      localStream = null;
    }
    // Limpa os players de vídeo
    localVideo.srcObject = null;
    remoteVideo.srcObject = null;
    
    // Volta para o lobby
    callContainer.style.display = 'none';
    lobbyContainer.style.display = 'block';
    loader.classList.add('hidden'); // (NOVO) Esconde o loader
    enableLobbyButtons();
    
    // (NOVO) Reseta o texto dos botões de mídia
    muteAudioBtn.textContent = 'Mutar';
    stopVideoBtn.textContent = 'Parar Vídeo';
  }

  // --- Lógica de Sinalização (Socket.IO Listeners) ---
  
  socket.on('status', (msg) => {
    lobbyStatus.textContent = msg;
  });

  socket.on('chat_start', async (data) => {
    loader.classList.add('hidden'); // (NOVO) Esconde o loader
    lobbyContainer.style.display = 'none';
    callContainer.style.display = 'flex';
    form.classList.remove('disabled');
    messages.innerHTML = ''; // Limpa o chat anterior
    
    if (data.type === 'video') {
      videoContainer.style.display = 'block'; // Mostra os vídeos
      statusDiv.textContent = 'Conectado com vídeo!';
      
      // Garante que a mídia local está rodando (caso o 'stopChat' a tenha parado)
      await getLocalMedia(); 
      initializePeerConnection(); 
      
      if (data.isCaller) {
        await createOffer();
      }
    } else { // 'text'
      videoContainer.style.display = 'none'; // Esconde os vídeos
      statusDiv.textContent = 'Conectado (somente texto)!';
    }
  });

  socket.on('partner_disconnected', (msg) => {
    addMessage(`--- ${msg} ---`, 'partner');
    stopChat();
  });

  socket.on('mensagem_recebida', (msg) => { addMessage(msg, 'partner'); });

  // (NOVO) Ouve as mudanças de mídia do parceiro
  socket.on('partner_media_status_changed', (data) => {
    if (data.type === 'audio') {
      addMessage(data.enabled ? '--- Parceiro reativou o áudio ---' : '--- Parceiro mutou o áudio ---', 'partner');
    } else if (data.type === 'video') {
      addMessage(data.enabled ? '--- Parceiro reativou o vídeo ---' : '--- Parceiro desativou o vídeo ---', 'partner');
    }
  });

  // --- Handlers de Sinalização WebRTC ---
  
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
  // --- Fim dos Handlers ---

}); // <-- Fim do DOMContentLoaded