from enum import Enum
import matplotlib.pyplot as plt
import networkx as nx
import random

from Ahc.Ahc import Topology
from NodeChannel import NodeChannel
from Node import Node
from Utility import drawGraph

class commands(Enum):   # TODO
    NEIGHBORS = "n"     # "neighbors"
    MST = "m"           # "mst"
    SHOW = "s"          # "show"
    HELP = "help"       # "help"

class arguments(Enum):  # TODO
    # NEIGHBORS
    WEIGHTS = "-w"      # "-weights"
    ALL = "-a"          # "-all"
    # MST
    START = "-s"        # "-start"
    CONTINUE = "-c"     # "-continue"
    # SHOW
    NETWORK = "-n"      # "-network"
    LMST = "-l"      # "-localmst"

def helpUserCommand(cmd: commands):
    if cmd is commands.NEIGHBORS:
        print(f"Show Neighbors:\n"
              f"\t\"{commands.NEIGHBORS.value} {arguments.WEIGHTS.value} {arguments.ALL.value}\"\n"
              f"\t\"{commands.NEIGHBORS.value} nodeId\"\n"
              f"\t\"{commands.NEIGHBORS.value} {arguments.WEIGHTS.value} nodeId\"")
    elif cmd is commands.MST:
        print(f"Start MinimumSpanningTree:\n"
              f"\t\"{commands.MST.value} {arguments.START.value} nodeId\"")
        print(f"Continue MinimumSpanningTree:\n"
              f"\t\"{commands.MST.value} {arguments.CONTINUE.value} sourceNodeId destinationNodeId\"")
    elif cmd is commands.SHOW:
        print(f"Show Network Topology:\n"
              f"\t\"{commands.SHOW.value} {arguments.NETWORK.value}\"")
        print(f"Show Local MinimumSpanningTree:\n"
              f"\t\"{commands.SHOW.value} {arguments.LMST.value}\" nodeId")
    elif cmd is commands.HELP:
        helpUserCommand(commands.NEIGHBORS)
        helpUserCommand(commands.MST)
        helpUserCommand(commands.SHOW)

def neighborsCommand(args: arguments, topology: Topology):
    includeWeights = arguments.WEIGHTS.value in args
    if includeWeights:
        args.remove(arguments.WEIGHTS.value)

    if len(args) == 1:
        allNodes = arguments.ALL.value in args
        nodes = []
        if allNodes:
            for node in topology.nodes.values():
                nodes.append(node)
        else:
            try:
                nodeId = int(args[0])
                node = topology.nodes[nodeId]
                nodes.append(node)
            except KeyError:
                print(f"Node {nodeId} does not exist in the topology.")

        for node in nodes:
            nodeId = node.componentinstancenumber
            neighbors = node.MSTComponent.getNeighbors(includeWeights)
            if (includeWeights):
                neighborsString = ", ".join(map(lambda t: f"{t[0]}({t[1]})", neighbors))
            else:
                neighborsString = ", ".join(map(lambda n: f"{n}", neighbors))
            print(f"Neighbors of Node {nodeId}: {neighborsString}")

    else:
        helpUserCommand(commands.NEIGHBORS)

def mstCommand(args: arguments, topology: Topology):
    mstStart = arguments.START.value in args
    mstContinue = arguments.CONTINUE.value in args

    if mstStart and not mstContinue:
        args.remove(arguments.START.value)

        if len(args) == 1:
            try:
                nodeId = int(args[0])
                topology.nodes.get(nodeId).MSTComponent.startMST()
            except KeyError:
                print(f"Node {nodeId} does not exist in the topology.")
        else:
            helpUserCommand(commands.MST)
    elif mstContinue and not mstStart:
        args.remove(arguments.CONTINUE.value)

        if len(args) == 2:
            try:
                sourceNodeId = int(args[0])
                sourceNode = topology.nodes.get(sourceNodeId)
            except KeyError:
                print(f"Node {sourceNodeId} does not exist in the topology.")
            try:
                destinationNodeId = int(args[1])
            except KeyError:
                print(f"Node {sourceNodeId} does not exist in the topology.")

            if sourceNode.MSTComponent.localMST is not None:
                sourceNode.MSTComponent.sendLocalMSTUpdate(destinationNodeId)
            else:
                print(f"Node {sourceNodeId} does not have LocalMinimumSpanningTree.")
        else:
            helpUserCommand(commands.MST)
    else:
        helpUserCommand(commands.MST)

def showCommand(args: arguments, topology: Topology):
    if arguments.NETWORK.value in args:
        drawGraph(topology.G, isTopologyGraph=True)
    elif arguments.LMST.value in args:
        args.remove(arguments.LMST.value)
        try:
            nodeId = int(args[0])
            node = topology.nodes[nodeId]
            localMST = node.MSTComponent.localMST
            drawGraph(localMST)
        except KeyError:
            print(f"Node {nodeId} does not exist in the topology.")
    else:
        helpUserCommand(commands.SHOW)

def processUserCommand(userInput: str, topology: Topology):
    splitInput = userInput.split(" ")
    cmd = splitInput[0]
    args = []
    if len(splitInput) > 1:
        args = splitInput[1:]

    if cmd == commands.NEIGHBORS.value:
        neighborsCommand(args, topology)
    elif cmd == commands.MST.value:
        mstCommand(args, topology)
    elif cmd == commands.SHOW.value:
        showCommand(args, topology)
    elif cmd == commands.HELP.value:
        helpUserCommand(commands.HELP)
    else:
        argsToString = " ".join(args)
        print(f"Unknown command: {cmd} {argsToString}")


def main():
    G: nx.Graph= nx.random_geometric_graph(5, 0.5, seed=3)      # Remove seed
    #G: nx.Graph = nx.random_geometric_graph(10, 0.5, seed=5)
    for (u, v) in G.edges:
        G.get_edge_data(u, v)['weight'] = u + v + u * v          # random.randint(1, len(G.nodes)) # TODO

    topo = Topology()
    topo.construct_from_graph(G, Node, NodeChannel)
    topo.start()

    drawGraph(G, isTopologyGraph=True)

    while (True):
        userInput = input("\nUser Command:\n")
        processUserCommand(userInput, topo)

if __name__ == "__main__":
    main()
