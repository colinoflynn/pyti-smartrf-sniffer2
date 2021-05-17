import serial
import struct
import time


class TICommand(object):

    CMD_PING = 0x40
    CMD_START = 0x41
    CMD_STOP = 0x42
    CMD_PAUSE = 0x43
    CMD_RESUME = 0x44
    CMD_CFG_FREQUENCY = 0x45
    CMD_CFG_PHY = 0x47
    CMD_CFG_WBMS_CHANNEL_TABLE = 0x50
    CMD_CFG_BLE_INITIATOR_ADDRESS = 0x70

    STATUS_CODES = ["OK", "Timeout", "FCS failed", "Invalid Command", "Invalid State"]

    def __init__(self, comport, baudrate=3000000):
        """Connect to a dev-kit programmed with sniffing firmware, note default baudrate is 3Mbps not 921Kbps as docs suggest"""
        self.ser = serial.Serial(comport, baudrate)
        self.ping()
        self.sniff_stop()

    def cmd_set_phy(self, phyindex):
        """Set phy ID to given index"""

        self.cmd(self.CMD_CFG_PHY, [phyindex])
    
    def cmd_set_frequencymhz(self, freq):

        freqint = int(freq)
        freqfrac = freq - freqint
        freqfrac = int(freqfrac * 65536)

        pl = list(struct.pack("<H", freqint))
        pl.extend(list(struct.pack("<H", freqfrac)))

        self.cmd(self.CMD_CFG_FREQUENCY, pl)

    def sniff_stop(self):
        self.cmd(self.CMD_STOP)

    def sniff_start(self):
        self.cmd(self.CMD_START)

    def cmd(self, packet_info, payload=[]):
        """Send command, check response is OK"""

        self.tx(packet_info, payload)

        t = 0
        while t < 10000:
            resp = self.rx()

            if resp:
                pinfo = resp[0]
                payload = resp[1]

                if pinfo == 0x80:
                    break
            else:
                t += 1
                time.sleep(0.001)                

        if pinfo == None:
            raise IOError("Timeout on response")
            
        if len(payload) != 1:
            raise IOError("Unexpected payload - %s"%str(payload))
            
        stat = int(payload[0])
            
        if stat != 0x00:
                raise IOError("Unexpected status: %x (%s)"%(stat, self.STATUS_CODES[stat]))

    def tx(self, packet_info, payload=[]):
        """Transmit a message to the device"""

        plen = len(payload)

        cmd = [0x40, 0x53]
        cmd.append(packet_info)
        cmd.extend(list(struct.pack("<H", plen)))

        cmd.extend(payload)

        #FCS not incluided in data streaming or error packet (0x3 in top 2 bits)
        if packet_info & 0xC0 != 0xC0:
            fcs = 0
            for b in cmd[2:]:
                #print("%x"%b)
                fcs += b
            fcs = fcs & 0xff
            cmd.append(fcs)

        cmd.extend([0x40, 0x45])

        self.ser.write(bytes(cmd))

    def ping(self):
        self.tx(0x40)
        t = 0
        pinfo = 0
        while t < 10000:
            resp = self.rx()

            if resp:
                pinfo = resp[0]
                payload = resp[1]

                if pinfo == 0x80:
                    break

        
        if pinfo == 0:
            raise IOError("Not found?")
        
        #print(payload[0])

        chip_id = struct.unpack("<H", payload[1:3])[0]
        chip_rev = int(payload[3])
        fw_id = int(payload[4])
        fw_rev = struct.unpack("<H", payload[5:])[0]

        print("Found sniffer: ChipID = %x, Chip Rev = %x, FWID = %x, FWRev = %x"%(chip_id, chip_rev, fw_id, fw_rev))

    def rx(self):
        """Receive data"""

        if self.ser.in_waiting:
            data = int(self.ser.read(1)[0])
            if data == 0x40:
                data = int(self.ser.read(1)[0])
                if data == 0x53:
                    #Start received - let's go
                    pinfo = int(self.ser.read(1)[0])
                    plen = self.ser.read(2)
                    plen = struct.unpack("<H", plen)[0]
                    if plen:
                        payload = self.ser.read(plen)
                    else:
                        payload = []
                    if pinfo & 0xC0 != 0xC0:
                        fcs = int(self.ser.read(1)[0])
                    eof = self.ser.read(2)
                    eof = struct.unpack("<H", eof)[0]

                    if pinfo & 0xC0 != 0xC0:
                        #Only check FCS if valid
                        efcs = pinfo + (plen & 0xff) + (plen >> 8)
                        for b in payload:
                            efcs += int(b)
                        
                        efcs &= 0xff

                        if efcs != fcs:
                            raise IOError("FCS Error: %x != %x"%(fcs, efcs))

                    if eof != 0x4540:
                        raise IOError("Invalid EOF - got %x"%eof)
                    
                    #print("Received %x, plen=%d"%(pinfo, plen))

                    return (pinfo, payload)


# Simple example of connecting to device (need to program it w/ firmware)

test = TICommand('COM90')

for phy in range(0, 9):
    for ch in range(0, 129):
        print("Phy = %x, Channel %d"%(phy, ch))
        test.sniff_stop()    
        test.cmd_set_frequencymhz(902.2 + 0.2*ch)
        test.cmd_set_phy(phy)
        test.sniff_start()

        rxd = 0

        for i in range(0, 3):
            time.sleep(1)

            resp = test.rx()
            if resp:
                print(resp)
                rxd += 1