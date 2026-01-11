#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"

#define LED_PIN 2  // LED interno do ESP32, geralmente GPIO2

void app_main(void)
{
    // Configura o pino como saída
    gpio_pad_select_gpio(LED_PIN);
    gpio_set_direction(LED_PIN, GPIO_MODE_OUTPUT);

    while (1)
    {
        gpio_set_level(LED_PIN, 1);  // LED acende
        vTaskDelay(500 / portTICK_PERIOD_MS);  // espera 500ms
        gpio_set_level(LED_PIN, 0);  // LED apaga
        vTaskDelay(500 / portTICK_PERIOD_MS);  // espera 500ms
    }
}
