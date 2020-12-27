from enum import Enum
import matplotlib.pyplot as plt
import networkx as nx
import random
import time

from Ahc.Ahc import Topology
from NodeChannel import NodeChannel
from Node import Node
from Utility import drawGraph, getPathInMST


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
    RANDOM = "-r"       # "-random"
    MANUAL = "-m"       # "-manuel"
    CONTINUE = "-c"     # "-continue"
    # SHOW
    NETWORK = "-n"      # "-network"
    LMST = "-l"         # "-localmst"
    LMST_PATH = "-p"    # "-path"

lastLocalMSTUpdatedNode = -1
localMSTManualMode = False

def helpUserCommand(cmd: commands):
    if cmd is commands.NEIGHBORS:
        print(f"Show Neighbors:\n"
              f"\t\"{commands.NEIGHBORS.value} {arguments.WEIGHTS.value} {arguments.ALL.value}\"\n"
              f"\t\"{commands.NEIGHBORS.value} nodeId\"\n"
              f"\t\"{commands.NEIGHBORS.value} {arguments.WEIGHTS.value} nodeId\"")
    elif cmd is commands.MST:
        print(f"Start Minimum Spanning Tree Algorithm:\n"
              f"\t\"{commands.MST.value} {arguments.START.value} nodeId\"\n"
              f"\t\"{commands.MST.value} {arguments.START.value} {arguments.RANDOM.value}\"\n"
              f"\t\"{commands.MST.value} {arguments.START.value} {arguments.MANUAL.value} nodeId\"\n"
              f"\t\"{commands.MST.value} {arguments.START.value} {arguments.MANUAL.value} {arguments.RANDOM.value}\"")
        print(f"Continue Minimum Spanning Tree Algorithm Manually:\n"
              f"\t\"{commands.MST.value} {arguments.CONTINUE.value} destinationNodeId\"\n"
              f"\t\"{commands.MST.value} {arguments.CONTINUE.value} sourceNodeId destinationNodeId\"")
    elif cmd is commands.SHOW:
        print(f"Show Network Topology:\n"
              f"\t\"{commands.SHOW.value} {arguments.NETWORK.value}\"")
        print(f"Show Local MinimumSpanningTree:\n"
              f"\t\"{commands.SHOW.value} {arguments.LMST.value}\" nodeId")
        print(f"Show Path in Local MinimumSpanningTree:\n"
              f"\t\"{commands.SHOW.value} {arguments.LMST_PATH.value}\" sourceNodeId destinationNodeId")
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
                return
            except ValueError:
                print(f"\'{args[0]}\' is not integer.")
                return

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
    global lastLocalMSTUpdatedNode, localMSTManualMode

    mstStart = arguments.START.value in args
    mstContinue = arguments.CONTINUE.value in args

    if mstStart and not mstContinue:
        args.remove(arguments.START.value)
        mstManual = arguments.MANUAL.value in args
        mstRandom = arguments.RANDOM.value in args
        if mstManual:
            args.remove(arguments.MANUAL.value)
            localMSTManualMode = True
        if mstRandom:
            args.remove(arguments.RANDOM.value)

            if len(args) == 0:
                try:
                    randomNodeId = random.randint(0, len(topology.nodes) - 1)
                    randomNode = topology.nodes.get(randomNodeId)
                except KeyError:
                    print(f"Node {randomNodeId} does not exist in the topology.")
                    return
                randomNode.MSTComponent.startMST(localMSTManualMode)
                lastLocalMSTUpdatedNode = randomNodeId
            else:
                helpUserCommand(commands.MST)
        else:
            if len(args) == 1:
                try:
                    nodeId = int(args[0])
                    node = topology.nodes.get(nodeId)
                except KeyError:
                    print(f"Node {nodeId} does not exist in the topology.")
                    return
                except ValueError:
                    print(f"\'{args[0]}\' is not integer.")
                    return
                node.MSTComponent.startMST(localMSTManualMode)
                lastLocalMSTUpdatedNode = nodeId
            else:
                helpUserCommand(commands.MST)
    elif mstContinue and not mstStart:
        if localMSTManualMode:
            args.remove(arguments.CONTINUE.value)

            if len(args) == 1:
                if lastLocalMSTUpdatedNode != -1:
                    sourceNodeId = lastLocalMSTUpdatedNode
                    sourceNode = topology.nodes.get(sourceNodeId)
                    try:
                        destinationNodeId = int(args[0])
                    except KeyError:
                        print(f"Node {destinationNodeId} does not exist in the topology.")
                        return
                    except ValueError:
                        print(f"\'{args[0]}\' is not integer.")
                        return

                    if sourceNode.MSTComponent.localMST is not None:
                        if destinationNodeId in sourceNode.MSTComponent.localMST.nodes:
                            sourceNode.MSTComponent.sendLocalMSTUpdateManually(destinationNodeId)
                            lastLocalMSTUpdatedNode = destinationNodeId
                        else:
                            print(f"Local Minimum Spanning Tree of Source Node {sourceNodeId} does not contain "
                                  f"Destination Node {destinationNodeId}.")
                    else:
                        print(f"Node {sourceNodeId} does not have LocalMinimumSpanningTree.")
                else:
                    print(f"Minimum Spanning Tree algorithm must be started manually before continuing.")
            elif len(args) == 2:
                try:
                    sourceNodeId = int(args[0])
                    sourceNode = topology.nodes.get(sourceNodeId)
                except KeyError:
                    print(f"Node {sourceNodeId} does not exist in the topology.")
                    return
                except ValueError:
                    print(f"\'{args[0]}\' is not integer.")
                    return
                try:
                    destinationNodeId = int(args[1])
                except KeyError:
                    print(f"Node {destinationNodeId} does not exist in the topology.")
                    return
                except ValueError:
                    print(f"\'{args[1]}\' is not integer.")
                    return

                if sourceNode.MSTComponent.localMST is not None:
                    if destinationNodeId in sourceNode.MSTComponent.localMST.nodes:
                        sourceNode.MSTComponent.sendLocalMSTUpdateManually(destinationNodeId)
                        lastLocalMSTUpdatedNode = destinationNodeId
                    else:
                        print(f"Local Minimum Spanning Tree of Source Node {sourceNodeId} does not contain "
                              f"Destination Node {destinationNodeId}.")
                else:
                    print(f"Node {sourceNodeId} does not have LocalMinimumSpanningTree.")
            else:
                helpUserCommand(commands.MST)
        else:
            if lastLocalMSTUpdatedNode == -1:
                print(f"Minimum Spanning Tree algorithm did not started.")
            else:
                print(f"Minimum Spanning Tree algorithm did not started in manual mode.")
    else:
        helpUserCommand(commands.MST)

