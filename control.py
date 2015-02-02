#!/usr/bin/python
import sys
import netifaces
from mpd import MPDClient
import thread
import inspect
import time
from piDisplay import piDisplay
from piDisplayLine import piDisplayLine
from subprocess import call
import traceback

import Adafruit_CharLCD as LCD

SPECIAL_PLAYERSTATE = 5
SPECIAL_PL_MODE = 1
SPECIAL_MPD_STATE = 2
SPECIAL_MENU = 3
SPECIAL_WIFI = 4
SPECIAL_INTERNET = 0

CHAR_STOP = "\x01"
CHAR_SMILY = "\x02"
CHAR_PAUSE = "\x04"
CHAR_PL = "\x05"
CHAR_WAIT = "\x06"
CHAR_PLAY = "\x07"
CHAR_WIFI = "\x03"
CHAR_INTERNET = "W"


class control:

        theend = 0
        currentPlayList = 0

        def shutdown(self):
            self.theend = 1
            self.line1.setline("Goodbye")
            self.line2.setline("")
            self.displayThread.setcolour(1, 0, 0)
            time.sleep(2)
            self.displayThread.off()

        def doSomething(self):
            self.line1.setlinePeriod("A long line to scroll", 30)

        def pishutdown(self):
            # #confirm?
            self.shutdown()
            call(["poweroff"])

        def doBig(self):
            self.line1.setlinePeriod("BIG SELECT", 100)

        def turnBacklightOff(self):
            self.displayThread.turnOff()

        def turnBacklightOn(self):
            self.displayThread.turnOn()

        def mpdCheck(self):
            self.mpdClient = self.mpdCheckVar(self.mpdClient)

        def mpdCheckVar(self, mpdClient):
            while(True):
                try:
                    if(mpdClient):
                        mpdClient.ping()
                        return mpdClient
                    else:
                        mpdClient = MPDClient()
                        self.line2.setSpecial(SPECIAL_MPD_STATE, CHAR_WAIT)
                        mpdClient.connect("localhost", 6600)
                        self.line2.rmSpecial(SPECIAL_MPD_STATE)
                except:
                    self.line2.setSpecial(SPECIAL_MPD_STATE, CHAR_WAIT)
                    tb = traceback.format_exc()
                    print "MPD client failed ping,", tb
                    time.sleep(1)
                    try:
                        if(mpdClient):
                            mpdClient.kill()
                    except:
                        pass
                        mpdClient = None

        def music(self):
            self.menuitem = 0
            self.mpdCheck()
            self.line2.setline("")
            self.line2.setSpecial(SPECIAL_MENU, CHAR_SMILY)
            self.showSong()
            self.playListLoaded = self.mpdClient.playlistinfo()

        def musicRight(self):
            self.mpdCheck()
            self.line2.setSpecial(SPECIAL_MPD_STATE, CHAR_WAIT)
            self.mpdClient.next()
            self.line2.rmSpecial(SPECIAL_MPD_STATE)

        def musicLeft(self):
            self.mpdCheck()
            self.line2.setSpecial(SPECIAL_MPD_STATE, CHAR_WAIT)
            self.mpdClient.previous()
            self.line2.rmSpecial(SPECIAL_MPD_STATE)

        def musicUp(self):
            self.musicMove(-1)

        def musicDown(self):
            self.musicMove(1)

        def musicMove(self, direction):
            self.mpdCheck()

            if(self.playlistwait > 0):
                # play list displayed currently
                self.playlistpos += direction

            if(self.playlistpos >= len(self.playListLoaded)):
                self.playlistpos = 0
            if(self.playlistpos == -1):
                self.playlistpos = len(self.playListLoaded) - 1
            if not self.playListLoaded:
                self.line2.setline("Empty playlist")
            else:
                plItem = self.playListLoaded[self.playlistpos]
                self.line2.clearq()
                self.line2.setlinePeriod(plItem['title'] + "," +
                                         plItem['artist'], 80)
                self.playlistwait = 60

        def musicSelect(self):
            self.mpdCheck()
            self.line2.setSpecial(SPECIAL_MPD_STATE, CHAR_WAIT)
            if self.playlistwait > 0:
                plItem = self.playListLoaded[self.playlistpos]
                print "item:", plItem
                self.mpdClient.playid(plItem['id'])
            else:
                status = self.mpdClient.status()
                if status['state'] == "play":
                    self.mpdClient.pause()
                else:
                    self.mpdClient.play()
            self.line2.rmSpecial(SPECIAL_MPD_STATE)

        def musicplaylistRight(self):
            self.playlistloadpos += 1
            self.musicplaylist()

        def musicplaylistLeft(self):
            self.playlistloadpos -= 1
            self.musicplaylist()

        def musicplaylistDown(self):
            self.mpdCheck()
            pli = self.mpdClient.lsinfo(self.playlistloadsub)
            plItem = pli[self.playlistloadpos]
            self.line2.clearq()
            if 'playlist' in plItem:
                self.musicplaylistSelect()
            elif 'directory' in plItem:
                self.playlistloadsub = plItem['directory']
                self.musicplaylist()

        def musicplaylistSelect(self):
            self.mpdCheck()
            self.line2.clearq()
            self.line2.setline("Loading playlist")
            pli = self.mpdClient.lsinfo(self.playlistloadsub)
            plItem = pli[self.playlistloadpos]
            self.line2.setSpecial(SPECIAL_MPD_STATE, CHAR_WAIT)
            if 'playlist' in plItem:
                self.mpdClient.clear()
                self.mpdClient.load(plItem['playlist'])
                self.mpdClient.play()
                self.music()
                self.playlistLoaded(plItem['playlist'])
            elif 'directory' in plItem:
                self.mpdClient.clear()
                self.mpdClient.add(plItem['directory'])
                self.mpdClient.play()
                self.music()
                self.line2.rmSpecial(SPECIAL_MPD_STATE)
                self.line2.setline("")

        def musicplaylist(self):
            # Enter the Playlist submenu
            self.line2.setSpecial(SPECIAL_MENU, CHAR_PL)
            self.mpdCheck()
            pl = self.mpdClient.listplaylists()
            print "playlists", pl
            pli = self.mpdClient.lsinfo(self.playlistloadsub)
            print "lsinfo", pli

            if(self.playlistloadpos > len(pli) - 1):
                self.playlistloadpos = 0
            if(self.playlistloadpos == -1):
                self.playlistloadpos = len(pli) - 1
            if not pli:
                self.line2.setline("No music found")
            else:
                plItem = pli[self.playlistloadpos]
                self.line2.clearq()
                if 'playlist' in plItem:
                    self.line2.setline(plItem['playlist'])
                elif 'directory' in plItem:
                    self.line2.setline(plItem['directory'])

        def showSong(self):
            self.mpdCheck()
            song = self.mpdClient.currentsong()
            print "song:", song
            if('title' in song and type(song['title']) is str):
                self.line1.clearq()
                self.line1.setline(song['title'])
