from copy import deepcopy as deepcopy
from enum import Enum
import networkx as nx

from Ahc.Ahc import ComponentModel, Event, EventTypes, GenericMessage, GenericMessageHeader, GenericMessagePayload
from Ahc.Channels import MessageDestinationIdentifiers
from Utility import drawGraph, getPathInMST, getMaximumWeightedEdge


class LocalMinimumSpanningTreeUpdate:
    def __init__(self, S: nx.graph):
        self.S = S


class MSTEventTypes(Enum):
    MFRNeighbor = "messagefromneighbor"
    LMST = "localminimumspanningtree"


class MSTMessageTypes(Enum):
    NEIGHBOR_DISCOVERY = "neighbordiscovery"
    LOCAL_MST = "localminimumspanningtree"


class NEIGHBORMessagePayload(GenericMessagePayload):
    def __init__(self, weight=1):
        super().__init__(weight)


class NEIGHBORMessageHeader(GenericMessageHeader):
    def __init__(self, messagefrom, messageto):
        super().__init__(MSTMessageTypes.NEIGHBOR_DISCOVERY, messagefrom, messageto,
                         nexthop=MessageDestinationIdentifiers.LINKLAYERBROADCAST)


class LOCALMSTMessagePayload(GenericMessagePayload):
    def __init__(self, localMST: nx.Graph):
        super().__init__(localMST)


class LOCALMSTMessageHeader(GenericMessageHeader):  # TODO
    def __init__(self, messagefrom, messageto):
        if messageto == -1:
            super().__init__(MSTMessageTypes.LOCAL_MST, messagefrom, messageto,
                             nexthop=MessageDestinationIdentifiers.LINKLAYERBROADCAST)
        else:
            super().__init__(MSTMessageTypes.LOCAL_MST, messagefrom, messageto, nexthop=messageto)


class MSTMessage(GenericMessage):
    def __init__(self, messagefrom, messageto, messagetype: MSTMessageTypes, messagepayload=None):
        if messagetype == MSTMessageTypes.NEIGHBOR_DISCOVERY:
            super().__init__(NEIGHBORMessageHeader(messagefrom, messageto), NEIGHBORMessagePayload())
        elif messagetype == MSTMessageTypes.LOCAL_MST:
            super().__init__(LOCALMSTMessageHeader(messagefrom, messageto), LOCALMSTMessagePayload(messagepayload))


class MSTComponent(ComponentModel):
    def on_init(self, eventobj: Event):
        mstMessage = MSTMessage(self.componentinstancenumber, -1, MSTMessageTypes.NEIGHBOR_DISCOVERY)
        mstEvent = Event(self, EventTypes.MFRT, mstMessage)
        self.send_down(mstEvent)

    def on_message_from_top(self, eventobj: Event):
        pass

    def on_message_from_peer(self, eventobj: Event):
        pass

    def on_message_from_bottom(self, eventobj: Event):
        message = eventobj.eventcontent
        messageType = message.header.messagetype

        if messageType is MSTMessageTypes.NEIGHBOR_DISCOVERY:
            neighborEvent = Event(eventobj.eventsource, MSTEventTypes.MFRNeighbor, eventobj.eventcontent,
                                  eventobj.fromchannel)
            self.send_self(neighborEvent)
        elif messageType is MSTMessageTypes.LOCAL_MST:
            neighborEvent = Event(eventobj.eventsource, MSTEventTypes.LMST, eventobj.eventcontent, eventobj.fromchannel)
            self.send_self(neighborEvent)
        else:
            pass

    def on_message_from_neighbor(self, eventobj: Event):
        linkMessageHeader = eventobj.eventcontent.header
        linkMessagePayload = eventobj.eventcontent.payload

        neighbor = int(linkMessageHeader.messagefrom)
        weight = int(linkMessagePayload.messagepayload)
        self.neighbors[neighbor] = weight
        self.neighbors = dict(sorted(self.neighbors.items(), key=lambda item: item[1]))

    def on_local_minimum_spanning_tree(self, eventobj: Event):
        content = eventobj.eventcontent
        payload = content.payload

        currentNode = self.componentinstancenumber
        receivedMSTUpdate: nx.Graph = payload.messagepayload

        if receivedMSTUpdate is None:
            S: nx.Graph = nx.Graph()
            S.add_node(self.componentinstancenumber)

            for (node, weight) in self.neighbors.items():
                S.add_node(node)
                S.nodes[node]['activated'] = False
                S.add_edge(currentNode, node)
                S.edges[currentNode, node]['weight'] = weight
        else:
            S: nx.Graph = deepcopy(receivedMSTUpdate)

            for (node, weight) in self.neighbors.items():
                if not S.has_node(node):
                    S.add_node(node)
                    S.nodes[node]['activated'] = False
                    S.add_edge(currentNode, node)
                    S.edges[currentNode, node]['weight'] = weight
                else:
                    if not S.has_edge(currentNode, node):
                        path = getPathInMST(S, currentNode, node)
                        maximumWeight, node1, node2 = getMaximumWeightedEdge(S, path)

                        if weight < maximumWeight:
                            S.remove_edge(node1, node2)
                            S.add_edge(currentNode, node)
                            S.get_edge_data(currentNode, node)['weight'] = weight

        S.nodes[currentNode]['activated'] = True
        self.localMST = S
        drawGraph(self.localMST, currentNode, self.neighbors)

    def __init__(self, componentid):
        componentname = "MSTComponent"
        super().__init__(componentname, componentid)
        self.eventhandlers[MSTEventTypes.MFRNeighbor] = self.on_message_from_neighbor
        self.eventhandlers[MSTEventTypes.LMST] = self.on_local_minimum_spanning_tree

        self.neighbors = {}
        self.localMST: nx.Graph = None

    def getNeighbors(self, withWeights=False):
        if not withWeights:
            return [k for k in self.neighbors.keys()]
        else:
            return [(k, v) for k, v in self.neighbors.items()]

    def startMST(self):
        localMSTEventContent = MSTMessage(self.componentinstancenumber, self.componentinstancenumber,
                                          MSTMessageTypes.LOCAL_MST)
        localMSTEvent = Event(self, MSTEventTypes.LMST, localMSTEventContent)
        self.send_self(localMSTEvent)

    def sendLocalMSTUpdate(self, nodeId: int):
        localMSTEventContent = MSTMessage(self.componentinstancenumber, nodeId, MSTMessageTypes.LOCAL_MST,
                                          self.localMST)
        localMSTEvent = Event(self, EventTypes.MFRT, localMSTEventContent)
        self.send_down(localMSTEvent)