from enum import Enum
import matplotlib.pyplot as plt
import networkx as nx
import random

from Ahc.Ahc import Topology
from NodeChannel import NodeChannel
from Node import Node

class commands(Enum):
    NEIGHBORS = "n"     # "neighbors"
    MST = "m"           # "mst"

class arguments(Enum):
    WEIGHTS = "-w"      # "-weights"
    ALL = "-a"          # "-all"
    START = "-s"        # "-start"

def helpUserCommand(cmd: commands, arg: arguments=None):
    if cmd is commands.NEIGHBORS:
        print(f"Usage: \'{commands.NEIGHBORS.value} {arguments.WEIGHTS.value} {arguments.ALL.value}"
              f" or \'{commands.NEIGHBORS.value} nodeId\'"
              f" or \'{commands.NEIGHBORS.value} {arguments.WEIGHTS.value} nodeId\'")
    elif cmd is commands.MST:
        print(f"Usage: \'{commands.MST.value} {arguments.START.value} nodeId\'")

def processUserCommand(userInput: str, topology: Topology):
    splittedInput = userInput.split(" ")
    cmd = splittedInput[0]
    args = []
    if len(splittedInput) > 1:
        args = splittedInput[1:]

    if cmd == commands.NEIGHBORS.value:
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
    elif cmd == commands.MST.value:
        mstStart = arguments.START.value in args
        if mstStart:
            args.remove(arguments.START.value)

        if len(args) == 1:
            try:
                nodeId = int(args[0])
                topology.nodes.get(nodeId).MSTComponent.startMST()
            except KeyError:
                print(f"Node {nodeId} does not exist in the topology.")
        else:
            helpUserCommand(commands.MST)
    else:
        argsString = " ".join(args)
        print(f"Unknown command: {cmd} {argsString}")


def main():
    # G = nx.Graph()
    # G.add_nodes_from([1, 2])
    # G.add_edges_from([(1, 2)])
    # nx.draw(G, with_labels=True, font_weight='bold')
    # plt.draw()
    G = nx.random_geometric_graph(5, 0.5, seed=3)  # Remove seed
    for (u, v) in G.edges:
        G.edges[u, v]['weight'] = random.randint(1, len(G.nodes))
    pos = nx.get_node_attributes(G, 'pos')
    nx.draw(G, pos, with_labels=True, font_weight='bold')
    labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
    plt.draw()

    topo = Topology()
    topo.construct_from_graph(G, Node, NodeChannel)
    topo.start()

    plt.show()  # while (True): pass
    while (True):
        userInput = input("User Command:\n")
        processUserCommand(userInput, topo)

if __name__ == "__main__":
    main()