#                self.line1.setlinePeriod("T:" + song['title'], 20);
#                self.line1.setlinePeriod("A:" + song['artist'], 20);
#                self.line1.setlinePeriod("Al:" + song['album'], 20);

        def playlistLoaded(self, listloaded):
            print "ListLoaded:", listloaded
            if listloaded != self.playlistloaded:
                self.playlistloaded = listloaded
                f = open('/data/bongopi/playlistloaded', 'w')
                f.write(listloaded)
                f.close()

        def mpdWatcherThread(self):
            mpd = None
            states = ["player"]
            while True:
                try:
                    mpd = self.mpdCheckVar(mpd)
                    for state in states:
                        if state == "player":
                            mpdClientStatus = mpd.status()
                            if 'state' in mpdClientStatus:
                                playerState = mpdClientStatus['state']
                                print "Playerstatus=" + playerState
                                if playerState == "play":
                                    self.line1.setSpecial(SPECIAL_PLAYERSTATE,
                                                          CHAR_PLAY)
                                    self.showSong()
                                elif playerState == "stop":
                                    self.line1.setSpecial(SPECIAL_PLAYERSTATE,
                                                          CHAR_STOP)
                                elif playerState == "pause":
                                    self.line1.setSpecial(SPECIAL_PLAYERSTATE,
                                                          CHAR_PAUSE)
                                else:
                                    self.line1.setline(playerState)
                            elif state == "playlist":
                                playlistState = mpdClientStatus['playlist']
                                print "PL state:", playlistState
                            else:
                                print "State from MPD:", state

                            states = mpd.idle()
                except:
                    tb = traceback.format_exc()
                    print "EXCEPTION::::Error in mpd watcher thread", tb
                    if(mpd):
                        try:
                            mpd.close()
                        except:
                            pass
                        mpd = None

        def buttonPressed(self, button, downTime):
            if downTime > self.longpress:
                button += 5

            if len(self.menus[self.menuitem]) < button:
                print "Button not defined"
            elif isinstance(self.menus[self.menuitem][button + 1], int):
                nmenuitem = self.menus[self.menuitem][button + 1]
                self.menuitem = nmenuitem
                if inspect.ismethod(self.menus[self.menuitem][0]):
                    self.menus[self.menuitem][0]()
                else:
                    self.line1.setline(self.menus[self.menuitem][0])
            elif inspect.ismethod(self.menus[self.menuitem][button + 1]):
                self.menus[self.menuitem][button + 1]()

        # Make list of button value, text, and backlight color.
        buttons = (LCD.SELECT, LCD.LEFT, LCD.UP, LCD.DOWN, LCD.RIGHT)

        def randomChange(self):
            if self.randommode == 0:
                self.randommode = 1
                self.line2.setlinePeriod("Enabled random", 10)
            else:
                self.randommode = 0
                self.line2.setlinePeriod("Disabled Random", 10)
            self.mpdClient.random(self.randommode)

        def readButtons(self, lcd):
            states = []
            for button in self.buttons:
                if(lcd.is_pressed(button)):
                    states.append(button)
            return states

        def process(self):
            colourChange = 0
            lcd = self.displayThread.lcd
            bigTimeout = 0
            ifaceCheck = 0
            exceptcount = 0
            self.music()
            while True:
                try:
                    if(self.theend):
                        return
                    buttonStates = self.readButtons(lcd)

                    # #Self restart with select+right pushed
                    if len(buttonStates) == 2 \
                            and LCD.SELECT in buttonStates \
                            and LCD.RIGHT in buttonStates:
                        print "Select + Right"
                        buttonStates = self.readButtons(lcd)
                        while len(buttonStates) == 2 \
                                and LCD.SELECT in buttonStates \
                                and LCD.RIGHT in buttonStates:
                            time.sleep(.1)
                            buttonStates = self.readButtons(lcd)
                        call(["service", "bongopi", "restart"])

                    if len(buttonStates) == 2 \
                            and LCD.UP in buttonStates \
                            and LCD.DOWN in buttonStates:
                        print "Up and Down"
                        buttonStates = self.readButtons(lcd)
                        while len(buttonStates) == 2 \
                                and LCD.UP in buttonStates \
                                and LCD.DOWN in buttonStates:
                            time.sleep(.1)
                            buttonStates = self.readButtons(lcd)
                        self.displayThread.force()

                    if len(buttonStates) == 3 \
                            and LCD.SELECT in buttonStates \
                            and LCD.UP in buttonStates \
                            and LCD.DOWN in buttonStates:
                        print "Select + Up + Down"
                        buttonStates = self.readButtons(lcd)
                        while len(buttonStates) == 3 \
                                and LCD.SELECT in buttonStates \
                                and LCD.UP in buttonStates \
                                and LCD.DOWN in buttonStates:
                            time.sleep(.1)
                            buttonStates = self.readButtons(lcd)
                        self.pishutdown()

                    for button in self.buttons:
                        if len(buttonStates) == 1 and button in buttonStates:
                            buttonDownTime = 0
                            buttonStates = self.readButtons(lcd)
                            while len(buttonStates) == 1 \
                                    and button in buttonStates:
                                buttonDownTime += 1
                                time.sleep(.1)
                                buttonStates = self.readButtons(lcd)
                                if(buttonDownTime > self.longpress
                                        and colourChange == 0):
                                    self.displayThread.setcolour(0, 0, 1)
                                    colourChange = 1
                                if(buttonDownTime > self.longerpress
                                        and colourChange == 1):
                                    self.displayThread.setcolour(0, 1, 1)
                                    colourChange = 2
                            if(colourChange):
                                self.displayThread.setcolour(0, 1, 0)
                                colourChange = 0
                            if self.displayThread.displayIsOff():
                                # wake up
                                self.displayThread.turnOn()
                            else:
                                self.buttonPressed(button, buttonDownTime)
                                bigTimeout = 500

                    if(self.playlistwait > 0):
                        self.playlistwait -= 1
                        if(self.playlistwait == 0):
                            print "playlistwait end"
                            self.line2.clearq()

                    if(bigTimeout > 0):
                        bigTimeout -= 1
                        if(bigTimeout == 0):
                            self.music()

                    ifaceCheck -= 1
                    if(ifaceCheck <= 0):
                        ifaceCheck = 1000
                        # Check the status of wlan0
                        wlan0 = netifaces.ifaddresses('wlan0')
                        if(wlan0 and netifaces.AF_INET in wlan0
                                and wlan0[netifaces.AF_INET]
                                and 'addr' in wlan0[netifaces.AF_INET][0]):
                            self.line2.setSpecial(SPECIAL_WIFI, CHAR_WIFI)
                        else:
                            self.line2.rmSpecial(SPECIAL_WIFI)

                            eth0 = netifaces.ifaddresses('eth0')
                            if(eth0 and netifaces.AF_INET in eth0
                                    and eth0[netifaces.AF_INET]
                                    and 'addr' in eth0[netifaces.AF_INET][0]):
                                self.line2.setSpecial(SPECIAL_INTERNET,
                                                      CHAR_INTERNET)
                            else:
                                self.line2.rmSpecial(SPECIAL_INTERNET)
                            ifaceCheck = 100

                        time.sleep(.1)

                    exceptcount = 0

                except:
                    tb = traceback.format_exc()
                    print "BONGOPI EXCEPTION::Error in main thread", tb
                    exceptcount += 1
                    if(exceptcount > 10):
                        print "TOO MANY EXCEPTION..exit"
                        lcd = LCD.Adafruit_CharLCDPlate()
                        lcd.set_color(1, 0, 0)
                        lcd.message("Too many exceptions\nExit")
                        time.sleep(10)
                        lcd.clear()
                        lcd.set_color(0, 0, 0)
                        sys.exit(1)

    # #INIT
        def __init__(self):
            self.line1 = piDisplayLine(1)
            self.line2 = piDisplayLine(2)

            self.line1.setline("Bongo PI")
            self.line2.setline("Starting up")
            self.displayThread = piDisplay(self.line1, self.line2)
            self.displayThread.start()

            self.menuitem = 0
            self.playlistpos = 0
            self.playlistwait = 0
            self.playlistloadpos = 0
            self.playlistloadsub = ""

            self.playlistloaded = ""
            self.randommode = 0

            self.musicstatus = "normal"
            self.mpdClient = None

            self.longpress = 15
            self.longerpress = 30
            # Menu name, SELECT, RIGHT, DOWN,UP,LEFT
            self.menus = (
                (self.music,
                 self.musicSelect,
                 self.musicRight,
                 self.musicDown,
                 self.musicUp,
                 self.musicLeft,
                 1),  # LongSelect
                (self.musicplaylist,  # Playlist Submenu
                 self.musicplaylistSelect,
                 self.musicplaylistRight,
                 self.musicplaylistDown,
                 0,
                 self.musicplaylistLeft,
                 2),  # 1
                ('Control',
                 '',
                 '',
                 3,
                 0,
                 '',
                 ''),  # 2
                ('Random',
                 '',
                 self.randomChange,
                 4,
                 2,
                 self.randomChange,
                 ''),  # 3
                )

            self.displayThread.setTimeout(9000)
            self.mpdCheck()
            if self.mpdClient.playlist() is None \
                    or len(self.mpdClient.playlist()) == 0:
                print "No current playlist"
                try:
                    f = open("/data/bongopi/playlistloaded")
                    playlist = f.read()
                    if playlist is not None:
                        self.playlistloaded = playlist
                        self.line2.setline("Loading:" + playlist)
                        self.mpdClient.load(playlist)

                except:
                    print "Error loading playlist previous info"
            self.mpdClient.random(1)
            self.displayThread.setTimeout(100)
            self.line2.setline("")
            thread.start_new_thread(self.mpdWatcherThread, ())
