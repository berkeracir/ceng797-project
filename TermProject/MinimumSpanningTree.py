from copy import deepcopy as deepcopy
from enum import Enum
import networkx as nx

from Ahc.Ahc import ComponentModel, Event, EventTypes, GenericMessage, GenericMessageHeader, GenericMessagePayload
from Ahc.Channels import MessageDestinationIdentifiers
from Utility import drawGraph, getPathInMST, getMaximumWeightedEdge, selectDeactivatedNode, optimizeInsertions, \
    optimizeDeletions


class LMSTUpdate:
    def __init__(self, localMST: nx.Graph = None, insertions={}, deletions=[], activatedNodes=[], isCompressed=False):
        if isCompressed:
            self.localMST = None
            self.insertions = insertions
            self.deletions = deletions
            self.activatedNodes = activatedNodes
        else:
            self.localMST = localMST
            self.insertions = {}
            self.deletions = []
            self.activatedNodes = []
        self.isCompressed = isCompressed


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
    def __init__(self, lmstUpdate: LMSTUpdate, manualMode=False, nextActivationNode=-1):
        super().__init__(lmstUpdate)
        self.manualMode = manualMode
        self.nextActivationNode = nextActivationNode


class LOCALMSTMessageHeader(GenericMessageHeader):
    def __init__(self, messagefrom, messageto):
        if messageto == -1:
            super().__init__(MSTMessageTypes.LOCAL_MST, messagefrom, messageto,
                             nexthop=MessageDestinationIdentifiers.LINKLAYERBROADCAST)
        else:
            super().__init__(MSTMessageTypes.LOCAL_MST, messagefrom, messageto, nexthop=messageto)


