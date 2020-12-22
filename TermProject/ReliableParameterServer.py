import random
import time

from Ahc.Ahc import ComponentModel, Event, EventTypes


class RPSComponent(ComponentModel):
    def on_init(self, eventobj: Event):
        print(f"{self.componentname}.{self.componentinstancenumber} - on_init")

        if self.componentinstancenumber == 0:
            time.sleep(random.randint(0, 2))
            event = Event(self, EventTypes.MFRT, "R")
            self.send_down(event)

    def on_message_from_bottom(self, eventobj: Event):
        #print(f"{self.componentname}.{self.componentinstancenumber} - on_message_from_bottom")
        print(eventobj.eventcontent)
        time.sleep(random.randint(0, 2))
        event = Event(self, EventTypes.MFRT, str(eventobj.eventcontent) + "R")
        self.send_down(event)

    def __init__(self, componentid):
        componentname = "RPSComponent"
        super().__init__(componentname, componentid)