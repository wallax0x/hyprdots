/* Blink Example

   Este exemplo de código está no Domínio Público (veja a licença UNLICENSE).

   A não ser que seja exigido pela lei aplicável ou acordado por escrito, o
   software é distribuído "COMO ESTÁ", SEM GARANTIAS OU CONDIÇÕES DE QUALQUER
   TIPO, expressas ou implícitas.
*/
#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "esp_log.h"
#include "sdkconfig.h"

static const char *TAG = "blink";

/* Use o pino GPIO 2 para o LED. A maioria das placas ESP32 DevKit tem um LED azul neste pino */
#define BLINK_GPIO 2

void app_main(void)
{
    /* Configura o pino GPIO */
    gpio_reset_pin(BLINK_GPIO);
    /* Define o pino GPIO como uma saída (Output) */
    gpio_set_direction(BLINK_GPIO, GPIO_MODE_OUTPUT);

    while(1) {
        /* Define o nível do pino para 1 (liga o LED) */
        gpio_set_level(BLINK_GPIO, 1);
        /* Espera por 1000 milissegundos (1 segundo) */
        vTaskDelay(1000 / portTICK_PERIOD_MS);

        /* Define o nível do pino para 0 (desliga o LED) */
        gpio_set_level(BLINK_GPIO, 0);
        /* Espera por 1000 milissegundos (1 segundo) */
        vTaskDelay(1000 / portTICK_PERIOD_MS);
    }
}
