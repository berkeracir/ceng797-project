import random
import time

from Ahc.Ahc import ComponentModel, Event, ConnectorTypes, EventTypes
from LinkComponent import LinkComponent
from MinimumSpanningTree import MSTComponent
from NetworkComponent import NetworkComponent
from ReliableParameterServer import RPSComponent


class Node(ComponentModel):
    def on_init(self, eventobj: Event):
        print(f"{self.componentname}.{self.componentinstancenumber} - on_init")

    def on_message_from_top(self, eventobj: Event):
        #print(f"{self.componentname}.{self.componentinstancenumber} - {eventobj.eventcontent}")
        time.sleep(random.randint(0, 2))
        event = Event(self, EventTypes.MFRT, str(eventobj.eventcontent) + f"N{self.componentinstancenumber}-")
        self.send_down(event)

    def on_message_from_bottom(self, eventobj: Event):
        #print(f"{self.componentname}.{self.componentinstancenumber} - on_message_from_bottom")
        time.sleep(random.randint(0, 2))
        event = Event(self, EventTypes.MFRB, str(eventobj.eventcontent) + f"N{self.componentinstancenumber}")
        self.send_up(event)

    def __init__(self, componentname, componentid):
        # SUBCOMPONENTS
        self.RPSComponent = RPSComponent(componentid)
        self.NetworkComponent = NetworkComponent(componentid)
        self.MSTComponent = MSTComponent(componentid)
        self.LinkComponent = LinkComponent(componentid)

        # CONNECTIONS AMONG SUBCOMPONENTS
        self.RPSComponent.connect_me_to_component(ConnectorTypes.DOWN, self.NetworkComponent)
        self.RPSComponent.connect_me_to_component(ConnectorTypes.DOWN, self.MSTComponent)

        self.MSTComponent.connect_me_to_component(ConnectorTypes.UP, self.RPSComponent)
        self.NetworkComponent.connect_me_to_component(ConnectorTypes.UP, self.RPSComponent)

        self.MSTComponent.connect_me_to_component(ConnectorTypes.PEER, self.NetworkComponent)
        self.NetworkComponent.connect_me_to_component(ConnectorTypes.PEER, self.MSTComponent)

        self.NetworkComponent.connect_me_to_component(ConnectorTypes.DOWN, self.LinkComponent)
        self.MSTComponent.connect_me_to_component(ConnectorTypes.DOWN, self.LinkComponent)

        self.LinkComponent.connect_me_to_component(ConnectorTypes.UP, self.NetworkComponent)
        self.LinkComponent.connect_me_to_component(ConnectorTypes.UP, self.MSTComponent)

        # Connect the bottom component to the composite component....
        self.LinkComponent.connect_me_to_component(ConnectorTypes.DOWN, self)
        self.connect_me_to_component(ConnectorTypes.UP, self.LinkComponent)

        super().__init__(componentname, componentid)