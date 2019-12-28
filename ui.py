from PyQt5.QtCore import QDir, Qt
from PyQt5.QtGui import QImage, QPainter, QPalette, QPixmap
from PyQt5.QtWidgets import (QAction, QApplication, QFileDialog, QLabel,
        QMainWindow, QMenu, QMessageBox, QScrollArea, QSizePolicy)

from PyQt5 import QtWidgets, QtGui, QtCore

from project import Project, Photo

# https://stackoverflow.com/questions/52751121/pyqt-user-editable-polygons

class GripItem(QtWidgets.QGraphicsPathItem):
    circle = QtGui.QPainterPath()
    circle.addEllipse(QtCore.QRectF(-5, -5, 10, 10))

    def __init__(self, annotation_item, index):
        super(GripItem, self).__init__()
        self.m_annotation_item = annotation_item
        self.m_index = index

        self.setPath(GripItem.circle)
        self.setBrush(QtGui.QColor("red"))
        self.setPen(QtGui.QPen(QtGui.QColor("red"), 2))
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(11)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

    def hoverEnterEvent(self, event):
        self.setBrush(QtGui.QColor(0, 0, 0, 0))
        super(GripItem, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(QtGui.QColor("red"))
        super(GripItem, self).hoverLeaveEvent(event)

    def mouseReleaseEvent(self, event):
        self.setSelected(False)
        super(GripItem, self).mouseReleaseEvent(event)
        self.scene().pointsChanged.emit(self.m_annotation_item.getPoints())

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.ItemPositionChange and self.isEnabled():
            self.m_annotation_item.movePoint(self.m_index, value)
        return super(GripItem, self).itemChange(change, value)


class PolygonAnnotation(QtWidgets.QGraphicsPolygonItem):
    def __init__(self, parent=None):
        super(PolygonAnnotation, self).__init__(parent)
        self.setZValue(10)
        self.setPen(QtGui.QPen(QtGui.QColor("red"), 0))
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges, True)
        self.m_items = []

    def setPoints(self, points):
        for i in self.m_items:
            self.scene().removeItem(i)
        
        self.m_items = []
        
        points = [QtCore.QPointF(x, y) for x, y in points]
        
        for i, p in enumerate(points):
            item = GripItem(self, i)
            item.setPos(p)
            self.scene().addItem(item)
            self.m_items.append(item)

        self.setPolygon(QtGui.QPolygonF(points))

    def getPoints(self):
        return [(pt.x(), pt.y()) for pt in self.polygon()]

    def movePoint(self, i, p):
        polygon = self.polygon()
        if 0 <= i < len(polygon):
            polygon[i] = self.mapFromScene(p)
            self.setPolygon(polygon)

class AnnotationScene(QtWidgets.QGraphicsScene):
    pointsChanged = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        super(AnnotationScene, self).__init__(parent)
        self.image_item = QtWidgets.QGraphicsPixmapItem()
        self.image_item.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
        self.addItem(self.image_item)

        self.polygon_item = PolygonAnnotation()
        self.addItem(self.polygon_item)

    def load_image(self, filename, points=None):
        self.image_item.setPixmap(QtGui.QPixmap(filename))
        rect = self.image_item.boundingRect()
        self.setSceneRect(QtCore.QRectF(-rect.width(), -rect.height(), rect.width()*3, rect.height()*3))

        if points is None:
            points = [
                (1*rect.width()/4, 1*rect.height()/4),
                (3*rect.width()/4, 1*rect.height()/4),
                (3*rect.width()/4, 3*rect.height()/4),
                (1*rect.width()/4, 3*rect.height()/4),
            ]

        self.polygon_item.setPoints(points)

class AnnotationView(QtWidgets.QGraphicsView):
    def __init__(self, parent=None):
        super(AnnotationView, self).__init__(parent)
        self.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)
        self.setMouseTracking(True)
        self.setTransformationAnchor(self.AnchorUnderMouse)
        self.setResizeAnchor(self.AnchorUnderMouse)
        self.setDragMode(self.ScrollHandDrag)

    @QtCore.pyqtSlot()
    def wheelEvent(self, event):
        if self.scene() is not None:
            delta = event.angleDelta().y()
            factor = 1.002 ** delta
            self.scale(factor,factor)

class ImageViewer(QMainWindow):
    def __init__(self, base):
        super(ImageViewer, self).__init__()

        self.project = Project(base)

        self.widget = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout()

        self.view = AnnotationView()
        self.scene = AnnotationScene(self)
        self.view.setScene(self.scene)
        vbox.addWidget(self.view)

        prevButton = QtWidgets.QPushButton("Previous")
        prevButton.clicked.connect(lambda e: self.load_image(self.photo_index-1))
        nextButton = QtWidgets.QPushButton("Next")
        nextButton.clicked.connect(lambda e: self.load_image(self.photo_index+1))

        toolbar = QtWidgets.QHBoxLayout()
        toolbar.addWidget(prevButton)
        toolbar.addStretch(1)
        toolbar.addWidget(nextButton)
        vbox.addLayout(toolbar)

        self.widget.setLayout(vbox)
        self.setCentralWidget(self.widget)

        self.scene.pointsChanged.connect(self.savePoints)

        self.load_image(0)

    def load_image(self, i):
        self.photo_index = i % len(self.project.photos)
        photo = self.project.photos[self.photo_index]
        print("load image", self.photo_index, photo.path)
        self.scene.load_image(photo.fname(), photo.polygon)
        self.view.fitInView(self.scene.image_item, QtCore.Qt.KeepAspectRatio)
        self.view.centerOn(self.scene.image_item)

    def savePoints(self, points):
        self.project.photos[self.photo_index].polygon = points
        self.project.save()


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    viewer = ImageViewer(sys.argv[1])
    viewer.show()
    viewer.resize(800, 600)
    sys.exit(app.exec_())