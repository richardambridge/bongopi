import threading


class piDisplayLine:
        scrollspeed = 8
        lineno = 0
        line = ""
        lineb = ""
        linescrolled = ""
        scrollcount = -1
        linerest = ""
        lineOriginal = ""
        lineTempPeriod = 0
        updatedLine = ""

        def __init__(self, number):
            print "Create displayline:", number
            self.lineno = number
            self.lineQ = []
            self.special = ['', '', '', '', '', '']
            self.lock = threading.Lock()

        def setSpecial(self, number, chari):
            self.special[number] = chari

        def rmSpecial(self, number):
            self.special[number] = ''

        def specialSize(self):
            size = 0
            for chari in self.special:
                if(chari):
                    size += 1
            return size

        def getLock(self):
            self.lock.acquire()

        def unLock(self):
            self.lock.release()

        def process(self):
            try:
                self.getLock()
                # If tempperiod then the line we are showing is temporary
                if(self.lineTempPeriod > 0):
                        self.lineTempPeriod -= 1
                        if(self.lineTempPeriod == 0):
                                # temp period expired
                                if(self.lineQ):
                                        nextline = self.lineQ.pop(0)
                                        orig = self.lineOriginal
                                        self.setlinePeriodDo(nextline[0],
                                                             nextline[1])
                                        self.lineOriginal = orig
                                else:
                                        self.setlinePeriodDo(self.lineOriginal,
                                                             0)

                if(self.scrollcount >= 0):
                        self.scrollcount += 1

                if(self.scrollcount > self.scrollspeed):
                        # Time to scroll
                        if len(self.linerest) > 0:
                                self.scrollcount = 0
                                self.line = self.line[1:] + self.linerest[:1]
                                self.linerest = self.linerest[1:]
                        else:
                                self.line = self.linescrolled
                                self.scrollcount = -1

                sSize = self.specialSize()
                if len(self.line) > 16 - sSize:
                        # needs to scroll
                        self.linescrolled = self.line[:16 - sSize]
                        self.linerest = self.line[16 - sSize:]
                        self.line = self.line[:16 - sSize]
                        self.scrollcount = 0

                myline = self.getline()
                updated = self.lineb != myline
                self.lineb = myline
            finally:
                self.unLock()

            return updated

        def getline(self):
            myline = ""
            for chari in self.special:
                if(chari):
                    myline += chari
            myline += self.line
            retv = myline.ljust(16)
            return myline.ljust(16)

        def clearq(self):
            self.lineQ = []
            self.lineTempPeriod = 0
            self.setline(self.lineOriginal)

        def setline(self, line):
            self.setlinePeriod(line, 0)

        def setlinePeriod(self, line, tempPeriod):
            try:
                self.getLock()
                self.setlinePeriodDo(line, tempPeriod)
            finally:
                self.unLock()

        def setlinePeriodDo(self, line, tempPeriod):

            print("%d:setlineperiod:%s,%d:%s current:%d" % (self.lineno, line,
                  tempPeriod, self.lineQ, self.lineTempPeriod))
            if(tempPeriod == 0):
                # Do now, clear queue
                self.lineTempPeriod = 0
            if(self.lineTempPeriod == 0):
                print "Set line:", line
                self.lineOriginal = self.line
                self.lineTempPeriod = tempPeriod
                self.line = line
                self.linescrolled = ""
                self.linerest = ""
                self.scrollcount = -1
            else:
                print "Q line:" + line + ",", tempPeriod
                self.lineQ.append((line, tempPeriod))