def showCommand(args: arguments, topology: Topology):
    if arguments.NETWORK.value in args:
        drawGraph(topology.G, isTopologyGraph=True)
    elif arguments.LMST.value in args:
        args.remove(arguments.LMST.value)

        if len(args) == 1:
            try:
                nodeId = int(args[0])
                node = topology.nodes[nodeId]
            except KeyError:
                print(f"Node {nodeId} does not exist in the topology.")
                return
            except ValueError:
                print(f"\'{args[0]}\' is not integer.")
                return
            localMST = node.MSTComponent.localMST
            neighbors = node.MSTComponent.neighbors
            drawGraph(localMST, currentNode=nodeId, neighbors={}, showTopology=False)
        else:
            helpUserCommand(commands.SHOW)
    elif arguments.LMST_PATH.value in args:
        args.remove(arguments.LMST_PATH.value)
        if len(args) == 2:
            try:
                sourceNodeId = int(args[0])
                sourceNode = topology.nodes[sourceNodeId]
            except KeyError:
                print(f"Node {sourceNodeId} does not exist in the topology.")
                return
            except ValueError:
                print(f"\'{args[0]}\' is not integer.")
                return
            try:
                destinationNodeId = int(args[1])
                destinationNode = topology.nodes[sourceNodeId]
            except KeyError:
                print(f"Node {destinationNodeId} does not exist in the topology.")
                return
            except ValueError:
                print(f"\'{args[1]}\' is not integer.")
                return
            localMST = sourceNode.MSTComponent.localMST
            drawGraph(localMST, showTopology=False)
            print(f"Path from Node {sourceNodeId} to Node {destinationNodeId}: "
                  f"{getPathInMST(localMST, sourceNodeId, destinationNodeId)}")
        else:
            helpUserCommand(commands.SHOW)
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
        print(f"Unknown input: \'{userInput}\'")

def main():
    # G: nx.Graph= nx.random_geometric_graph(5, 0.5, seed=3)
    G: nx.Graph = nx.random_geometric_graph(14, 0.4, seed=1)
    # G: nx.Graph = nx.random_geometric_graph(15, 0.4, seed=3)
    for (u, v) in G.edges:
        G.get_edge_data(u, v)['weight'] = u + v + u * v # random.randint(1, len(G.nodes))   # u + v + u * v # TODO

    topo = Topology()
    topo.construct_from_graph(G, Node, NodeChannel)
    topo.start()

    drawGraph(G, isTopologyGraph=True)

    while True:
        userInput = input("\nUser Command:\n")
        processUserCommand(userInput, topo)
        time.sleep(1)

if __name__ == "__main__":
    main()
