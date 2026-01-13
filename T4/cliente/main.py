import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from backend.conexion import ConexionCliente
from backend.logica_cliente import LogicaCliente
from frontend.ventanas_e_p import VEntrada
from frontend.v_blackjack import MesaBlackJack
from frontend.v_aviator import MesaAviator


class ControladorVentanas:

    # Gestiona las instancias de ventanas de juego, y conecta señales
    def __init__(self, logica, conexion):
        self.logica = logica
        self.conexion = conexion
        self.ventana_actual = None

    def iniciar_blackjack(self):
        nombre = self.logica.nombre_usuario
        saldo = self.logica.saldo
        self.ventana_actual = MesaBlackJack(nombre, saldo, self.conexion)
        # Nombres de señales son auto explicativos
        self.logica.senal_dibujar_carta.connect(
            self.ventana_actual.recibir_carta)
        self.logica.senal_revelar_dealer.connect(
            self.ventana_actual.revelar_carta_dealer)
        self.logica.senal_fin_ronda_blackjack.connect(
            self.ventana_actual.terminar_ronda)
        self.logica.senal_jugador_perdio.connect(
            self.ventana_actual.jugador_perdio)
        self.logica.senal_actualizar_saldo.connect(
            self.ventana_actual.actualizar_saldo)
        self.logica.senal_apuesta_aceptada.connect(
            self.ventana_actual.procesar_apuesta_aceptada)
        self.logica.senal_apuesta_rechazada.connect(
            self.ventana_actual.procesar_apuesta_rechazada)
        self.logica.senal_cambio_turno_blackjack.connect(
            self.ventana_actual.actualizar_turno)

        self.ventana_actual.show()

    def iniciar_aviator(self):
        nombre = self.logica.nombre_usuario
        saldo = self.logica.saldo
        self.ventana_actual = MesaAviator(nombre, saldo, self.conexion)

        self.logica.senal_aviator_inicio.connect(
            self.ventana_actual.recibir_inicio)
        self.logica.senal_aviator_avanza.connect(
            self.ventana_actual.recibir_avanza)
        self.logica.senal_aviator_crash.connect(
            self.ventana_actual.recibir_crash)
        self.logica.senal_aviator_nueva_partida.connect(
            self.ventana_actual.recibir_nueva_partida)

        self.logica.senal_apuesta_aceptada.connect(
            self.ventana_actual.procesar_apuesta_aceptada)
        self.logica.senal_apuesta_rechazada.connect(
            self.ventana_actual.procesar_apuesta_rechazada)
        self.logica.senal_retiro_aviator_exitoso.connect(
            self.ventana_actual.procesar_retiro_exitoso)
        self.logica.senal_aviator_retiro.connect(
            self.ventana_actual.actualizar_retiro_otro_jugador)

        self.ventana_actual.show()


def cierre_forzado_cliente(motivo):
    QMessageBox.critical(None, "Desconexión fatal",
                         f"Error: {motivo}")
    sys.exit() # Método para imprimir mensaje de desconexión en pantalla


if __name__ == "__main__":

    def hook(type, value, traceback) -> None:
        print(type)
        print(traceback)
    sys.__excepthook__ = hook
    app = QApplication([])

    logica_cliente = LogicaCliente()
    conexion = ConexionCliente(logica_cliente)
    conexion.senal_desconexion.connect(cierre_forzado_cliente)

    conectado, mensaje_status = conexion.conexion_server()
    if not conectado:
        QMessageBox.critical(None, "Error de conexión", mensaje_status)
        sys.exit(1)

    controlador = ControladorVentanas(logica_cliente, conexion)
    ve = VEntrada(conexion, logica_cliente)

    logica_cliente.senal_terminar_app.connect(
        cierre_forzado_cliente)
    logica_cliente.senal_abrir_blackjack.connect(
        controlador.iniciar_blackjack)
    logica_cliente.senal_ingreso_aviator_exitoso.connect(
        controlador.iniciar_aviator)

    ve.show()
    app_exec = app.exec() # Cerrar conexión correctamente:
    print("[MAIN] Cerrando conexión y liberando recursos...")
    conexion.cerrar()
    sys.exit(app_exec)