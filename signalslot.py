class SignalSlot(object):
    def __init__(self):
        self._SSPool = {}

    def connect(self, signal, slot):
        if(signal not in self._SSPool):
            self._SSPool[signal] = [];
        if(slot not in self._SSPool[signal]):
            self._SSPool[signal].append(slot);

    def emit(self, signal, *args):
        if(signal in self._SSPool):
            slots = self._SSPool[signal];
            for i in range(len(slots)):
                slots[i](*args);

    def disconnect(self, signal, slot):
        if slot in self._SSPool[signal]:
            self._SSPool[signal].remove(slot)

class SignalSlotInterface(SignalSlot):
    def __init__(self):
        super(SignalSlotInterface, self).__init__()

    #############
    def register_indicator_select(self, func):
        return self.connect('indicator', func)

    def unregister_indicator_select(self, func):
        return self.disconnect('indicator', func)

    def indicator_select(self, indicator):
        return self.emit('indicator', indicator)

    #############
    def register_plat_select(self, func):
        return self.connect('plat', func)

    def unregister_plat_select(self, func):
        return self.disconnect('plat', func)

    def plat_select(self, plat):
        return self.emit('plat', plat)

    #############
    def register_pair_select(self, func):
        return self.connect('pair', func)

    def unregister_pair_select(self, func):
        return self.disconnect('pair', func)

    def pair_select(self, pair):
        return self.emit('pair', pair)

    #############
    def register_other_select(self, func):
        return self.connect('other', func)

    def unregister_other_select(self, func):
        return self.disconnect('other', func)

    def other_select(self, other):
        return self.emit('other', other)

    #############
    def register_robot_log(self, func):
        return self.connect('robotlog', func)

    def unregister_robot_log(self, func):
        return self.disconnect('robotlog', func)

    def robot_log(self, log):
        return self.emit('robotlog', log)

    #############
    def register_trade_log(self, func):
        return self.connect('tradelog', func)

    def unregister_trade_log(self, func):
        return self.disconnect('tradelog', func)

    def trade_log(self, log):
        return self.emit('tradelog', log)

sslot = SignalSlotInterface()
