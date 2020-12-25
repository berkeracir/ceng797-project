import networkx as nx
import matplotlib.pyplot as plt

topologyGraph = None


def drawGraph(G: nx.Graph, currentNode=-1, neighbors=[], isTopologyGraph=False):
    global topologyGraph

    if G is not None:
        if topologyGraph is None and isTopologyGraph:
            topologyGraph = G

        if isTopologyGraph:
            pos = nx.get_node_attributes(G, 'pos')
        else:
            if topologyGraph is not None:
                pos = nx.get_node_attributes(topologyGraph, 'pos')
                for node in G.nodes:
                    G.nodes[node]['pos'] = pos[node]
            else:
                pos = nx.spring_layout(G, seed=3)
        nx.draw(G, pos, with_labels=True, font_weight='bold')
        weight_labels = nx.get_edge_attributes(G, 'weight')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=weight_labels)
        activated_labels = nx.get_node_attributes(G, 'activated')
        nx.draw_networkx_labels(G, pos, labels=activated_labels, verticalalignment='bottom', horizontalalignment='left')
        if currentNode != -1:
            if len(neighbors) > 0:
                nx.draw_networkx_nodes(G, pos, nodelist=[currentNode], node_color=(1, 0, 1))
                edgesToDraw = []
                for n in neighbors.keys():
                    if not G.has_edge(currentNode, n):
                        edgesToDraw.append((currentNode, n))
                nx.draw_networkx_edges(G, pos, edgelist=edgesToDraw, style='dashed')
        plt.draw()
        plt.show()
    else:
        print("Graph does not exist!")


def getPathInMST(S: nx.Graph, s: int, d: int):
    neighbors = list(S.neighbors(s))

    if d in neighbors:
        return [s, d]
    else:
        for n in neighbors:
            path = getPathInMST(S, n, d)
            if d in path:
                return [s] + path
    return None


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
