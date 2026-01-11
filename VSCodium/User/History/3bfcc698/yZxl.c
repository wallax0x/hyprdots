#include "RF24.h"
#include <ezButton.h> // A biblioteca ainda é útil para tratar o "debounce"
#include "esp_wifi.h" 

SPIClass *hp = nullptr;
RF24 radio(16, 15, 16000000);
byte i = 45;
unsigned int flag = 0;

// MUDANÇA 1: Alterado do pino 33 para o pino 0 (o botão BOOT)
ezButton bootButton(0); 

void setup(void) {
  esp_wifi_stop();
  esp_wifi_deinit();
  Serial.begin(115200);
  bootButton.setDebounceTime(50); // Configura o debounce para o botão BOOT
  initHP();
}

void initHP() {
  hp = new SPIClass(HSPI);
  hp->begin();
  if (radio.begin(hp)) {
    delay(200);
    Serial.println("Rádio Iniciado! Pressione o botão BOOT na placa para alternar o modo.");
    radio.setAutoAck(false);
    radio.stopListening();
    radio.setRetries(0, 0);
    radio.setPayloadSize(5);
    radio.setAddressWidth(3);
    radio.setPALevel(RF24_PA_MAX, true);
    radio.setDataRate(RF24_2MBPS);
    radio.setCRCLength(RF24_CRC_DISABLED);
    radio.printPrettyDetails();
    radio.startConstCarrier(RF24_PA_MAX, i); 
  } else {
    Serial.println("HP couldn’t start !!!");
  }
}

// Modo 2: Faz o canal oscilar
void two() {
  if (flag == 0) { i += 2; } else { i -= 2; }
  if ((i > 79) && (flag == 0)) { flag = 1; } 
  else if ((i < 2) && (flag == 1)) { flag = 0; }
  radio.setChannel(i);
}

// Modo 1: Faz uma varredura rápida de canais
void one() {
  for (int i = 0; i < 79; i++) {
    radio.setChannel(i);
  }
}

void loop(void) {
  bootButton.loop(); // Atualiza o estado do botão BOOT

  // MUDANÇA 2: A lógica foi ajustada.
  // Quando o botão BOOT é pressionado, o pino 0 fica em estado LOW (Baixo).
  // A função isPressed() da biblioteca detecta exatamente isso.
  
  if (bootButton.isPressed()) {
    // Se o botão estiver pressionado, executa o MODO 2
    two();
  } else {
    // Se o botão estiver solto, executa o MODO 1
    one();
  }
}