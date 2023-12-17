from qt import QObject, QTimer, pyqtSignal


class IdleSignal(QObject):
    idle = pyqtSignal()

    def __init__(self, console, interval):
        super().__init__()
        self.timer = QTimer()
        self.timer.setInterval(interval)
        self.timer.timeout.connect(self.emitIdle)
        console.textEdited.connect(self.onUpdate)

    def emitIdle(self):
        self.idle.emit()
        self.timer.stop()

    def onUpdate(self):
        self.timer.start()


class Autosave(QObject):
    save = pyqtSignal()

    def __init__(self, console, on=True, interval=5000):
        super().__init__()
        self.on = on
        self.signal = IdleSignal(console, interval)
        self.signal.idle.connect(self.maybeEmitSave)

    def maybeEmitSave(self):
        if self.on:
            self.save.emit()
