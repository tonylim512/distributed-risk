import QtQuick 1.1

Item {
        signal reload();
        signal click(int x, int y);
        signal addCountry(int country, int x, int y);
        signal setCountryColor(int x, int y, color color);
        signal setCountryArmy(int x, int y, int army);
        signal addAttack(int attacker, int defender, color color);
        signal showAttack(int attacker, int defender, color color);
        signal hideAttack(int attacker, int defender);

        id: root;
        implicitWidth: map.status == Image.Ready ? map.implicitWidth : undefined;
        implicitHeight: map.status == Image.Ready ? map.implicitHeight : undefined;

        Component {
                id: circleComponent;
                Rectangle {
                        signal setColor(color c);
                        signal setText(string s);

                        onSetColor: {
                                color = c;
                        }

                        onSetText: {
                                text.text = s;
                        }

                        width: 18;
                        height: width;
                        radius: width / 2;

                        Text {
                                id: text;
                                anchors.centerIn: parent;
                                color: "white";
                        }
                }
        }

        Component {
                id: attackComponent;
                Image {
                        property int attacker;
                        property int defender;
                        property color color;

                        signal showAttack(int a, int d, color c);
                        signal hideAttack(int a, int d);

                        onShowAttack: {
                                if (a == attacker && d == defender) {
                                        visible = true;
                                        color = c;
                                }
                        }

                        onHideAttack: {
                                if (a == attacker && d == defender) {
                                        visible = false;
                                }
                        }

                        anchors.fill: parent;
                        asynchronous: false;
                        cache: true;
                        fillMode: Image.PreserveAspectFit;
                        smooth: true;
                        source: "image://map/attack " + attacker + " " + defender + " " + color;

                        Component.onCompleted: {
                                root.showAttack.connect(showAttack);
                                root.hideAttack.connect(hideAttack);
                        }
                }
        }

        onReload: {
                var source = map.source;
                map.smooth = false;
                map.source = "image://map/background";
                map.source = source;
                map.smooth = true;
        }

        onAddCountry: {
                var circle = circleComponent.createObject(map);
                circle.x = x - circle.radius;
                circle.y = y - circle.radius;
        }

        onSetCountryColor: {
                var circle = map.childAt(x, y);
                if (circle.setColor)    circle.setColor(color);
        }

        onSetCountryArmy: {
                var circle = map.childAt(x, y);
                if (circle.setText)     circle.setText(army);
        }

        onAddAttack: {
                var attack = attackComponent.createObject(attacks,
                        {
                                "attacker": attacker,
                                "defender": defender,
                                "color": color
                        });
        }

        Image {
                id: map;
                width: sourceSize.width;
                height: sourceSize.height;
                scale: Math.min(parent.width / width, parent.height / height);
                anchors.centerIn: parent;
                asynchronous: false;
                cache: false;
                fillMode: Image.PreserveAspectFit;
                smooth: true;
                source: "image://map/background";

                Item {
                        id: attacks;
                        anchors.fill: parent;
                }

                MouseArea {
                        anchors.fill: parent;
                        enabled: true;
                        hoverEnabled: true;
                        onPositionChanged: {
                                map.source = "image://map/background " + mouse.x + " " + mouse.y;
                        }
                        onClicked: {
                                root.click(mouse.x, mouse.y);
                        }
                }
        }

}

