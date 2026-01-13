from os.path import join
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGraphicsView, QGraphicsScene, QLineEdit,
    QGraphicsTextItem, QGraphicsPixmapItem, QGraphicsPathItem)
from PyQt5.QtGui import (
    QPainter, QColor, QFont, QPen, QPainterPath, QPixmap)
from PyQt5.QtCore import Qt
import parametros


class WidgetJugador(QFrame):


    def __init__(self, nombre, apuesta, retiro, ganancia):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(
            "background-color: white; border: 1px solid black; "
            "border-radius: 5px;")
        self.setFixedHeight(50)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        fuente = QFont("Arial", 10)

        self.label_nombre = QLabel(nombre)
        self.label_nombre.setFont(fuente)

        self.label_apuesta = QLabel(f"${apuesta}")
        self.label_apuesta.setFont(fuente)

        self.label_retiro = QLabel(retiro)
        self.label_retiro.setFont(fuente)

        self.label_ganancia = QLabel(ganancia)
        self.label_ganancia.setFont(fuente)

        layout.addWidget(self.label_nombre, 2)
        layout.addWidget(self.label_apuesta, 1)
        layout.addWidget(self.label_retiro, 1)
        layout.addWidget(self.label_ganancia, 1)

    def actualizar(self, apuesta, retiro, ganancia):
        self.label_apuesta.setText(f"${apuesta}")
        self.label_retiro.setText(retiro)
        self.label_ganancia.setText(ganancia)


