from os.path import join, dirname
from PyQt5.QtGui import QPixmap, QColor, QBrush, QPen, QFont
from PyQt5.QtCore import Qt, QRectF, QPointF, QTimer
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsScene,
    QGraphicsPixmapItem, QWidget, QVBoxLayout, QGraphicsRectItem,
    QGraphicsTextItem, QDesktopWidget, QInputDialog, QMessageBox)
from frontend.auxiliar_blackjack import (Visualizacion, AyudanteBlackjack)
import parametros


class MesaBlackJack(QMainWindow):

    # path de los recursos de blackjack
    assets_base = join(dirname(dirname(__file__)), "Assets", "Blackjack")

    def __init__(self, nombre_usuario, saldo, conexion):
        super().__init__()
        self.nombre_usuario = nombre_usuario
        self.conexion = conexion # instancia de conexion cliente
        self.saldo = saldo
        self.apuesta_actual = 0
        self.es_mi_turno = False
        self.estado_juego = "esperando"

        self.mapeo_usuarios = {
            self.nombre_usuario: "jugador1",
            "dealer": "dealer"
        }
        self.etiquetas_nombres = {}
        self.geometria_etiquetas = {}
        self.botones = {}
        self.siguiente_cupo = 2
        self.indices_cartas = {
            "jugador1": 0,
            "jugador2": 0,
            "jugador3": 0,
            "jugador4": 0,
            "dealer": 0,
        }

        self.cartas_por_jugador = {}
        self._centrar_en_pantalla()
        self._inicializa_gui()
        self.setGeometry(0, 0, 1280, 720)
        self.setMinimumSize(800, 450)

        self.setWindowTitle(f"BLACKJACK - {self.nombre_usuario.upper()} - "
                            f"ESPERANDO APUESTAS")

    def _inicializa_gui(self):
        self.setWindowTitle("BLACKJACK")
        self._objetos_graficos()

        # Creación de widgets:
        self.ayudante = AyudanteBlackjack(self.mesa, self.assets_base)
        self.ayudante.generar_widgets_mesa(self)

        self._actualizar_posicion_texto_apuesta()

        # Objeto Widget Central -> necesario en QMainWindow
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.visualizacion)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(central_widget)

        self._conectar_senales_extra()

    def _conectar_senales_extra(self):
        self.conexion.logica_cliente.senal_apuesta_cancelada.connect(
            self.procesar_apuesta_cancelada)
        self.conexion.logica_cliente.senal_cambio_turno_blackjack.connect(
            self.actualizar_turno)
        self.conexion.logica_cliente.senal_aviso_turno_dealer.connect(
            self.mostrar_aviso_dealer)
        self.conexion.logica_cliente.senal_actualizar_saldo.connect(
            self.actualizar_saldo)
        self.conexion.logica_cliente.senal_bancarrota.connect(
            self.manejar_bancarrota)

    def _objetos_graficos(self):
        # proporcion 16:9
        self.mesa_ancho = 1600
        self.mesa_alto = 900

        # objeto gráfico virtual
        self.mesa = QGraphicsScene(0, 0, self.mesa_ancho, self.mesa_alto)
        self.mesa.setBackgroundBrush(QColor(0, 100, 0))

        # visualizar la mesa
        self.visualizacion = Visualizacion(self.mesa, self)

    def _centrar_en_pantalla(self):
        marco = self.frameGeometry()
        centro = QDesktopWidget().availableGeometry().center()
        marco.moveCenter(centro)
        self.move(marco.topLeft())

    def showEvent(self, event):
        super().showEvent(event)
        self.visualizacion.maximizar_en_ventana()

    def closeEvent(self, event):
        self.conexion.enviar_instruccion({
            "comando": "salir_blackjack"
        })
        event.accept()

    def boton_clickeado_mesa(self, nombre_boton):
        # Gestion el click a los botones
        if nombre_boton in ("PEDIR", "PLANTARSE") and not self.es_mi_turno:
            return

        if nombre_boton == "PEDIR":
            print("[GUI] Solicitando carta...")
            self.conexion.enviar_instruccion({
                "comando": "accion_blackjack",
                "tipo": "pedir"
            })
        elif nombre_boton == "PLANTARSE":
            print("[GUI] Plantandose...")
            self.estado_juego = "plantado"
            self.conexion.enviar_instruccion({
                "comando": "accion_blackjack",
                "tipo": "plantarse"
            })
            self.ayudante.mostrar_mensaje_superior(
                "Te has plantado.\nEsperando al resto...", self.mesa_ancho,
            self.mesa_alto)
        elif nombre_boton == "APOSTAR":
            if self.apuesta_actual > 0:
                QMessageBox.warning(self, "Error", "Ya has apostado. "
                                                   "Cancela para cambiar.")
                return
            monto, ok = QInputDialog.getInt(self, "HACER APUESTA",
                                            "INGRESE SU APUESTA",
                                            min = parametros.
                                            APUESTA_MINIMA_BLACKJACK)
            if ok:
                print(f"[GUI] Solicitando apuesta de ${monto}...")
                self.conexion.enviar_instruccion({
                    "comando": "apostar_blackjack",
                    "monto": monto
                })
        elif nombre_boton == "VOLVER":
            print("[GUI] Volviendo al menu principal...")
            self.conexion.enviar_instruccion({"comando": "salir_blackjack"})
            self.conexion.logica_cliente.senal_volver_principal.emit()
            self.close()
        elif nombre_boton == "SALIR":
            self.close()
            QApplication.quit()
        elif nombre_boton == "CANCELAR":
            if self.apuesta_actual > 0:
                print("[GUI] Cancelando apuesta blackjack...")
                self.conexion.enviar_instruccion({
                    "comando": "cancelar_apuesta_blackjack"
                })
            else:
                QMessageBox.warning(self, "Error", "No tienes apuesta "
                                                   "para cancelar.")

    def recibir_carta(self, data):
        if "EN JUEGO" not in self.windowTitle():
            self.setWindowTitle("BLACKJACK - EN JUEGO")
        usuario_servidor = data["quien"]
        pinta = data["pinta"]
        valor = data["valor"]
        oculta = data.get("oculta", False)

        if usuario_servidor == self.nombre_usuario:
            oculta = False
        if usuario_servidor not in self.mapeo_usuarios:
            # Si es un jugador nuevo, asignarle un puesto disponible 2, 3, 4
            if self.siguiente_cupo <= 4:
                puesto = f"jugador{self.siguiente_cupo}"
                self.mapeo_usuarios[usuario_servidor] = puesto
                self.siguiente_cupo += 1
                if puesto in self.etiquetas_nombres:
                    self._actualizar_texto_etiqueta(puesto, usuario_servidor)
            else:
                return

        puesto_visual = self.mapeo_usuarios[usuario_servidor]
        if puesto_visual == "jugador1":
            if "jugador1" in self.etiquetas_nombres:
                self._actualizar_texto_etiqueta("jugador1",
                                                self.nombre_usuario)

        indice = self.indices_cartas[puesto_visual]
        rect_placeholder = self.cartas_por_jugador[puesto_visual][indice]
        pinta_final = ""
        if oculta:
            pinta_final = "back"
        else:
            pinta_final = pinta
        self.ayudante.mostrar_carta(puesto_visual, indice, pinta_final,
                                    valor, rect_placeholder)
        self.indices_cartas[puesto_visual] += 1

    def _actualizar_apuesta(self, monto):
        self.apuesta_actual = monto
        saldo_visual = self.saldo
        texto = f"APUESTA = ${monto}\nSALDO = ${saldo_visual}"
        self.mostrar_apuesta.setPlainText(texto)
        self._actualizar_posicion_texto_apuesta()

    def _actualizar_posicion_texto_apuesta(self):
        rect = self.mostrar_apuesta.boundingRect()
        texto_x = self.apuesta_texto_centro_x - (rect.width() / 2)
        texto_y = self.apuesta_texto_centro_y - (rect.height() / 2)
        self.mostrar_apuesta.setPos(texto_x, texto_y)

    def revelar_carta_dealer(self, data):
        # data = {pinta, valor}
        self.ayudante.ocultar_mensaje_superior()
        pinta = data["pinta"]
        valor = data["valor"]
        self.indices_cartas["dealer"] -= 1
        rect_placeholder = self.cartas_por_jugador["dealer"][1]
        self.ayudante.revelar_dealer(pinta, valor, rect_placeholder)
        self.indices_cartas["dealer"] += 1

    def jugador_perdio(self, data):
        nombre = data["nombre"]
        print(f"[GUI] El usuario {nombre} excedió 21.")
        if nombre == self.nombre_usuario:
            self.estado_juego = "perdio"
            self.ayudante.mostrar_mensaje_superior("¡Te pasaste de 21!\n"
                                          "Esperando al resto...",
                                                   self.mesa_ancho,
                                                   self.mesa_alto)

    def limpiar_mesa(self):
        self.ayudante.limpiar_mesa()
        for jugador in self.indices_cartas:
            self.indices_cartas[jugador] = 0
        self.mostrar_apuesta.setPlainText("APUESTA = $0")
        self._actualizar_posicion_texto_apuesta()

    def terminar_ronda(self, data):
        resultados = data["resultados"]
        puntaje_dealer = data.get("puntaje_dealer", "?")

        texto = f"Fin de Ronda!\nDealer: {puntaje_dealer}\n"
        for r in resultados:
            if r['nombre_usuario'] == self.nombre_usuario:
                ganancia = r['ganancia']
                puntaje_propio = r.get('puntaje', 0)
                texto += f"Tu puntaje: {puntaje_propio} pts\n"
                if ganancia > 0:
                    texto += f"GANASTE ${ganancia}!"
                elif ganancia < 0:
                    texto += f"PERDISTE ${abs(ganancia)}"
                else:
                    texto += f"EMPATE (Recuperas ${self.apuesta_actual})"

        self.ayudante.mostrar_mensaje_superior(texto, self.mesa_ancho,
                                               self.mesa_alto)

        QTimer.singleShot(6000, self.fase_resetear_tablero)

    def fase_resetear_tablero(self):
        self.limpiar_mesa()
        self.apuesta_actual = 0
        self._actualizar_apuesta(0)
        self.estado_juego = "esperando"
        self.setWindowTitle(f"BLACKJACK - {self.nombre_usuario.upper()} - "
                            f"ESPERANDO APUESTAS")
        self.ayudante.mostrar_mensaje_superior(
            "¡Nueva Ronda!\nEsperando apuestas...", self.mesa_ancho,
            self.mesa_alto)
        QTimer.singleShot(2000, self.ayudante.ocultar_mensaje_superior)

    def actualizar_saldo(self, nuevo_saldo):
        self.saldo = nuevo_saldo
        self._actualizar_apuesta(self.apuesta_actual)

    def procesar_apuesta_aceptada(self, monto, nuevo_saldo):
        self.saldo = nuevo_saldo
        self._actualizar_apuesta(monto)
        print(f"[GUI] Apuesta confirmada. Saldo: {self.saldo}")

    def procesar_apuesta_rechazada(self, motivo):
        QMessageBox.warning(self, "Apuesta Rechazada",
                            f"No se pudo realizar la apuesta.\nMotivo: {motivo}")

    def _actualizar_texto_etiqueta(self, llave, nuevo_texto):
        if (llave not in self.etiquetas_nombres or llave not in
                self.geometria_etiquetas):
            return
        item = self.etiquetas_nombres[llave]
        x, y, ancho, alto = self.geometria_etiquetas[llave]
        item.setPlainText(nuevo_texto)
        texto_rect = item.boundingRect()

        centro_x = x + ancho / 2
        centro_y = y + alto / 2

        item.setTransformOriginPoint(texto_rect.width() / 2,
                                     texto_rect.height() / 2)

        item.setPos(centro_x - texto_rect.width() / 2,
                    centro_y - texto_rect.height() / 2)

    def actualizar_turno(self, nombre_turno):
        self.es_mi_turno = (nombre_turno == self.nombre_usuario)
        if self.es_mi_turno:
            self.ayudante.ocultar_mensaje_superior()
            self.setWindowTitle(f"BLACKJACK - "
                                f"{self.nombre_usuario.upper()} - "
                                f"TU TURNO")
            print("[GUI] Es mi turno. Overlay oculto.")
        else:
            mensaje = f"Turno de {nombre_turno}."
            if self.estado_juego == "plantado":
                mensaje += "\nTe has plantado. Esperando resultados..."
            elif self.estado_juego == "perdio":
                mensaje += "\nTe pasaste de 21. Esperando resultados..."
            else:
                mensaje += "\nEsperando tu turno..."
            self.ayudante.mostrar_mensaje_superior(mensaje, self.mesa_ancho,
                                                   self.mesa_alto)
            self.setWindowTitle(f"BLACKJACK - "
                                f"{self.nombre_usuario.upper()} - "
                                f"ESPERANDO")

    def procesar_apuesta_cancelada(self, nuevo_saldo):
        self.saldo = nuevo_saldo
        self.apuesta_actual = 0
        self._actualizar_apuesta(0)
        self.setWindowTitle("BLACKJACK - APUESTA CANCELADA")
        print(f"[GUI] Apuesta cancelada. Saldo recuperado: {self.saldo}")

    def mostrar_aviso_dealer(self):
        self.ayudante.mostrar_mensaje_superior(
            "¡Todos jugaron!\nTurno del Dealer...", self.mesa_ancho,
            self.mesa_alto)

    def manejar_bancarrota(self):
        if self.isVisible():
            QMessageBox.warning(self, "Saldo Insuficiente",
                                "Te has quedado sin dinero suficiente "
                                "para seguir jugando.\n"
                                "Volviendo al menú principal.")
            self.close()