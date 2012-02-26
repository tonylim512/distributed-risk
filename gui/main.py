#!/usr/bin/python
from collections import deque
import math, operator, random, sys, os

from PyQt4.QtCore import Qt, QByteArray, QFile, QPoint, QString, QTimer, QThread, QRegExp, QUrl
from PyQt4.QtGui import QApplication, QBrush, QColor, QImage, QPainter, QPen
from PyQt4.QtDeclarative import QDeclarativeEngine, QDeclarativeImageProvider, QDeclarativeView

neutralColor = QColor(Qt.gray).darker()

class GameMap():
        def __init__(self, mapName):
                self.mapName = mapName
                self._parseMap()
        
        def _isBorder(self, x, y):
                if x > 0 and self.country[y][x - 1] != self.country[y][x]:
                        return True
                if y > 0 and self.country[y - 1][x] != self.country[y][x]:
                        return True
                if x + 1 < self.width and self.country[y][x + 1] != self.country[y][x]:
                        return True
                if y + 1 < self.height and self.country[y + 1][x] != self.country[y][x]:
                        return True
                return False

        def _floodFill(self, filled, x, y):
                q = deque([(x, y)])
                updated = False
                while q:
                        x, y = q.popleft()
                        if (x, y) in filled:
                                continue
                        filled.add((x, y))
                        updated = True
                        if x > 0 and self.country[y][x - 1] == self.country[y][x]:
                                q.append((x - 1, y))
                        if y > 0 and self.country[y - 1][x] == self.country[y][x]:
                                q.append((x, y - 1))
                        if x + 1 < self.width and self.country[y][x + 1] == self.country[y][x]:
                                q.append((x + 1, y))
                        if y + 1 < self.height and self.country[y + 1][x] == self.country[y][x]:
                                q.append((x, y + 1))
                return updated

        def _parseMap(self):
                self._rawImage = QImage('maps' + os.path.sep + self.mapName + '.gif')
                self.country = [[0] * self._rawImage.width() for dummy in xrange(self._rawImage.height())] # [y][x] -> country
                self.border = [[False] * self._rawImage.width() for dummy in xrange(self._rawImage.height())] # [y][x] -> isBorder

                self.countries = 0
                for y in xrange(self.height):
                        for x in xrange(self.width):
                                country = 255 - QColor(self._rawImage.pixel(x, y)).black()
                                if country == 255:
                                        continue
                                if country > self.countries:
                                        self.countries = country
                                self.country[y][x] = country

                weight = [(0, 0, 0) for dummy in xrange(self.countries + 1)] # country -> (weightX, weightY)
                self.keyCoordinates = [[] for dummy in xrange(self.countries + 1)] # country -> [(x, y), ...]
                coordinates = [set() for dummy in xrange(self.countries + 1)]
                for y in xrange(self.height):
                        for x in xrange(self.width):
                                country = self.country[y][x]
                                if country == 0:
                                        continue
                                weight[country] = map(operator.add, weight[country], (1, x, y))
                                if self._floodFill(coordinates[country], x, y):
                                        self.keyCoordinates[country].append((x, y))
                                self.border[y][x] = self._isBorder(x, y)

                self.center = [() for dummy in xrange(self.countries + 1)] # country -> (x, y)
                for country in xrange(1, self.countries + 1):
                        self.center[country] = (weight[country][1] / weight[country][0], weight[country][2] / weight[country][0])

                self.color = {0 : neutralColor}
                self.owner = [0 for dummy in xrange(self.countries + 1)]

                self._parseConnection()

        def _parseConnection(self):
                mapFile = QFile('maps' + os.path.sep + self.mapName + '.map')
                mapFile.open(QFile.ReadOnly)
                self.connections = [[] for dummy in xrange(self.countries + 1)]
                while not mapFile.atEnd():
                        connection = QString(mapFile.readLine()).split(QRegExp(r'\D'), QString.SkipEmptyParts)
                        country = connection[0].toInt()[0]
                        for other in xrange(1, len(connection)):
                                self.connections[country].append(connection[other].toInt()[0])

        @property
        def width(self):
                return self._rawImage.width()

        @property
        def height(self):
                return self._rawImage.height()

        @property
        def size(self):
                return self._rawImage.size()

