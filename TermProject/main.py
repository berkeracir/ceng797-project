import networkx as nx
import matplotlib.pyplot as plt

from Ahc.Ahc import Topology
from Ahc.Channels import FIFOBroadcastPerfectChannel
from Node import Node


def main():
    # G = nx.Graph()
    # G.add_nodes_from([1, 2])
    # G.add_edges_from([(1, 2)])
    # nx.draw(G, with_labels=True, font_weight='bold')
    # plt.draw()
    G = nx.random_geometric_graph(5, 0.5)
    nx.draw(G, with_labels=True, font_weight='bold')
    plt.draw()

    topo = Topology()
    topo.construct_from_graph(G, Node, FIFOBroadcastPerfectChannel)
    topo.start()

    plt.show()  # while (True): pass
    while (True):
        pass


if __name__ == "__main__":
    main()
