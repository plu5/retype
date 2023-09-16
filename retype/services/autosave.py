from qt import QObject, QTimer, pyqtSignal, QEvent


class IdleSignal(QObject):
    idle = pyqtSignal()

    def __init__(self, interval):
        super().__init__()
        self.timer = QTimer()
        self.timer.setInterval(interval)
        self.timer.timeout.connect(self.emitIdle)
        self.timer.start()

    def emitIdle(self):
        self.idle.emit()
        self.timer.stop()

    def eventFilter(self, obj, event):
        if event.type() in [QEvent.KeyPress, QEvent.MouseMove]:
            self.timer.start()
        return super().eventFilter(obj, event)


class Autosave(QObject):
    save = pyqtSignal()

    def __init__(self, on=True, interval=5000):
        super().__init__()
        self.on = on
        self.signal = IdleSignal(interval)
        self.signal.idle.connect(self.maybeEmitSave)

    def maybeEmitSave(self):
        if self.on:
            self.save.emit()
