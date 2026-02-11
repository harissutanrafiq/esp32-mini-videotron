/*
 * ESP32-S3 EXTREME E1.31 RECEIVER
 * Optimization Level: MAXIMUM
 * Features: Static IP, No WiFi Sleep, Bitwise Logic, Pointer Arithmetic
 */

#include <Arduino.h>
#include <WiFi.h>
#include <esp_wifi.h> // Library native untuk kontrol power WiFi
#include <ESPAsyncE131.h>
#include <ESP32-HUB75-MatrixPanel-I2S-DMA.h>

// ==========================================
// 1. KONFIGURASI NETWORK (STATIC IP = FASTER)
// ==========================================
const char *ssid = "NAMA_WIFI_ANDA";
const char *password = "PASSWORD_WIFI_ANDA";

// Setting Static IP (Sesuaikan dengan network Anda)
// Ini jauh lebih cepat daripada menunggu DHCP!
IPAddress local_IP(192, 168, 1, 105); // IP Device ini
IPAddress gateway(192, 168, 1, 1);    // Router
IPAddress subnet(255, 255, 255, 0);

#define START_UNIVERSE 1 
#define UNIVERSE_COUNT 25 
#define E131_PORT 5568

// ==========================================
// 2. KONFIGURASI MATRIX
// ==========================================
#define PANEL_RES_X 64      
#define PANEL_RES_Y 64      
#define PANEL_CHAIN 1       

// Pinout ESP32-S3 (Default DevKit)
#define R1_PIN 42
#define G1_PIN 41
#define B1_PIN 40
#define R2_PIN 38
#define G2_PIN 39
#define B2_PIN 37
#define A_PIN 45
#define B_PIN 36
#define C_PIN 48
#define D_PIN 35
#define E_PIN 21 
#define LAT_PIN 47
#define OE_PIN 14
#define CLK_PIN 2

// ==========================================
// 3. OBJEK & VARIABEL
// ==========================================
MatrixPanel_I2S_DMA *dma_display = nullptr;
ESPAsyncE131 e131(20); // Deep buffer

// ==========================================
// 4. SETUP
// ==========================================
void setup() {
    // 1. CPU MAX SPEED
    setCpuFrequencyMhz(240);
    
    // Matikan Serial di produksi untuk menghemat cycle CPU
    // Serial.begin(115200); 

    // 2. SETUP MATRIX
    HUB75_I2S_CFG mxconfig(PANEL_RES_X, PANEL_RES_Y, PANEL_CHAIN);
    mxconfig.gpio.r1 = R1_PIN; mxconfig.gpio.g1 = G1_PIN; mxconfig.gpio.b1 = B1_PIN;
    mxconfig.gpio.r2 = R2_PIN; mxconfig.gpio.g2 = G2_PIN; mxconfig.gpio.b2 = B2_PIN;
    mxconfig.gpio.a = A_PIN;   mxconfig.gpio.b = B_PIN;   mxconfig.gpio.c = C_PIN;
    mxconfig.gpio.d = D_PIN;   mxconfig.gpio.e = E_PIN;
    mxconfig.gpio.lat = LAT_PIN; mxconfig.gpio.oe = OE_PIN; mxconfig.gpio.clk = CLK_PIN;

    // Overclock I2S (Coba 20M, jika flicker turunkan ke 10M)
    mxconfig.i2sspeed = HUB75_I2S_CFG::HZ_20M; 
    mxconfig.double_buff = true; 

    dma_display = new MatrixPanel_I2S_DMA(mxconfig);
    dma_display->begin();
    dma_display->setBrightness8(128); 
    dma_display->clearScreen();

    // 3. SETUP WIFI (EXTREME MODE)
    WiFi.mode(WIFI_STA);
    
    // DISABLE SLEEP (Native API Call)
    // Ini memaksa modem WiFi ON terus menerus. Boros baterai, tapi Latency terendah.
    esp_wifi_set_ps(WIFI_PS_NONE); 
    
    // Gunakan Static IP
    if (!WiFi.config(local_IP, gateway, subnet)) {
        // Fallback jika gagal config
    }
    
    WiFi.begin(ssid, password);

    // Booting Indicator (Red Dot)
    while (WiFi.status() != WL_CONNECTED) {
        dma_display->drawPixelRGB888(0, 0, 255, 0, 0); 
        delay(50);
        dma_display->drawPixelRGB888(0, 0, 0, 0, 0);
        delay(50);
    }
    
    // Green Dot (Connected)
    dma_display->drawPixelRGB888(0, 0, 0, 255, 0);

    // 4. E1.31 INIT
    if (e131.begin(E131_UNICAST)) {
        // Ready
    }
}

// ==========================================
// 5. LOOP (ZERO OVERHEAD)
// ==========================================
void loop() {
    // Polling packet tanpa delay
    if (!e131.isEmpty()) {
        e131_packet_t packet;
        e131.pull(&packet); 

        // Optimasi: Swap bytes manual hanya sekali
        uint16_t universe = (packet.universe << 8) | (packet.universe >> 8); // Fast htons replacement
        
        // Pengecekan range universe yang sangat cepat
        if (universe >= START_UNIVERSE && universe < (START_UNIVERSE + UNIVERSE_COUNT)) {
            
            // Pointer arithmetic setup
            // Data pixel dimulai dari property_values[1] (index 0 adalah start code)
            uint8_t *data_ptr = packet.property_values + 1;
            
            // Hitung jumlah pixel dalam paket ini (panjang data / 3)
            // htons manual: ((high << 8) | (low >> 8))
            uint16_t p_count = packet.property_value_count;
            uint16_t count = (((p_count << 8) | (p_count >> 8)) - 1) / 3;

            // Pre-calculate Pixel Offset Global
            // (Universe sekarang - Universe Awal) * 170 pixel
            uint32_t base_pixel_idx = (universe - START_UNIVERSE) * 170;

            // LOOP UNROLLING-FRIENDLY
            for (uint16_t i = 0; i < count; i++) {
                // Kalkulasi Koordinat dengan Bitwise Operation (Super Cepat)
                // Hanya bekerja untuk Width 64!
                // px = base + i
                uint32_t px = base_pixel_idx + i;
                
                // x = px % 64  ->  px & 63
                // y = px / 64  ->  px >> 6
                int16_t x = px & 0x3F; 
                int16_t y = px >> 6;

                // Direct draw
                // Mengambil RGB langsung dari pointer memory (increment otomatis)
                // data_ptr[0] = R, data_ptr[1] = G, data_ptr[2] = B
                dma_display->drawPixelRGB888(x, y, *data_ptr, *(data_ptr + 1), *(data_ptr + 2));
                
                // Geser pointer 3 langkah (R,G,B) ke pixel berikutnya
                data_ptr += 3;
            }
        }
    }
}