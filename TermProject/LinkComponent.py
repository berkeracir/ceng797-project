from Ahc.Ahc import ComponentModel, Event

class LinkComponent(ComponentModel):
    def on_init(self, eventobj: Event):
        pass

    def on_message_from_top(self, eventobj: Event):
        self.send_down(eventobj)

    def on_message_from_peer(self, eventobj: Event):
        pass

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(eventobj)

    def __init__(self, componentid):
        componentname = "LinkComponent"
        super().__init__(componentname, componentid)