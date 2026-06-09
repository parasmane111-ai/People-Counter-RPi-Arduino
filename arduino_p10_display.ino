#include <SPI.h>
#include <DMD2.h>
#include <fonts/SystemFont5x7.h>

#define DISPLAYS_WIDE 3
#define DISPLAYS_HIGH 1

SoftDMD dmd(DISPLAYS_WIDE, DISPLAYS_HIGH);

// UART data
String incoming = "";
int totalCount = 0;

// Fake date and time
int hourVal = 1;
int minuteVal = 10;
int dayVal = 27;
int monthVal = 3;

unsigned long previousMinuteMillis = 0;
unsigned long previousDisplayMillis = 0;

const unsigned long minuteInterval = 60000;
const unsigned long displayInterval = 1000;

void setup() {
  Serial.begin(9600);

  dmd.begin();
  dmd.setBrightness(255);
  dmd.selectFont(SystemFont5x7);
  dmd.clearScreen();
}

void loop() {
  receiveSerialData();
  updateClock();
  updateDisplay();
}

// ================= RECEIVE DATA FROM RPi =================
void receiveSerialData() {
  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '\n') {
      incoming.trim();

      if (incoming.length() > 0) {
        totalCount = incoming.toInt();
      }

      incoming = "";
    } 
    else {
      incoming += c;
    }
  }
}

// ================= FAKE CLOCK =================
void updateClock() {
  unsigned long currentMillis = millis();

  if (currentMillis - previousMinuteMillis >= minuteInterval) {
    previousMinuteMillis = currentMillis;

    minuteVal++;

    if (minuteVal >= 60) {
      minuteVal = 0;
      hourVal++;
    }

    if (hourVal >= 24) {
      hourVal = 0;
      dayVal++;
    }

    if (dayVal > 31) {
      dayVal = 1;
      monthVal++;
    }

    if (monthVal > 12) {
      monthVal = 1;
    }
  }
}

// ================= DISPLAY DATA =================
void updateDisplay() {
  unsigned long currentMillis = millis();

  if (currentMillis - previousDisplayMillis >= displayInterval) {
    previousDisplayMillis = currentMillis;

    char dateStr[8];
    char timeStr[8];
    char countStr[8];

    sprintf(dateStr, "%02d/%02d", dayVal, monthVal);
    sprintf(timeStr, "%02d:%02d", hourVal, minuteVal);
    sprintf(countStr, "%d", totalCount);

    dmd.clearScreen();

    // First 16x32 display: DATE
    dmd.drawString(1, 0, "DATE");
    dmd.drawString(1, 8, dateStr);

    // Second 16x32 display: TIME
    dmd.drawString(33, 0, "TIME");
    dmd.drawString(33, 8, timeStr);

    // Third 16x32 display: TOTAL COUNT
    dmd.drawString(65, 0, "COUNT");
    dmd.drawString(65, 8, countStr);
  }
}
