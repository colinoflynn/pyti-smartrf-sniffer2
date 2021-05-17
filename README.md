#TI SmartRF Packet Sniffer 2 Python Interface

TI Makes available a nice packet sniffer firmware, which interfaces to Wireshark. You can see this project here: https://www.ti.com/tool/download/PACKET-SNIFFER-2

Unfortunately sometimes you want to do stuff like scan channels, which is a hassle to do via the GUI. Luckily they document the interface.

## Documentation from TI

The Documentation is installed when you install the Tool, but you can find it online.

Link to documentation: [https://dev.ti.com/tirex/explore/node?node=AJ1gMrg0O1AMxi9KUZmTiQ__FUz-xrs__LATEST](https://dev.ti.com/tirex/explore/node?node=AJ1gMrg0O1AMxi9KUZmTiQ__FUz-xrs__LATEST)

Direct link to firmware interface codes:
[https://software-dl.ti.com/lprf/packet_sniffer_2/docs/user_guide/html/sniffer_fw/firmware/command_interface.html](https://software-dl.ti.com/lprf/packet_sniffer_2/docs/user_guide/html/sniffer_fw/firmware/command_interface.html)

## Errata from TI Docs

The TI documentation claims the serial interface is at 921.6kbit baud, but on my board it was at 3Mbit baud. I'm not sure if all firmware does this or just some of the boards?

## Setup

You'll need to flash the firmware onto your board. Basically ensure the GUI tool works first before trying this interface, as you'll get less feedback with this Python tool.

## Scanning

For example, on my CC1352R1 board I can scan all 900 MHz channels + PHYs:

```python
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
```

Note the PHY index is specified in the reference docs from TI, as each board/chip uses different indexes. Also some of them are using the wrong frequency for the given phy etc, this is a quick-n-dirty way of doing it.