import threading
import time
import Adafruit_CharLCD as LCD


class piDisplay (threading.Thread):

        displayOn = 0
        displayTimeout = 100
        idleCount = 0

        def __init__(self, line1, line2):
            threading.Thread.__init__(self)
            self.daemon = True
            self.lcd = LCD.Adafruit_CharLCDPlate()
            self.turnOn()
            self.line1 = line1
            self.line2 = line2
            self.forceUpdate = False

            # http://www.quinapalus.com/hd44780udg.html   5x8
            # Only 0-7 are allowed

            # Stop
            self.lcd.create_char(1, [0x0, 0x0, 0xe, 0xe, 0xe, 0xe, 0x0, 0x0])
            # Smily
            self.lcd.create_char(2, [0x0, 0xa, 0xa, 0xa, 0x0, 0x11, 0xe, 0x0])
            # Wifi
            self.lcd.create_char(3, [0x0, 0x1f, 0x0, 0xe, 0x0, 0x4, 0x0, 0x0])
            # pause
            self.lcd.create_char(4, [0x0, 0x0, 0xa, 0xa, 0xa, 0xa, 0x0, 0x0])
            # PL
            self.lcd.create_char(5, [0x18, 0x14, 0x18, 0x10,
                                     0x4, 0x4, 0x7, 0x0])
            # Wait
            self.lcd.create_char(6, [0x1f, 0x11, 0xa, 0x4, 0xa,
                                     0x11, 0x1f, 0x0])
            # Play
            self.lcd.create_char(7, [0x0, 0x8, 0xc, 0xe, 0xc, 0x8, 0x0, 0x0])

        def displayIsOff(self):
            return self.displayOn == 0

        def turnOn(self):
            self.idleCount = 0
            if self.displayOn == 0:
                print "turn Backlight on"
                self.displayOn = 1
                self.lcd.set_color(0, 1, 0)

        def setcolour(self, r, g, b):
            self.lcd.set_color(r, g, b)

        def off(self):
            self.lcd.clear()
            self.turnOff()

        def turnOff(self):
            if self.displayOn == 1:
                print "turn Backlight off"
                self.displayOn = 0
                self.lcd.set_color(0, 0, 0)

        def force(self):
            self.lcd = LCD.Adafruit_CharLCDPlate()
            self.turnOn()
            self.forceUpdate = True

        def setTimeout(self, timeout):
            self.displayTimeout = timeout
            self.idleCount = 0

        def run(self):
            print "starting display thread"
            self.lcd.clear()
            while True:
                time.sleep(.1)
                # Do we need to do anything
                update = False
                for line in (self.line1, self.line2):
                    if(line.process()):
                        update = True
                if(update or self.forceUpdate):
                    self.forceUpdate = False
                    self.idleCount = 0
                    self.turnOn()
                    self.lcd.home()
                    message = self.line1.getline() + "\n" \
                        + self.line2.getline()
                    self.lcd.message(message)

                self.idleCount += 1
                if(self.idleCount > self.displayTimeout
                        and self.displayOn == 1):
                    self.turnOff()
