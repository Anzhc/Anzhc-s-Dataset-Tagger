from PyQt5.QtWidgets import QLayout
from PyQt5.QtCore import QRect, QSize, QPoint


class FlowLayout(QLayout):

    def __init__(self, parent=None, margin=0, spacing=0):
        super().__init__(parent)
        self.setSpacing(spacing)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.itemList = []

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList.pop(index)
        return None

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self.doLayout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())
        left, top, right, bottom = self.getContentsMargins()
        size += QSize(left + right, top + bottom)
        return size

    def doLayout(self, rect, testOnly=False):
        x = rect.x()
        y = rect.y()
        lineHeight = 0

        for item in self.itemList:
            widget = item.widget()
            widget.setContentsMargins(0, 0, 0, 0)
            spaceX = self.spacing() + self.contentsMargins().left(
            ) + self.contentsMargins().right()
            spaceY = self.spacing() + self.contentsMargins().top(
            ) + self.contentsMargins().bottom()
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0
            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())
        return y + lineHeight - rect.y()
