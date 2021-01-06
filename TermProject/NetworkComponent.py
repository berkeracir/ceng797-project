from Ahc.Ahc import ComponentModel, Event


class NetworkComponent(ComponentModel):
    def on_init(self, eventobj: Event):
        pass

    def on_message_from_top(self, eventobj: Event):
        pass

    def on_message_from_peer(self, eventobj: Event):
        pass

    def on_message_from_bottom(self, eventobj: Event):
        pass

    def __init__(self, componentid):
        componentname = "NetworkComponent"
        super().__init__(componentname, componentid)