class MSTMessage(GenericMessage):
    def __init__(self, messagefrom, messageto, messagetype: MSTMessageTypes,
                 messagepayload=None, manualMode=False, nextActivationNode=-1):
        if messagetype == MSTMessageTypes.NEIGHBOR_DISCOVERY:
            super().__init__(header=NEIGHBORMessageHeader(messagefrom, messageto),
                             payload=NEIGHBORMessagePayload())
        elif messagetype == MSTMessageTypes.LOCAL_MST:
            super().__init__(header=LOCALMSTMessageHeader(messagefrom, messageto),
                             payload=LOCALMSTMessagePayload(messagepayload, manualMode, nextActivationNode))


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

        messagefrom = content.header.messagefrom
        messagepayload: LMSTUpdate = payload.messagepayload
        isCompressed = messagepayload.isCompressed
        manualMode = payload.manualMode
        nextActivationNode = payload.nextActivationNode

        receivedInsertions = messagepayload.insertions
        receivedDeletions = messagepayload.deletions
        receivedActivatedNodes = messagepayload.activatedNodes

        if not isCompressed:
            receivedMSTUpdate = messagepayload.localMST
        else:
            if self.localMST is None:
                if len(receivedInsertions) > 0 or len(receivedDeletions) > 0 or len(receivedActivatedNodes) > 0:
                    receivedMSTUpdate = nx.Graph()
                else:
                    receivedMSTUpdate = None
            else:
                receivedMSTUpdate = self.localMST

            if receivedMSTUpdate is not None:
                for u, v in receivedInsertions:
                    if not receivedMSTUpdate.has_edge(u, v):
                        receivedMSTUpdate.add_edge(u, v)
                        receivedMSTUpdate.edges[u, v]['weight'] = receivedInsertions[(u, v)]
                        self.insertions[u, v] = receivedInsertions[(u, v)]
                for u, v in receivedDeletions:
                    if receivedMSTUpdate.has_edge(u, v):
                        receivedMSTUpdate.remove_edge(u, v)
                        self.deletions.add((u, v))
                for node in receivedMSTUpdate.nodes:
                    if node in receivedActivatedNodes:
                        receivedMSTUpdate.nodes[node]['activated'] = True
                    else:
                        if 'activated' not in receivedMSTUpdate.nodes[node]:
                            receivedMSTUpdate.nodes[node]['activated'] = False

        self.activatedNodes.update(receivedActivatedNodes)

        currentNode = self.componentinstancenumber
        decideNextActivation = False

        localInsertions = {}
        localDeletions = set()
        localActivatedNodes = set()

        if receivedMSTUpdate is None:
            S: nx.Graph = nx.Graph()
            S.add_node(self.componentinstancenumber)
            S.nodes[currentNode]['activated'] = True
            decideNextActivation = True
            localActivatedNodes.add(currentNode)

            for (node, weight) in self.neighbors.items():
                S.add_node(node)
                S.nodes[node]['activated'] = False
                S.add_edge(currentNode, node)
                S.edges[currentNode, node]['weight'] = weight
                localInsertions[currentNode, node] = weight
        else:
            S: nx.Graph = deepcopy(receivedMSTUpdate)

            if currentNode in S.nodes:
                if S.nodes[currentNode]['activated']:
                    pass
                else:
                    for (node, weight) in self.neighbors.items():
                        if not S.has_node(node):
                            S.add_node(node)
                            S.nodes[node]['activated'] = False
                            S.add_edge(currentNode, node)
                            S.edges[currentNode, node]['weight'] = weight
                            localInsertions[currentNode, node] = weight
                        else:
                            if not S.has_edge(currentNode, node):
                                path = getPathInMST(S, currentNode, node)
                                maximumWeight, node1, node2 = getMaximumWeightedEdge(S, path)
                                if weight < maximumWeight:
                                    S.remove_edge(node1, node2)
                                    localDeletions.add((node1, node2))
                                    S.add_edge(currentNode, node)
                                    S.get_edge_data(currentNode, node)['weight'] = weight
                                    localInsertions[currentNode, node] = weight

                    S.nodes[currentNode]['activated'] = True
                    decideNextActivation = True
                    localActivatedNodes.add(currentNode)
            else:
                raise NotImplementedError

        self.localMST = S
        localInsertions = optimizeInsertions(localInsertions)
        localDeletions = optimizeDeletions(localDeletions)
        self.insertions.update(localInsertions)
        self.deletions.update(localDeletions)
        self.activatedNodes.update(localActivatedNodes)
        self.optimizeLocalParameters()

        self.latestLocalLMSTUpdate = LMSTUpdate(S, localInsertions, localDeletions, localActivatedNodes, isCompressed)
        self.latestActivationLMSTUpdate = LMSTUpdate(S, self.insertions, self.deletions, self.activatedNodes,
                                                     isCompressed)
        self.latestForwardingLMSTUpdate = LMSTUpdate(S, receivedInsertions, receivedDeletions, receivedActivatedNodes,
                                                     isCompressed)

        if not manualMode:
            if decideNextActivation:
                drawGraph(S, currentNode, self.neighbors, showTopology=True)

                nextActivation = selectDeactivatedNode(S, currentNode, self.neighbors)
                if nextActivation == -1:
                    print(f"Minimum Spanning Tree is constructed.")

                if nextActivation in self.neighbors:
                    localMSTEventContent = MSTMessage(currentNode, nextActivation, MSTMessageTypes.LOCAL_MST,
                                                      messagepayload=self.latestActivationLMSTUpdate)
                    localMSTEvent = Event(self, EventTypes.MFRT, localMSTEventContent)
                    self.send_down(localMSTEvent)
                    nextActivation = -1

                for node in S.neighbors(currentNode):
                    if S.nodes[node]['activated']:
                        localMSTEventContent = MSTMessage(currentNode, node, MSTMessageTypes.LOCAL_MST,
                                                          messagepayload=self.latestLocalLMSTUpdate,
                                                          nextActivationNode=nextActivation)
                        localMSTEvent = Event(self, EventTypes.MFRT, localMSTEventContent)
                        self.send_down(localMSTEvent)
            else:
                if nextActivationNode in self.neighbors:
                    localMSTEventContent = MSTMessage(currentNode, nextActivationNode, MSTMessageTypes.LOCAL_MST,
                                                      messagepayload=self.latestActivationLMSTUpdate)
                    localMSTEvent = Event(self, EventTypes.MFRT, localMSTEventContent)
                    self.send_down(localMSTEvent)
                    nextActivationNode = -1

                for node in S.neighbors(currentNode):
                    if S.nodes[node]['activated'] and node is not messagefrom:
                        localMSTEventContent = MSTMessage(currentNode, node, MSTMessageTypes.LOCAL_MST,
                                                          messagepayload=self.latestForwardingLMSTUpdate,
                                                          nextActivationNode=nextActivationNode)
                        localMSTEvent = Event(self, EventTypes.MFRT, localMSTEventContent)
                        self.send_down(localMSTEvent)
        else:
            if decideNextActivation:
                drawGraph(S, currentNode, self.neighbors, showTopology=True)

                for node in S.neighbors(currentNode):
                    if S.nodes[node]['activated']:
                        localMSTEventContent = MSTMessage(currentNode, node, MSTMessageTypes.LOCAL_MST,
                                                          messagepayload=self.latestLocalLMSTUpdate, manualMode=True)
                        localMSTEvent = Event(self, EventTypes.MFRT, localMSTEventContent)
                        self.send_down(localMSTEvent)
            else:
                if nextActivationNode in S.neighbors(currentNode) or nextActivationNode in self.neighbors:
                    localMSTEventContent = MSTMessage(currentNode, nextActivationNode, MSTMessageTypes.LOCAL_MST,
                                                      messagepayload=self.latestActivationLMSTUpdate, manualMode=True)
                    localMSTEvent = Event(self, EventTypes.MFRT, localMSTEventContent)
                    self.send_down(localMSTEvent)
                    nextActivationNode = -1

                for node in S.neighbors(currentNode):
                    if S.nodes[node]['activated'] and node is not messagefrom:
                        localMSTEventContent = MSTMessage(currentNode, node, MSTMessageTypes.LOCAL_MST,
                                                          messagepayload=self.latestForwardingLMSTUpdate,
                                                          manualMode=True, nextActivationNode=nextActivationNode)
                        localMSTEvent = Event(self, EventTypes.MFRT, localMSTEventContent)
                        self.send_down(localMSTEvent)

    def getNeighbors(self, withWeights=False):
        if not withWeights:
            return [k for k in self.neighbors.keys()]
        else:
            return [(k, v) for k, v in self.neighbors.items()]

    def startMST(self, manualMode=False, compressedMode=True):
        lmstUpdate = LMSTUpdate(isCompressed=compressedMode)
        localMSTEventContent = MSTMessage(self.componentinstancenumber, -1, MSTMessageTypes.LOCAL_MST,
                                          messagepayload=lmstUpdate, manualMode=manualMode)
        localMSTEvent = Event(self, MSTEventTypes.LMST, localMSTEventContent)
        self.send_self(localMSTEvent)

    def sendLocalMSTUpdateManually(self, nodeId: int):
        S = self.localMST
        currentNode = self.componentinstancenumber
        nextActivationNode = nodeId

        if nextActivationNode in S.neighbors(currentNode):
            localMSTEventContent = MSTMessage(currentNode, nextActivationNode, MSTMessageTypes.LOCAL_MST,
                                              messagepayload=self.latestActivationLMSTUpdate, manualMode=True)
            localMSTEvent = Event(self, EventTypes.MFRT, localMSTEventContent)
            self.send_down(localMSTEvent)
        else:
            for node in S.neighbors(currentNode):
                if S.nodes[node]['activated']:
                    localMSTEventContent = MSTMessage(currentNode, node, MSTMessageTypes.LOCAL_MST,
                                                      messagepayload=self.latestLocalLMSTUpdate, manualMode=True,
                                                      nextActivationNode=nextActivationNode)
                    localMSTEvent = Event(self, EventTypes.MFRT, localMSTEventContent)
                    self.send_down(localMSTEvent)

    def __init__(self, componentid):
        componentname = "MSTComponent"
        super().__init__(componentname, componentid)
        self.eventhandlers[MSTEventTypes.MFRNeighbor] = self.on_message_from_neighbor
        self.eventhandlers[MSTEventTypes.LMST] = self.on_local_minimum_spanning_tree

        self.neighbors = {}
        self.localMST: nx.Graph = None
        self.insertions = {}
        self.deletions = set()
        self.activatedNodes = set()

        self.latestActivationLMSTUpdate = None
        self.latestLocalLMSTUpdate = None
        self.latestForwardingLMSTUpdate = None

    def optimizeLocalParameters(self):
        self.insertions = optimizeInsertions(self.insertions)
        self.deletions = optimizeDeletions(self.deletions)
