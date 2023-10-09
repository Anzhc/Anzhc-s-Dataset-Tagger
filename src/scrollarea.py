from PyQt5.QtWidgets import QScrollArea


class CustomScrollArea(QScrollArea):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

    def resizeEvent(self, event):
        self.parent.load_images()
