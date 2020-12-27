import copy
import time
import sys

from Ahc.Ahc import Event, EventTypes
from Ahc.Channels import Channel, ChannelEventTypes, MessageDestinationIdentifiers
from MinimumSpanningTree import MSTMessage, MSTMessageTypes

totalWeight = 0

class NodeChannel(Channel):

    def on_message_from_top(self, eventobj: Event):
        header = eventobj.eventcontent.header
        if header.nexthop == MessageDestinationIdentifiers.LINKLAYERBROADCAST \
                or header.nexthop in self.connectedNodeIds or header.messageto in self.connectedNodeIds:
            myevent = Event(eventobj.eventsource, ChannelEventTypes.INCH, eventobj.eventcontent)
            self.channelqueue.put_nowait(myevent)

    def on_process_in_channel(self, eventobj: Event):
        if isinstance(eventobj.eventcontent, MSTMessage) \
                and eventobj.eventcontent.header.messagetype == MSTMessageTypes.NEIGHBOR_DISCOVERY:
            myeventcontent = copy.deepcopy(eventobj.eventcontent)
            myeventcontent.payload.messagepayload = self.weight
            myevent = Event(eventobj.eventsource, ChannelEventTypes.DLVR, myeventcontent)
            self.outputqueue.put_nowait(myevent)
        else:
            if isinstance(eventobj.eventcontent, MSTMessage) \
                    and eventobj.eventcontent.header.messagetype == MSTMessageTypes.LOCAL_MST:
                global totalWeight
                totalWeight += sys.getsizeof(eventobj)
                print(f"TOTAL WEIGHT = {totalWeight}")
                time.sleep(1)
            myevent = Event(eventobj.eventsource, ChannelEventTypes.DLVR, eventobj.eventcontent)
            self.outputqueue.put_nowait(myevent)

    def on_deliver_to_component(self, eventobj: Event):
        sourceNodeId = eventobj.eventsource.componentinstancenumber
        for connector in self.connectors:
            for node in self.connectors[connector]:
                if node.componentinstancenumber != sourceNodeId:
                    myevent = Event(eventobj.eventsource, EventTypes.MFRB, eventobj.eventcontent, self.componentinstancenumber)
                    node.trigger_event(myevent)

    def __init__(self, componentname, componentinstancenumber, weight=1):
        super().__init__(componentname, componentinstancenumber)
        self.weight = weight
        self.connectedNodeIds = list(map(lambda nodeId: int(nodeId), componentinstancenumber.split("-")))
