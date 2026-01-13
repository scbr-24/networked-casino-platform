from os.path import join
from PyQt5.QtWidgets import (QGraphicsView, QGraphicsRectItem,
    QGraphicsTextItem, QGraphicsSceneMouseEvent, QGraphicsPixmapItem)
from PyQt5.QtGui import (QColor, QPainter, QFont, QBrush, QPen, QPixmap)
from PyQt5.QtCore import Qt, QRectF, QPointF


class Visualizacion(QGraphicsView):

    # Visualizacion de la mesa es proporcional
    # Gestiona selección de cartas
    def __init__(self, mesa, parent=None):
        super().__init__(mesa, parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)

    def resizeEvent(self, event):
        self.maximizar_en_ventana()
        super().resizeEvent(event)

    def maximizar_en_ventana(self):
        # Maximiza la visualizacion de la mesa en la ventana
        if self.scene(): # self.scene = la mesa del juego
            self.fitInView(self.scene().sceneRect(), Qt.KeepAspectRatio)


class ObjetoRoundedRect(QGraphicsRectItem):


    def __init__(self, rect, radius=5):
        super().__init__(rect)
        self.radio = radius

    def paint(self, painter, option, widget):
        # Pinta objetos en la mesa;
        # Option y Widget necesarios para llamar al metodo pero no se usan.
        painter.setBrush(self.brush()) # Relleno
        painter.setPen(self.pen()) # Borde
        painter.drawRoundedRect(self.rect(), self.radio, self.radio)


class BotonClickeadoAuxiliar(ObjetoRoundedRect):


    def __init__(self, rect, radio = 5, nombre = ""):
        super().__init__(rect, radio)
        self.nombre = nombre
        self.controlador = None
        self._crear_etiquetas()

    def _crear_etiquetas(self):
        self.etiqueta = QGraphicsTextItem(self.nombre, self)
        self.etiqueta.setFont(QFont("Arial", 18, QFont.Bold))
        self.etiqueta.setDefaultTextColor(QColor(255, 255, 255))
        rectangulo_boton = self.rect()
        rectangulo_texto = self.etiqueta.boundingRect()
        texto_x = (rectangulo_boton.x() +
                   (rectangulo_boton.width() -
                    rectangulo_texto.width()) / 2)
        texto_y = (rectangulo_boton.y() +
                   (rectangulo_boton.height() -
                    rectangulo_texto.height()) / 2)
        self.etiqueta.setPos(texto_x, texto_y)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if self.controlador:
            self.controlador.boton_clickeado_mesa(self.nombre)
        event.accept()


