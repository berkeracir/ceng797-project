from enum import Enum
import networkx as nx

from Ahc.Ahc import ComponentModel, Event, EventTypes, GenericMessage, GenericMessageHeader, GenericMessagePayload
from Ahc.Channels import MessageDestinationIdentifiers

class LocalMinimumSpanningTreeUpdate:
    def __init__(self, S: nx.graph, activatedNodes: list, deletedEdges: list, insertedEdges: list):
        self.S = S
        self.activatedNodes = activatedNodes
        self.deletedEdges = deletedEdges
        self.insertedEdges = insertedEdges

class MSTEventTypes(Enum):
    MFRNeighbor = "messagefromneighbor"
    LMST = "localminimumspanningtree"

class MSTMessageTypes(Enum):
    NEIGHBOR = "neighbor"
    LOCALMST = "localminimumspanningtree"

class NEIGHBORMessagePayload(GenericMessagePayload):
    def __init__(self, weight=1):
        super().__init__(weight)

class NEIGHBORMessageHeader(GenericMessageHeader):
  def __init__(self, messagefrom, messageto):
      super().__init__(MSTMessageTypes.NEIGHBOR, messagefrom, messageto, nexthop=MessageDestinationIdentifiers.LINKLAYERBROADCAST)

class LOCALMSTMessagePayload(GenericMessagePayload):
    def __init__(self, localMSTUpdate: LocalMinimumSpanningTreeUpdate):
        super().__init__(localMSTUpdate)

class LOCALMSTMessageHeader(GenericMessageHeader):      # TODO
    def __init__(self, messagefrom, messageto):
        super().__init__(MSTMessageTypes.LOCALMST, messagefrom, messageto, nexthop=MessageDestinationIdentifiers.LINKLAYERBROADCAST)

class MSTMessage(GenericMessage):
    def __init__(self, messagefrom, messageto, messagetype: MSTMessageTypes, messagepayload=None):
        if messagetype == MSTMessageTypes.NEIGHBOR:
            super().__init__(NEIGHBORMessageHeader(messagefrom, messageto), NEIGHBORMessagePayload())
        elif messagetype == MSTMessageTypes.LOCALMST:
            super().__init__(LOCALMSTMessageHeader(messagefrom, messageto), LOCALMSTMessagePayload(messagepayload))

class MSTComponent(ComponentModel):
    def on_init(self, eventobj: Event):
        mstMessage = MSTMessage(self.componentinstancenumber, -1, MSTMessageTypes.NEIGHBOR)
        mstEvent = Event(self, EventTypes.MFRT, mstMessage)
        self.send_down(mstEvent)

    def on_message_from_top(self, eventobj: Event):
        pass

    def on_message_from_peer(self, eventobj: Event):
        pass

    def on_message_from_bottom(self, eventobj: Event):
        message = eventobj.eventcontent
        messageType = message.header.messagetype

        if messageType == MSTMessageTypes.NEIGHBOR:
            neighborEvent = Event(eventobj.eventsource, MSTEventTypes.MFRNeighbor, eventobj.eventcontent, eventobj.fromchannel)
            self.send_self(neighborEvent)
        else:
            pass

    def on_message_from_neighbor(self, eventobj: Event):
        linkMessageHeader = eventobj.eventcontent.header
        linkMessagePayload = eventobj.eventcontent.payload

        if linkMessageHeader.messagetype is MSTMessageTypes.NEIGHBOR:
            neighbor = int(linkMessageHeader.messagefrom)
            weight = int(linkMessagePayload.messagepayload)
            self.neighbors[neighbor] = weight
            self.neighbors = dict(sorted(self.neighbors.items(), key=lambda item: item[1]))

    def on_local_minimum_spanning_tree(self, eventobj: Event):
        source = eventobj.eventsource
        type = eventobj.event
        content = eventobj.eventcontent
        header = content.header
        payload = content.payload

        localMSTUpdate: LocalMinimumSpanningTreeUpdate = payload.messagepayload
        S: nx.Graph = localMSTUpdate.S
        activatedNodes: list[int] = localMSTUpdate.activatedNodes
        deletedEdges: list[tuple] = localMSTUpdate.deletedEdges
        insertedEdges: list[tuple] = localMSTUpdate.insertedEdges

        nodes = S.nodes
        edges = S.edges


    def __init__(self, componentid):
        componentname = "MSTComponent"
        super().__init__(componentname, componentid)
        self.neighbors = {}
        self.eventhandlers[MSTEventTypes.MFRNeighbor] = self.on_message_from_neighbor
        self.eventhandlers[MSTEventTypes.LMST] = self.on_local_minimum_spanning_tree

    def getNeighbors(self, withWeights=False):
        if not withWeights:
            return [k for k in self.neighbors.keys()]
        else:
            return [(k, v) for k, v in self.neighbors.items()]

    def startMST(self):
        localMSTUpdate = LocalMinimumSpanningTreeUpdate(nx.Graph(), [], [], [])
        localMSTEventContent = MSTMessage(self.componentinstancenumber, -1, MSTMessageTypes.LOCALMST, localMSTUpdate)
        localMSTEvent = Event(self, MSTEventTypes.LMST, localMSTEventContent)
        self.send_self(localMSTEvent)