class MapImageProvider(QDeclarativeImageProvider):
        def __init__(self, mapFile):
                super(MapImageProvider, self).__init__(QDeclarativeImageProvider.Image)
                self.gameMap = GameMap(mapFile)
                self.baseImage = QImage(self.gameMap.size, QImage.Format_RGB32)
                for y in xrange(self.gameMap.height):
                        for x in xrange(self.gameMap.width):
                                if self.gameMap.country[y][x] == 0:
                                        self.baseImage.setPixel(x, y, QColor(Qt.white).rgb())
                for country in xrange(1, self.gameMap.countries + 1):
                        self.setCountryOwner(country, 0)
                self.attackImages = {}
                self._prepareAttackImage(self.gameMap.color[0])

        def _floodFill(self, image, x, y, color, lighterFactor):
                borderRgb = color.darker().rgb()
                innerRgb = color.lighter(lighterFactor).rgb()
                q = deque([(x, y)])
                filled = set()
                while q:
                        x, y = q.popleft()
                        if (x, y) in filled:
                                continue
                        filled.add((x, y))
                        rgb = borderRgb if self.gameMap.border[y][x] else innerRgb
                        image.setPixel(x, y, rgb)
                        if x > 0 and self.gameMap.country[y][x - 1] == self.gameMap.country[y][x]:
                                q.append((x - 1, y))
                        if y > 0 and self.gameMap.country[y - 1][x] == self.gameMap.country[y][x]:
                                q.append((x, y - 1))
                        if x + 1 < self.gameMap.width and self.gameMap.country[y][x + 1] == self.gameMap.country[y][x]:
                                q.append((x + 1, y))
                        if y + 1 < self.gameMap.height and self.gameMap.country[y + 1][x] == self.gameMap.country[y][x]:
                                q.append((x, y + 1))

        def _getOwner(self, x, y):
                return self.gameMap.owner[self.gameMap.country[y][x]]

        def _drawCountry(self, country, image, color, lighterFactor = 125):
                for (x, y) in self.gameMap.keyCoordinates[country]:
                        self._floodFill(image, x, y, color, lighterFactor)

        def _drawAttack(self, image, attacker, defender, color):
                painter = QPainter()
                painter.begin(image)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(QPen(Qt.SolidLine));
                painter.setBrush(QBrush(QColor(color)))
                x1, y1 = self.gameMap.center[attacker]
                x2, y2 = self.gameMap.center[defender]
                dx, dy = (x2 - x1, y2 - y1)
                l, r = math.sqrt(dx * dx + dy * dy), 8
                dx, dy = dy / l, -dx / l
                x11, y11 = x1 + dx * r, y1 + dy * r
                x12, y12 = x1 - dx * r, y1 - dy * r
                painter.drawConvexPolygon(QPoint(x11, y11), QPoint(x12, y12), QPoint(x2, y2))
                painter.end()

        def _prepareAttackImage(self, color):
                for attacker in xrange(1, self.gameMap.countries + 1):
                        for defender in self.gameMap.connections[attacker]:
                                image = QImage(self.gameMap.size, QImage.Format_ARGB32_Premultiplied)
                                self._drawAttack(image, attacker, defender, color)
                                self.attackImages[(attacker, defender, color.name())] = image

        def setPlayerColor(self, player, color):
                self.gameMap.color[player] = color
                self._prepareAttackImage(color)

        def setCountryOwner(self, country, player):
                self.gameMap.owner[country] = player
                self._drawCountry(country, self.baseImage, self.gameMap.color[player])

        def _requestBackground(self, id):
                if ' ' not in id:
                        return self.baseImage
                params = id.split(' ', QString.SkipEmptyParts)
                mouseX, mouseY = params[1].toInt()[0], params[2].toInt()[0]
                if self.gameMap.country[mouseY][mouseX] == 0:
                        return self.baseImage
                hoverImage = QImage(self.baseImage)
                self._drawCountry(self.gameMap.country[mouseY][mouseX], hoverImage, self.gameMap.color[self._getOwner(mouseX, mouseY)], 170)
                return hoverImage

        def _requestAttack(self, id):
                params = id.split(' ', QString.SkipEmptyParts)
                attacker, defender, color = params[1].toInt()[0], params[2].toInt()[0], params[3]
                return self.attackImages[(attacker, defender, color)]

        def requestImage(self, id, size, requestedSize):
                if size is not None:
                        size = self.gameMap.size
                if 'background' in id:
                        return self._requestBackground(id)
                elif 'attack' in id:
                        return self._requestAttack(id)

app = QApplication(sys.argv)
if len(app.arguments()) > 1:
    mapName = app.arguments()[1]
else:
    mapName = 'world'

view = QDeclarativeView()
provider = MapImageProvider(mapName)
view.engine().addImageProvider('map', provider)
view.setSource(QUrl('main.qml'))
view.setResizeMode(QDeclarativeView.SizeRootObjectToView)

root = view.rootObject()

for country in xrange(1, provider.gameMap.countries + 1):
        x, y = provider.gameMap.center[country]
        root.addCountry.emit(country, x, y)

provider.setPlayerColor(1, QColor(Qt.green))
provider.setPlayerColor(2, QColor(Qt.red))
provider.setPlayerColor(3, QColor(Qt.blue))
for country in xrange(1, provider.gameMap.countries + 1):
        player = random.randint(1, 3)
        color = provider.gameMap.color[player].darker()
        x, y = provider.gameMap.center[country]
        provider.setCountryOwner(country, player)
        root.setCountryColor.emit(x, y, color)
        root.setCountryArmy.emit(x, y, random.randint(1, 20))

timer = QTimer()
attacks = []
def randomArmy():
        country = random.randint(1, provider.gameMap.countries)
        x, y = provider.gameMap.center[country]
        root.setCountryArmy.emit(x, y, random.randint(1, 99))
def randomOwner():
        country = random.randint(1, provider.gameMap.countries)
        player = random.randint(0, 3)
        color = provider.gameMap.color[player].darker()
        x, y = provider.gameMap.center[country]
        provider.setCountryOwner(country, player)
        root.setCountryColor.emit(x, y, color)
        for (attacker, defender) in attacks:
                if attacker == country:
                        root.hideAttack.emit(attacker, defender)
def randomAttack():
        attacker = random.randint(1, provider.gameMap.countries)
        neighbors = provider.gameMap.connections[attacker]
        defender = neighbors[random.randint(0, len(neighbors) - 1)]
        color = provider.gameMap.color[provider.gameMap.owner[attacker]]
        if (attacker, defender) not in attacks:
                attacks.append((attacker, defender))
                root.addAttack.emit(attacker, defender, color)
        else:
                root.showAttack.emit(attacker, defender, color)
def randomTest():
        randomArmy()
        randomOwner()
        randomAttack()
        root.reload.emit()
                
timer.timeout.connect(randomTest)
timer.start(300)

view.show()
app.exec_()

