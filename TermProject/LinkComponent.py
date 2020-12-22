import random
import time

from Ahc.Ahc import ComponentModel, Event, EventTypes


class LinkComponent(ComponentModel):
    def on_init(self, eventobj: Event):
        print(f"{self.componentname}.{self.componentinstancenumber} - on_init")

    def on_message_from_top(self, eventobj: Event):
        #print(f"{self.componentname}.{self.componentinstancenumber} - on_message_from_top")
        time.sleep(random.randint(0, 2))
        event = Event(self, EventTypes.MFRT, str(eventobj.eventcontent) + "L")
        self.send_down(event)

    def on_message_from_peer(self, eventobj: Event):
        #print(f"{self.componentname}.{self.componentinstancenumber} - on_message_from_peer")
        pass

    def on_message_from_bottom(self, eventobj: Event):
        #print(f"{self.componentname}.{self.componentinstancenumber} - on_message_from_bottom")
        time.sleep(random.randint(0, 2))
        event = Event(self, EventTypes.MFRB, str(eventobj.eventcontent) + "L")
        self.send_up(event)

    def __init__(self, componentid):
        componentname = "LinkComponent"
        super().__init__(componentname, componentid)