class AyudanteBlackjack:

    # Clase auxiliar para manejar carga de assets, dibujado de cartas
    # y mensajes de overlay
    def __init__(self, mesa, assets_base):
        self.mesa = mesa
        self.assets_base = assets_base
        self.pixmap_cartas = {}
        self.cartas_cargadas = {}
        # Overlay:
        self.fondo_mensaje = QGraphicsRectItem(0, 0, 600, 200)
        self.fondo_mensaje.setBrush(QBrush(QColor(0, 0, 0, 200)))
        self.fondo_mensaje.setZValue(99)
        self.fondo_mensaje.setVisible(False)
        self.mesa.addItem(self.fondo_mensaje)
        self.mensaje_texto = QGraphicsTextItem("")
        self.mensaje_texto.setDefaultTextColor(Qt.white)
        self.mensaje_texto.setFont(QFont("Arial", 30, QFont.Bold))
        self.mensaje_texto.setZValue(100)
        self.mensaje_texto.setVisible(False)
        self.mesa.addItem(self.mensaje_texto)

        self._cargar_imagenes()

    def _cargar_imagenes(self):
        pintas = ["hearts", "spades", "diamonds", "clubs"]
        valores = [f"{n:02}" for n in range(2, 11)] + ["J", "Q", "K", "A"]
        for p in pintas:
            for v in valores:
                path = join(self.assets_base, f"card_{p}_{v}.png")
                self._guardar_imagen(path, f"{p}_{v}")

        for j in ["joker_red", "joker_black"]:
            path = join(self.assets_base, f"card_{j}.png")
            self._guardar_imagen(path, j)

        self._guardar_imagen(join(self.assets_base, "card_back.png"),
                             "back")

    def _guardar_imagen(self, path, llave):
        imagen = QPixmap(path)
        if not imagen.isNull():
            self.pixmap_cartas[llave] = imagen.scaled(
                100, 145, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            print(f"ERROR AL CARGAR RECURSO: {path}")

    def generar_widgets_mesa(self, controlador):
        carta_ancho = 100
        carta_alto = 145
        carta_espacio = 10

        # Fondo Gris
        barra_gris_alto = 150
        barra_y = controlador.mesa_alto - barra_gris_alto
        barra_gris = QGraphicsRectItem(0, barra_y,
                                       controlador.mesa_ancho,
                                       controlador.mesa_alto)
        barra_gris.setBrush(QColor(50, 50, 50))
        barra_gris.setPen(QPen(Qt.NoPen))
        barra_gris.setZValue(20)
        self.mesa.addItem(barra_gris)

        boton_ancho = 150
        boton_alto = 50
        espaciado = 20

        # Texto Apuesta
        controlador.mostrar_apuesta = QGraphicsTextItem(
            f"APUESTA = $0\nSALDO = ${controlador.saldo}")
        controlador.mostrar_apuesta.setDefaultTextColor(Qt.white)
        controlador.mostrar_apuesta.setFont(QFont("Arial", 20, QFont.Bold))
        controlador.mostrar_apuesta.setZValue(21)

        ancho_texto_reservado = 300
        total_ancho = ((boton_ancho * 5) + ancho_texto_reservado +
                       (espaciado * 5))
        barra_x = (controlador.mesa_ancho - total_ancho) / 2
        barra_centro_y = barra_y + barra_gris_alto / 2
        x_actual = barra_x

        # Botones
        for nombre in ["PEDIR", "PLANTARSE", "APOSTAR", "CANCELAR"]:
            self._crear_boton(nombre, x_actual, barra_centro_y,
                              boton_ancho, boton_alto, controlador)
            x_actual += boton_ancho + espaciado

        controlador.apuesta_texto_centro_x = (x_actual +
                                              (ancho_texto_reservado / 2))
        controlador.apuesta_texto_centro_y = barra_centro_y
        self.mesa.addItem(controlador.mostrar_apuesta)

        x_actual += ancho_texto_reservado + espaciado

        for nombre in ["VOLVER", "SALIR"]:
            self._crear_boton(nombre, x_actual, barra_centro_y,
                              boton_ancho, boton_alto, controlador)
            x_actual += boton_ancho + espaciado

        # Espacios Cartas
        ancho_mazo = (carta_ancho * 6) + (carta_espacio * 5)
        inicio_x = (controlador.mesa_ancho - ancho_mazo) / 2

        config_jugadores = [
            ("jugador1", "JUGADOR1", 630, True),
            ("jugador4", "JUGADOR4", 30, False),
            ("dealer", "DEALER", 260 + 50, False)]

        for llave, texto, y, etiqueta in config_jugadores:
            cartas = []
            if llave == "jugador1":
                etiqueta_y = y - 45
                carta_y = y
            else:
                if etiqueta:
                    etiqueta_y = y - 45
                    carta_y = y
                else:
                    etiqueta_y = y
                    carta_y = y + 50

            controlador.geometria_etiquetas[llave] = (inicio_x, etiqueta_y,
                                                      ancho_mazo, 40)
            etiqueta = self._crear_etiqueta_nombre(inicio_x, etiqueta_y,
                                                ancho_mazo, 40, texto)
            controlador.etiquetas_nombres[llave] = etiqueta

            for i in range(6):
                x = inicio_x + i * (carta_ancho + carta_espacio)
                cartas.append(self._crear_rect_carta(x, carta_y,
                                                     carta_ancho, carta_alto))
            controlador.cartas_por_jugador[llave] = cartas

        # Jugadores 2 y 3
        config_jugadores_2_3 = [
            ("jugador2", "JUGADOR2", 50, -90, "izquierda"),
            ("jugador3", "JUGADOR3", controlador.mesa_ancho - 50, 90,
             "derecha")]

        for llave, texto, x, rotacion, alineamiento in config_jugadores_2_3:
            cartas = []
            etiqueta_alto = (carta_alto * 3) + (espaciado * 2) - 20
            etiqueta_ancho = 40
            posicion_y = 150
            grilla_ancho = (carta_ancho * 2) + carta_espacio

            if alineamiento == "izquierda":
                etiqueta_x = x
                grilla_x = etiqueta_x + etiqueta_ancho + 20
            else:
                etiqueta_x = x - etiqueta_ancho
                grilla_x = etiqueta_x - 20 - grilla_ancho

            controlador.geometria_etiquetas[llave] = (
                etiqueta_x, posicion_y, etiqueta_ancho, etiqueta_alto)

            etiqueta = self._crear_etiqueta_nombre(etiqueta_x, posicion_y,
                                                etiqueta_ancho, etiqueta_alto,
                                                texto, rotacion)
            controlador.etiquetas_nombres[llave] = etiqueta

            for fila in range(3):
                for columna in range(2):
                    x = grilla_x + columna * (carta_ancho + carta_espacio)
                    y = posicion_y + fila * (carta_alto + carta_espacio)
                    cartas.append(self._crear_rect_carta(x, y, carta_ancho,
                                                         carta_alto))
            controlador.cartas_por_jugador[llave] = cartas

    def _crear_boton(self, nombre, x, centro_y, ancho, alto, controlador):
        y = centro_y - (alto / 2)
        boton = BotonClickeadoAuxiliar(QRectF(x, y, ancho, alto),
                                       radio=5, nombre=nombre)
        boton.controlador = controlador
        boton.setBrush(QBrush(QColor(100, 100, 100)))
        boton.setPen(QPen(QColor(150, 150, 150)))
        boton.setZValue(21)
        self.mesa.addItem(boton)
        controlador.botones[nombre] = boton

    def _crear_etiqueta_nombre(self, x, y, ancho, alto, texto, rotacion=0):
        etiqueta = QGraphicsRectItem(x, y, ancho, alto)
        etiqueta.setBrush(QColor(180, 0, 0))
        etiqueta.setPen(QPen(Qt.NoPen))
        etiqueta.setZValue(25)
        self.mesa.addItem(etiqueta)

        nombre = QGraphicsTextItem(texto)
        nombre.setDefaultTextColor(Qt.white)
        nombre.setFont(QFont("Arial", 16, QFont.Bold))
        nombre.setZValue(26)

        texto_rect = nombre.boundingRect()
        centro_etiqueta = QPointF(x + ancho / 2, y + alto / 2)
        nombre.setTransformOriginPoint(texto_rect.width() / 2,
                                       texto_rect.height() / 2)
        nombre.setRotation(rotacion)
        nombre.setPos(centro_etiqueta.x() - texto_rect.width() / 2,
                      centro_etiqueta.y() - texto_rect.height() / 2)
        self.mesa.addItem(nombre)
        return nombre

    def _crear_rect_carta(self, x, y, ancho, alto):
        carta = ObjetoRoundedRect(QRectF(x, y, ancho, alto), radius=5)
        carta.setBrush(QBrush(QColor(100, 100, 100, 100)))
        carta.setPen(QPen(QColor(150, 150, 150), 2))
        carta.setZValue(1)
        self.mesa.addItem(carta)
        return carta

    def mostrar_carta(self, llave_jugador, indice, pinta, valor,
                      rect_placeholder):
        llave = ""
        if pinta == "back":
            llave = "back"
        else:
            llave = f"{pinta}_{valor}"

        if llave not in self.pixmap_cartas:
            print(f"ERROR: Carta {llave} no encontrada")
            return

        imagen = self.pixmap_cartas[llave]
        rect = rect_placeholder.rect()
        dif_x = (rect.width() - imagen.width()) / 2
        dif_y = (rect.height() - imagen.height()) / 2

        item_pixmap = QGraphicsPixmapItem(imagen)
        item_pixmap.setPos(rect.x() + dif_x, rect.y() + dif_y)
        item_pixmap.setZValue(10 + indice)

        self.mesa.addItem(item_pixmap)

        if llave_jugador not in self.cartas_cargadas:
            self.cartas_cargadas[llave_jugador] = []
        self.cartas_cargadas[llave_jugador].append(item_pixmap)

    def revelar_dealer(self, pinta, valor, rect_placeholder):
        if "dealer" in self.cartas_cargadas:
            if len(self.cartas_cargadas["dealer"]) > 1:
                item_oculto = self.cartas_cargadas["dealer"][1]
                self.mesa.removeItem(item_oculto)
                self.cartas_cargadas["dealer"].pop(1)

        self.mostrar_carta("dealer", 1, pinta, valor,
                           rect_placeholder)

    def limpiar_mesa(self):
        for lista_cartas in self.cartas_cargadas.values():
            for item in lista_cartas:
                self.mesa.removeItem(item)
        self.cartas_cargadas.clear()
        self.ocultar_mensaje_superior()

    def mostrar_mensaje_superior(self, texto, ancho_mesa, alto_mesa):
        self.mensaje_texto.setPlainText(texto)
        centro_x = ancho_mesa / 2 - 300
        centro_y = alto_mesa / 2 - 100
        self.fondo_mensaje.setPos(centro_x, centro_y)

        rect_texto = self.mensaje_texto.boundingRect()
        texto_x = centro_x + (600 - rect_texto.width()) / 2
        texto_y = centro_y + (200 - rect_texto.height()) / 2
        self.mensaje_texto.setPos(texto_x, texto_y)

        self.fondo_mensaje.setVisible(True)
        self.mensaje_texto.setVisible(True)

    def ocultar_mensaje_superior(self):
        self.fondo_mensaje.setVisible(False)
        self.mensaje_texto.setVisible(False)
