from PyQt6.QtCore import QObject, pyqtSignal, QWaitCondition, QMutex

class GuiDisplayAdapter(QObject):
    text_written = pyqtSignal(str)
    input_request = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self._input_buffer = None
        self._mutex = QMutex()
        self._input_cond = QWaitCondition()

    def show(self, text: str):
        self.text_written.emit(str(text))

    def prompt(self, text: str) -> str:
        self.input_request.emit(text)
        
        self._mutex.lock()
        try:
            self._input_cond.wait(self._mutex)
            return self._input_buffer
        finally:
            self._mutex.unlock()
    
    def set_user_input(self, text: str):
        self._mutex.lock()
        self._input_buffer = text
        self._input_cond.wakeAll()
        self._mutex.unlock()