class AyudanteAviator:


    def __init__(self, assets_base):
        self.assets_base = assets_base
        self.items_jugadores = {}

    def inicializar_escena(self):
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setStyleSheet("background-color: #1a1a1a; "
                                "border: 2px solid black;")
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.texto_centro = QGraphicsTextItem("Periodo de Apuestas")
        self.texto_centro.setDefaultTextColor(Qt.white)
        self.texto_centro.setFont(QFont("Arial", 24, QFont.Bold))
        self.texto_centro.setZValue(10)
        self.scene.addItem(self.texto_centro)

        self.path_curva = QPainterPath()
        self.path_item = QGraphicsPathItem()
        pen = QPen(QColor("#ff4d4d"), 3)
        self.path_item.setPen(pen)
        self.scene.addItem(self.path_item)

        self.pix_avion = QGraphicsPixmapItem()
        self.pix_avion.setZValue(5)
        self.scene.addItem(self.pix_avion)

        return self.view

    def cargar_assets(self):
        path = join(self.assets_base, "logo-aviator.png")
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self.pix_avion.setPixmap(
                pixmap.scaled(50, 50, Qt.KeepAspectRatio,
                              Qt.SmoothTransformation))
            self.resetear_avion_posicion()
        else:
            print(f"[GUI] No se encontró avion.png en {path}")

    def resetear_avion_posicion(self):
        alto = self.scene.height()
        if alto < 100:
            alto = 400
        self.pix_avion.setPos(0, alto - 50)
        self.path_curva = QPainterPath()
        self.path_curva.moveTo(0, alto)
        self.path_item.setPath(self.path_curva)

    def centrar_texto(self):
        rect_view = self.scene.sceneRect()
        rect_txt = self.texto_centro.boundingRect()
        x = (rect_view.width() - rect_txt.width()) / 2
        y = (rect_view.height() - rect_txt.height()) / 2
        self.texto_centro.setPos(x, y)

    def actualizar_tamano_escena(self, width, height):
        self.scene.setSceneRect(0, 0, width, height)
        self.centrar_texto()

    def iniciar_animacion(self):
        self.texto_centro.setPlainText("¡Despegando!")
        self.centrar_texto()
        self.path_curva = QPainterPath()
        self.path_curva.moveTo(0, self.scene.height())
        self.path_item.setPath(self.path_curva)

    def dibujar_curva(self, tiempo, mult):
        self.texto_centro.setPlainText(f"{mult:.2f}x")
        self.centrar_texto()

        ancho = self.scene.width()
        alto = self.scene.height()
        escala_x = ancho / 15.0
        x = tiempo * escala_x
        y_pos = (mult - 1) * 20
        y = alto - y_pos - 50

        if x > ancho - 50:
            x = ancho - 50
        if y < 20:
            y = 20

        if self.path_curva.elementCount() == 0:
            self.path_curva.moveTo(0, alto)

        self.path_curva.lineTo(x, y + 25)
        self.path_item.setPath(self.path_curva)
        self.pix_avion.setPos(x - 40, y)

    def mostrar_crash(self, mensaje):
        self.texto_centro.setPlainText(mensaje)
        self.texto_centro.setDefaultTextColor(QColor("#ff4d4d"))
        self.centrar_texto()

    def resetear_vista_nueva_partida(self):
        self.texto_centro.setDefaultTextColor(Qt.white)
        self.texto_centro.setPlainText("Periodo de Apuestas")
        self.resetear_avion_posicion()
        self.centrar_texto()

    def agregar_o_actualizar_jugador(self, layout_jugadores, nombre,
                                     apuesta, retiro, ganancia):
        if nombre in self.items_jugadores:
            item = self.items_jugadores[nombre]
            item.actualizar(apuesta, retiro, ganancia)
        else:
            item = WidgetJugador(nombre, apuesta, retiro, ganancia)
            layout_jugadores.addWidget(item)
            self.items_jugadores[nombre] = item

    def limpiar_lista_jugadores(self):
        for nombre, widget in self.items_jugadores.items():
            widget.deleteLater()
        self.items_jugadores.clear()

    def eliminar_jugador_lista(self, nombre):
        if nombre in self.items_jugadores:
            widget = self.items_jugadores[nombre]
            widget.deleteLater()
            del self.items_jugadores[nombre]

    def resetear_lista_jugadores(self):
        for nombre, widget in self.items_jugadores.items():
            widget.actualizar("0", "", "")

    def configurar_interfaz(self, controlador):
        controlador.panel_izq = QFrame()
        controlador.panel_izq.setFixedWidth(280)
        controlador.panel_izq.setStyleSheet("background-color: #f0f0f0;")
        controlador.header_jugadores = QFrame()
        controlador.header_jugadores.setStyleSheet(
            "background-color: #e0e0e0; border: 1px solid black; "
            "border-radius: 5px;")
        controlador.header_jugadores.setFixedHeight(40)

        h_layout = QHBoxLayout(controlador.header_jugadores)
        h_layout.setContentsMargins(2, 2, 2, 2)
        h_layout.setSpacing(2)
        h_layout.addWidget(QLabel("Jugador"), 2)
        h_layout.addWidget(QLabel("Apuesta"), 1)
        h_layout.addWidget(QLabel("Retiro"), 1)
        h_layout.addWidget(QLabel("Ganancia"), 1)

        controlador.scroll_area = QScrollArea()
        controlador.scroll_area.setWidgetResizable(True)
        controlador.scroll_area.setStyleSheet("border: none; "
                                              "background-color: "
                                              "transparent;")

        controlador.contenedor_jugadores = QWidget()
        controlador.contenedor_jugadores.setStyleSheet("background-color: "
                                                       "transparent;")
        controlador.layout_jugadores = QVBoxLayout(controlador.
                                                   contenedor_jugadores)
        controlador.layout_jugadores.setAlignment(Qt.AlignTop)
        controlador.layout_jugadores.setSpacing(5)
        controlador.layout_jugadores.setContentsMargins(0, 0, 0, 0)
        controlador.scroll_area.setWidget(controlador.contenedor_jugadores)

        controlador.label_estado_ronda = QLabel("Periodo de Apuestas")
        controlador.label_estado_ronda.setAlignment(Qt.AlignCenter)
        controlador.label_estado_ronda.setMinimumHeight(40)
        controlador.label_estado_ronda.setStyleSheet(
            "border: 2px solid gray; "
            "padding: 5px; font-weight: bold; color: white; "
            "background-color: #333;")

        controlador.boton_volver = QPushButton("Volver a la ventana principal")
        controlador.boton_volver.clicked.connect(controlador.volver_menu)

        controlador.panel_der = QWidget()

        controlador.view = self.inicializar_escena()

        controlador.borde_apuestas = QFrame()
        controlador.borde_apuestas.setFrameShape(QFrame.StyledPanel)
        controlador.borde_apuestas.setStyleSheet(
            "background-color: #eee; border: 1px solid gray;")

        controlador.label_saldo = QLabel(f"Saldo: ${controlador.saldo}")
        controlador.label_saldo.setFont(QFont("Arial", 14, QFont.Bold))
        controlador.label_monto_texto = QLabel("Monto:")
        controlador.input_apuesta = QLineEdit()
        controlador.input_apuesta.setPlaceholderText(
            f"Min ${parametros.APUESTA_MINIMA_AVIATOR}")

        controlador.boton_accion = QPushButton("Apostar")
        controlador.boton_accion.setFixedSize(200, 60)
        controlador.boton_accion.setStyleSheet(
            "background-color: #28a745; color: white; "
            "font-size: 18px; font-weight: bold; border-radius: 10px;")
        controlador.boton_accion.clicked.connect(controlador.accion_boton)

        central_widget = QWidget()
        controlador.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        v_izq = QVBoxLayout(controlador.panel_izq)
        v_izq.addWidget(QLabel("Barra de Jugadores"))
        v_izq.addWidget(controlador.header_jugadores)
        v_izq.addWidget(controlador.scroll_area)
        v_izq.addWidget(controlador.label_estado_ronda)
        v_izq.addWidget(controlador.boton_volver)

        layout_der = QVBoxLayout(controlador.panel_der)
        layout_der.addWidget(controlador.view, stretch = 3)
        layout_apuestas = QHBoxLayout(controlador.borde_apuestas)

        layout_input = QVBoxLayout()
        hbox_input = QHBoxLayout()
        hbox_input.addWidget(controlador.label_monto_texto)
        hbox_input.addWidget(controlador.input_apuesta)
        layout_input.addWidget(controlador.label_saldo)
        layout_input.addLayout(hbox_input)

        layout_apuestas.addLayout(layout_input)
        layout_apuestas.addWidget(controlador.boton_accion)

        layout_der.addWidget(controlador.borde_apuestas, stretch=1)

        main_layout.addWidget(controlador.panel_izq)
        main_layout.addWidget(controlador.panel_der)
