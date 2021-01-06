import networkx as nx
import matplotlib.pyplot as plt

from sys import setrecursionlimit
setrecursionlimit(5000)

topologyGraph = None
saveIndex = 0
saveName = "Figures/figure_X.png"

activatedNodeColor = '#80ff80'
deactivatedNodeColor = '#ff8080'
activatedCurrentNodeColor = '#008000'
deactivatedCurrentNodeColor = '#800000'


def drawGraph(G: nx.Graph, currentNode=-1, neighbors={}, isTopologyGraph=False, showTopology=False, saveFigures=False):
    global topologyGraph
    global saveIndex, saveName
    global activatedNodeColor, deactivatedNodeColor, activatedCurrentNodeColor, deactivatedCurrentNodeColor

    if G is not None:
        if topologyGraph is None and isTopologyGraph:
            topologyGraph = G

        if isTopologyGraph:
            pos = nx.get_node_attributes(G, 'pos')
            nx.draw(G, pos, with_labels=True, font_weight='bold')
            weight_labels = nx.get_edge_attributes(G, 'weight')
            nx.draw_networkx_edge_labels(G, pos, edge_labels=weight_labels)
        else:
            if topologyGraph is not None:
                pos = nx.get_node_attributes(topologyGraph, 'pos')
                for node in G.nodes:
                    G.nodes[node]['pos'] = pos[node]
                if showTopology:
                    nx.draw(topologyGraph, pos, with_labels=True, style='dotted')
                    weight_labels = nx.get_edge_attributes(G, 'weight')
                    nx.draw_networkx_edge_labels(G, pos, edge_labels=weight_labels)
            else:
                pos = nx.spring_layout(G, seed=3)

            activatedNodes = []
            deactivatedNodes = []
            for node in G.nodes:
                if G.nodes[node]['activated']:
                    activatedNodes.append(node)
                else:
                    deactivatedNodes.append(node)

            nx.draw(G, pos, with_labels=True, font_weight='bold')
            weight_labels = nx.get_edge_attributes(G, 'weight')
            nx.draw_networkx_edge_labels(G, pos, edge_labels=weight_labels)
            # activated_labels = nx.get_node_attributes(G, 'activated')
            # nx.draw_networkx_labels(G, pos, labels=activated_labels, verticalalignment='bottom', horizontalalignment='left')
            nx.draw_networkx_nodes(G, pos, nodelist=activatedNodes, node_color=activatedNodeColor)
            nx.draw_networkx_nodes(G, pos, nodelist=deactivatedNodes, node_color=deactivatedNodeColor)

            if currentNode != -1:
                if G.nodes[currentNode]['activated']:
                    nodeColor = activatedCurrentNodeColor
                else:
                    nodeColor = deactivatedCurrentNodeColor
                nx.draw_networkx_nodes(G, pos, nodelist=[currentNode], node_color=nodeColor)

                if len(neighbors) > 0:
                    edgesToDraw = []
                    weightsToDraw = {}
                    for n, w in neighbors.items():
                        if not G.has_edge(currentNode, n):
                            edgesToDraw.append((currentNode, n))
                            weightsToDraw[(currentNode, n)] = w
                    if not showTopology:
                        nx.draw_networkx_edges(G, pos, edgelist=edgesToDraw, style='dotted')
                    nx.draw_networkx_edge_labels(G, pos, edge_labels=weightsToDraw)

        plt.draw()
        if saveFigures:
            plt.savefig(saveName.replace("X", str(saveIndex)), format="PNG")
            saveIndex += 1
        plt.show()
    else:
        print("Graph does not exist!")


def getPathInMST(S: nx.Graph, s: int, d: int, prevNode=-1):
    unvisitedNeighbors = list(S.neighbors(s))
    if prevNode in unvisitedNeighbors:
        unvisitedNeighbors.remove(prevNode)

    if d in unvisitedNeighbors:
        return [s, d]
    else:
        for n in unvisitedNeighbors:
            path = getPathInMST(S, n, d, s)
            if d in path:
                return [s] + path
        return [s]


def getMaximumWeightedEdge(S: nx.Graph, path: list):
    weight = float('-inf')

    i = 0
    while i < len(path) - 1:
        edgeWeight = S.get_edge_data(path[i], path[i + 1])['weight']
        if edgeWeight > weight:
            weight = edgeWeight
            nodes = (path[i], path[i + 1])
        i += 1
    return weight, nodes[0], nodes[1]


def getPathCost(S: nx.Graph, path: list):
    weight = 0
    i = 0
    while i < len(path) - 1:
        weight += S.get_edge_data(path[i], path[i + 1])['weight']
        i += 1
    return weight


def selectDeactivatedNode(S: nx.Graph, currentNode: int, neighbors):
    deactivatedNodes = []
    for node in S.nodes:
        if not S.nodes[node]['activated']:
            path = getPathInMST(S, currentNode, node)
            pathCost = getPathCost(S, path)
            hopCount = len(path) - 1
            deactivatedNodes.append((node, pathCost, hopCount))

            # if node in neighbors:
            #     path = [currentNode, node]
            #     pathCost = neighbors[node]
            #     hopCount = 1
            #     deactivatedNodes.append((node, pathCost, hopCount))
    deactivatedNodes.sort(key=lambda r: (r[1], r[2]))

    if len(deactivatedNodes) > 0:
        return deactivatedNodes[0][0]
    else:
        return -1


def optimizeInsertions(I: dict):
    insertions = dict(I)
    keys = list(I.keys())
    for u, v in keys:
        w = insertions[u, v]
        if u > v:
            insertions.pop((u, v))
            insertions[v, u] = w
    return insertions


def optimizeDeletions(D: set):
    deletions = set(D)
    l = list(D)
    for u, v in l:
        if u > v:
            deletions.remove((u, v))
            deletions.add((v, u))
    return deletions
