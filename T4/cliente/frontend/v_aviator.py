from os.path import join, dirname
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QMessageBox, QFrame, QScrollArea,
    QGraphicsView, QGraphicsScene, QGraphicsTextItem,
    QGraphicsPixmapItem, QGraphicsPathItem)
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QPainterPath, QPixmap
from PyQt5.QtCore import Qt
from frontend.auxiliar_aviator import AyudanteAviator
import parametros


class MesaAviator(QMainWindow):


    assets_base = join(dirname(dirname(__file__)), "Assets", "Aviator")

    def __init__(self, nombre_usuario, saldo, conexion):
        super().__init__()
        self.nombre_usuario = nombre_usuario
        self.saldo = saldo
        self.conexion = conexion
        self.conexion.logica_cliente.senal_aviator_actualizar_barra.connect(
            self.actualizar_barra_jugadores)
        self.conexion.logica_cliente.senal_aviator_nuevo_jugador.connect(
            self.jugador_entro)
        self.conexion.logica_cliente.senal_aviator_jugador_salio.connect(
            self.jugador_salio)
        self.conexion.logica_cliente.senal_apuesta_cancelada.connect(
            self.procesar_apuesta_cancelada)
        self.conexion.logica_cliente.senal_bancarrota.connect(
            self.manejar_bancarrota)
        self.conexion.logica_cliente.senal_aviator_kicked.connect(
            self.manejar_kick)

        self.apuesta_actual = 0
        self.en_juego = False  # True si el avion vuela
        self.estado_apuesta = "esperando"  # esperando, apostado, retirado
        self.multiplicador_actual = 1.0

        self.ayudante = AyudanteAviator(self.assets_base)

        self.setWindowTitle(f"AVIATOR - {self.nombre_usuario.upper()}")
        self.setGeometry(100, 100, 1000, 600)

        self._inicializa_gui()
        self.ayudante.cargar_assets()
        self.cargar_jugadores_iniciales()

    def cargar_jugadores_iniciales(self):
        lista = self.conexion.logica_cliente.cache_jugadores_aviator
        encontrado_yo = False

        for jugador in lista:
            nombre = jugador["nombre"]
            monto = jugador["apuesta"]
            estado_original = jugador["estado"]
            ganancia = jugador["ganancia"]

            if monto > 0:
                apuesta_str = str(monto)
                ganancia_str = f"${ganancia}"
            else:
                apuesta_str = "0"
                ganancia_str = ""

            estado_str = ""
            if estado_original == "apostado":
                estado_str = "Apostado"
            elif estado_original == "retirado":
                estado_str = "Retirado"
            elif estado_original == "perdio":
                estado_str = "Crash"

            self.agregar_o_actualizar_jugador(nombre, apuesta_str,
                                              estado_str, ganancia_str)

            if nombre == self.nombre_usuario:
                encontrado_yo = True
                if estado_original == "apostado":
                    self.estado_apuesta = "apostado"
                    self.apuesta_actual = monto

        if not encontrado_yo:
            self.agregar_o_actualizar_jugador(self.nombre_usuario,
                                              "0", "",
                                              "")

    def _inicializa_gui(self):
        self.ayudante.configurar_interfaz(self)
        self.ayudante.resetear_avion_posicion()
        self.recibir_nueva_partida()

    def resizeEvent(self, event):
        rect = self.view.viewport().rect()
        self.ayudante.actualizar_tamano_escena(rect.width(), rect.height())
        if not self.en_juego:
            self.ayudante.resetear_avion_posicion()
        super().resizeEvent(event)

    def recibir_inicio(self):
        self.ayudante.iniciar_animacion()
        self.label_estado_ronda.setText("Ronda en curso")
        self.en_juego = True

        # Actualizar boton si apostó
        if self.estado_apuesta == "apostado":
            self.boton_accion.setText("Retirar ($...)")
            self.boton_accion.setStyleSheet(
                "background-color: #ffc107; color: black; "
                "font-size: 18px; font-weight: bold; border-radius: 10px;")
            self.boton_accion.setEnabled(True)
        else:
            self.boton_accion.setText("Esperando fin de ronda...")
            self.boton_accion.setEnabled(False)  # Si no apostó, espera

    def recibir_avanza(self, mult, tiempo):
        self.en_juego = True
        if self.estado_apuesta == "esperando":
            self.boton_accion.setText("Esperando nueva ronda...")
            self.boton_accion.setEnabled(False)

        self.multiplicador_actual = mult
        self.ayudante.dibujar_curva(tiempo, mult)

        # Actualizar Timer
        self.label_estado_ronda.setStyleSheet(
            "border: 2px solid gray; padding: 5px; font-weight: bold; "
            "color: white; background-color: #333;")
        self.label_estado_ronda.setText(f"Tiempo: {tiempo:.1f}s")

        if self.estado_apuesta == "apostado":
            ganancia_potencial = int(self.apuesta_actual * mult)
            self.boton_accion.setText(f"Retirar (${ganancia_potencial})")

    def recibir_crash(self, final_mult, resultados):
        self.en_juego = False
        mensaje = f"CRASH\n{final_mult:.2f}x"
        texto_resultado = "\nNo apostaste en esta ronda."

        for r in resultados:
            if r['nombre_usuario'] == self.nombre_usuario:
                ganancia = r.get('ganancia', 0)
                if ganancia > 0:
                    texto_resultado = f"\nGANASTE ${ganancia}!"
                elif ganancia < 0:
                    texto_resultado = f"\nPERDISTE ${abs(ganancia)}"
                else:
                    if r.get('retirado'):
                        texto_resultado = "\nRetiraste sin ganancia."
                    else:
                        texto_resultado = ("\nNo obtuviste ganancia "
                                           "en esta ronda.")
                break

        self.ayudante.mostrar_crash(mensaje + texto_resultado)

        # Resetear boton
        self.boton_accion.setText("Esperando...")
        self.boton_accion.setStyleSheet(
            "background-color: gray; color: white; font-size: 18px; "
            "font-weight: bold; border-radius: 10px;")
        self.boton_accion.setEnabled(False)
        self.ayudante.limpiar_lista_jugadores()

        for r in resultados:
            if r['ganancia'] > 0:
                ganancia_texto = f"${r['ganancia']}"
            else:
                ganancia_texto = "$0"
            if r.get('retirado'):
                estado_texto = "Retirado"
            else:
                estado_texto = "Crash"

            self.agregar_o_actualizar_jugador(
                r['nombre_usuario'],
                str(r['apuesta']),
                estado_texto,
                ganancia_texto
            )

    def recibir_nueva_partida(self):
        self.en_juego = False
        self.estado_apuesta = "esperando"
        self.apuesta_actual = 0

        self.ayudante.resetear_vista_nueva_partida()
        self.ayudante.resetear_lista_jugadores()

        if self.nombre_usuario not in self.ayudante.items_jugadores:
            self.agregar_o_actualizar_jugador(self.nombre_usuario,
                                              "0", "",
                                              "")
        # Habilitar Apuesta
        self.boton_accion.setText("Apostar")
        self.boton_accion.setStyleSheet(
            "background-color: #28a745; color: white; font-size: 18px; "
            "font-weight: bold; border-radius: 10px;")
        self.boton_accion.setEnabled(True)

    def actualizar_saldo_gui(self, nuevo_saldo):
        self.saldo = nuevo_saldo
        self.label_saldo.setText(f"Saldo: ${self.saldo}")

    def accion_boton(self):
        if not self.en_juego: # Fase apuesta
            if self.estado_apuesta == "esperando":
                texto = self.input_apuesta.text()
                if not texto or not texto.isdigit():
                    QMessageBox.warning(self, "Error", "Ingrese "
                                                       "un monto válido.")
                    return
                monto = int(texto)
                if monto < parametros.APUESTA_MINIMA_AVIATOR:
                    QMessageBox.warning(self, "Error",
                                        f"Mínimo ${parametros.APUESTA_MINIMA_AVIATOR}")
                    return
                if monto > self.saldo:
                    QMessageBox.warning(self, "Error", "Saldo insuficiente")
                    return
                self.conexion.enviar_instruccion({
                    "comando": "apostar_aviator",
                    "monto": monto
                })
                self.apuesta_actual = monto
                self.boton_accion.setText("Enviando...")
                self.boton_accion.setEnabled(False)
            elif self.estado_apuesta == "apostado":
                print("[GUI] Cancelando apuesta...")
                (self.conexion.
                 enviar_instruccion({"comando": "cancelar_apuesta_aviator"}))
        else: # Fase vuelo
            if self.estado_apuesta == "apostado":
                print("[GUI] Solicitando retiro...")
                self.conexion.enviar_instruccion({
                    "comando": "retirar_aviator"
                })

    def procesar_apuesta_aceptada(self, monto, nuevo_saldo):
        self.saldo = nuevo_saldo
        self.actualizar_saldo_gui(nuevo_saldo)
        self.estado_apuesta = "apostado"
        self.boton_accion.setText(f"Cancelar (${monto})")
        self.boton_accion.setStyleSheet(
            "background-color: #dc3545; color: white; font-size: 18px; "
            "font-weight: bold;")
        self.boton_accion.setEnabled(True)
        self.agregar_o_actualizar_jugador(self.nombre_usuario, str(monto),
                                          "Listo", "")
        self.input_apuesta.clear()

    def procesar_apuesta_rechazada(self, motivo):
        QMessageBox.warning(self, "Apuesta Rechazada", motivo)
        self.boton_accion.setText("Apostar")
        self.boton_accion.setEnabled(True)

    def procesar_apuesta_cancelada(self, nuevo_saldo):
        self.saldo = nuevo_saldo
        self.actualizar_saldo_gui(nuevo_saldo)
        self.estado_apuesta = "esperando"
        self.apuesta_actual = 0
        self.boton_accion.setText("Apostar")
        self.boton_accion.setStyleSheet(
            "background-color: #28a745; color: white; font-size: 18px; "
            "font-weight: bold; border-radius: 10px;")
        self.boton_accion.setEnabled(True)
        self.agregar_o_actualizar_jugador(self.nombre_usuario, "0",
                                          "", "")

    def procesar_retiro_exitoso(self, ganancia, nuevo_saldo):
        self.saldo = nuevo_saldo
        self.label_saldo.setText(f"Saldo: ${self.saldo}")
        self.estado_apuesta = "retirado"

        self.boton_accion.setText(f"Ganaste ${ganancia}!")
        self.boton_accion.setStyleSheet("background-color: #28a745; "
                                        "border: 2px solid gold;")
        self.boton_accion.setEnabled(False)

        self.agregar_o_actualizar_jugador(
            self.nombre_usuario,
            str(self.apuesta_actual),
            "Retirado",
            f"${ganancia}"
        )

    def volver_menu(self):
        self.conexion.enviar_instruccion({"comando": "salir_aviator"})
        self.conexion.logica_cliente.senal_volver_principal.emit()
        self.close()

    def closeEvent(self, event):
        if self.conexion.conectado:
            self.conexion.enviar_instruccion({"comando": "salir_aviator"})
        event.accept()

    def agregar_o_actualizar_jugador(self, nombre, apuesta,
                                     retiro, ganancia):
        self.ayudante.agregar_o_actualizar_jugador(self.layout_jugadores,
                                                   nombre, apuesta, retiro,
                                                   ganancia)

    def actualizar_retiro_otro_jugador(self, data):
        self.agregar_o_actualizar_jugador(
            data['nombre'],
            "---",
            f"{data['multiplicador']:.2f}x",
            f"${data['monto']}"
        )

    def resetear_avion_posicion(self):
        self.ayudante.resetear_avion_posicion()

    def showEvent(self, event):
        super().showEvent(event)
        rect = self.view.viewport().rect()
        self.ayudante.actualizar_tamano_escena(rect.width(), rect.height())
        self.view.update()
        if not self.en_juego:
            self.ayudante.resetear_avion_posicion()

    def jugador_entro(self, data):
        nombre = data.get("nombre")
        self.agregar_o_actualizar_jugador(nombre, "0",
                                          "", "")

    def jugador_salio(self, data):
        nombre = data.get("nombre")
        self.ayudante.eliminar_jugador_lista(nombre)

    def actualizar_barra_jugadores(self, objeto_recibido):
        nombre = objeto_recibido.get("nombre", "")
        monto = objeto_recibido.get("monto", 0)
        cancelado = objeto_recibido.get("cancelado", False)
        if monto > 0:
            apuesta_str = str(monto)
            estado = "Apostado"
        else:
            apuesta_str = "0"
            estado = ""
        if cancelado:
            estado = "Cancelado"
            apuesta_str = "0"
        self.agregar_o_actualizar_jugador(nombre, apuesta_str,
                                          estado, "")

    def manejar_bancarrota(self):
        if self.isVisible():
            QMessageBox.warning(self, "Saldo Insuficiente",
                                "Te has quedado sin dinero suficiente "
                                "para seguir jugando.\n"
                                "Volviendo al menú principal.")
            self.close()

    def manejar_kick(self):
        if self.isVisible():
            QMessageBox.information(self, "Ronda Iniciada",
                                    "La ronda ha comenzado y no "
                                    "realizaste una apuesta.\n"
                                    "Has sido enviado al lobby.")
            self.conexion.logica_cliente.senal_volver_principal.emit()
            self.close()