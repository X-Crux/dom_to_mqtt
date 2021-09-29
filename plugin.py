# MQTT to HomeKit plugin

"""
<plugin key="MQTT to HomeKit plugin" name="MQTT to HomeKit">
  <description>
    <h2>MQTT to HomeKit plugin</h2>
  </description>
    <params>
        <h3>MQTT</h3>
        <param field="Username" label="Username" width="200px" />
        <param field="Password" label="Password" width="200px" />
        <param field="Broker" label="IP Broker" width="200px" />
        <param field="Port" label="Port" width="200px" />
        <param field="Topic" label="Domoticz Topic" width="200px" />
        <h3>Domoticz</h3>
        <param field="Url" label="Host:Port" width="200px" />
    </params>
    <p id="pairing_digits"></p>
    <div class="qr_container">
    </div>
</plugin>
"""

import Domoticz
import subprocess
# from multiprocessing import Process
from Domoticz import Parameters, Devices


class BasePlugin:
    enabled = False
    mqttConn = None
    counter = 0

    def __init__(self):
        return

    def onStart(self):
        Domoticz.Log("MQTT to HomeKit onStart called")

        # = = = = = = = = = Config = = = = = = = = =

        # [mqtt]
        username = Parameters["Username"]
        password = Parameters["Password"]
        broker = Parameters["Broker"]
        port = int(Parameters["Port"])
        topic = Parameters["Topic"]

        # [domoticz]
        url = Parameters["Url"]

        # = = = = = = = = = = = = = = = = = = = = =

        # [mqtt]
        # username = "user"
        # password = "user"
        # # broker = "l.com"
        # broker = "192.168.1.1"
        # port = 1883
        # # topic = "Grigory/domoticz/#"
        # topic = "domoticz/#"
        # # Domoticz/#
        #
        # [domoticz]
        # # url = "127.0.0.1:8080"
        # url = "192.168.1.1:8080"

        # if hk_proc.is_alive():
        #     try:
        #         hk_proc.terminate()
        #         time.sleep(1)
        #         log.debug("Process is terminating success")
        #     except Exception:
        #         hk_proc.kill()
        #         log.debug("Process is killing success")
        #
        # hk_proc = Process(target=start_hk, args=())
        # hk_proc.start()

        cmd = f"./Domoticz_HAP -mqtt.address {broker}:{port} -mqtt.password {password} -mqtt.username {username}"
        subprocess.call(cmd, shell=True)

        cmd = f"python3 main.py -u {username} -p {password} -b {broker} -s {port} -t {topic} -h {url}"
        subprocess.call(cmd, shell=True)

        DumpConfigToLog()

        Domoticz.Log("MQTT to HomeKit started")

    def onStop(self):
        Domoticz.Log("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Log("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log(
            "onCommand called for Unit " + str(Unit) + ": Parameter '" + str(
                Command) + "', Level: " + str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound,
                       ImageFile):
        Domoticz.Log(
            "Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(
                Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Log("onHeartbeat called")


global _plugin
_plugin = BasePlugin()


def onStart():
    global _plugin
    _plugin.onStart()


def onStop():
    global _plugin
    _plugin.onStop()


def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)


def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)


def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)


def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound,
                           ImageFile)


def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)


def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()


# Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug("'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug(
            "Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return