from PyQt5.QtCore import QObject, pyqtSignal
import parametros


class LogicaCliente(QObject):

    # procesa comandos del servidor hacia el cliente
    senal_login_exitoso = pyqtSignal(str, int) # nombre_usuario, saldo
    senal_login_fallido = pyqtSignal(str) # motivo
    senal_terminar_app = pyqtSignal(str) # motivo
    senal_ingreso_fallido = pyqtSignal(str)
    senal_aviso_turno_dealer = pyqtSignal()
    senal_bancarrota = pyqtSignal()
    senal_actualizar_stats = pyqtSignal(list)
    senal_carga_exitosa = pyqtSignal(int)
    senal_carga_rechazada = pyqtSignal(str)

    senal_abrir_blackjack = pyqtSignal()
    senal_dibujar_carta = pyqtSignal(dict) # dict con info de carta
    senal_revelar_dealer = pyqtSignal(dict)
    senal_cambio_turno_blackjack = pyqtSignal(str)
    senal_fin_ronda_blackjack = pyqtSignal(dict)
    senal_jugador_perdio = pyqtSignal(dict)
    senal_apuesta_aceptada = pyqtSignal(int, int)
    senal_apuesta_rechazada = pyqtSignal(str)
    senal_actualizar_saldo = pyqtSignal(int)
    senal_volver_principal = pyqtSignal()

    senal_ingreso_aviator_exitoso = pyqtSignal()
    senal_aviator_inicio = pyqtSignal()  # periodo de apuestas
    senal_aviator_avanza = pyqtSignal(float, float)  # mult, tiempo
    senal_aviator_crash = pyqtSignal(float, list)  # final_mult, reslt
    senal_aviator_retiro = pyqtSignal(dict)  # {nombre, monto, multiplicador}
    senal_aviator_nueva_partida = pyqtSignal()  # resetear
    senal_aviator_actualizar_barra = pyqtSignal(dict)
    senal_apuesta_cancelada = pyqtSignal(int)  # nuevo_saldo
    senal_aviator_nuevo_jugador = pyqtSignal(dict)
    senal_aviator_jugador_salio = pyqtSignal(dict)
    senal_retiro_aviator_exitoso = pyqtSignal(int, int)
    senal_aviator_kicked = pyqtSignal()


    def __init__(self):
        super().__init__()
        self.nombre_usuario = None
        self.saldo = 0
        self.cache_jugadores_aviator = []

    def procesar_respuesta_servidor(self, objeto_recibido):
        # recibe dict decodificado desde conexion cliente
        comando = objeto_recibido.get("comando")

        if comando == "login_exitoso":
            self.nombre_usuario = objeto_recibido.get("nombre_usuario")
            self.saldo = objeto_recibido.get("saldo")
            print(f"[CLIENTE] Login Exitoso. Saldo: {self.saldo}")
            self.senal_login_exitoso.emit(self.nombre_usuario, self.saldo)

        elif comando == "login_fallido":
            motivo = objeto_recibido.get("motivo", "Motivo desconocido.")
            print(f"[CLIENTE] Login Fallido: {motivo}")
            self.senal_login_fallido.emit(motivo)

        elif comando == "desconexion_servidor":
            motivo = objeto_recibido.get("motivo", "El servidor se cerró.")
            self.senal_terminar_app.emit(motivo)

        elif comando == "ingreso_blackjack_exitoso":
            self.senal_abrir_blackjack.emit()

        elif comando == "dibujar_carta":
            self.senal_dibujar_carta.emit(objeto_recibido)

        elif comando == "cambio_turno":
            turno = objeto_recibido.get("turno_actual", "")
            self.senal_cambio_turno_blackjack.emit(turno)

        elif comando == "aviso_turno_dealer":
            self.senal_aviso_turno_dealer.emit()

        elif comando == "revelar_carta_dealer":
            self.senal_revelar_dealer.emit(objeto_recibido)

        elif comando == "fin_ronda_blackjack":
            self.senal_fin_ronda_blackjack.emit(objeto_recibido)

        elif comando == "actualizar_saldo":
            nuevo_saldo = objeto_recibido.get("nuevo_saldo")
            self.saldo = nuevo_saldo
            self.senal_actualizar_saldo.emit(nuevo_saldo)
            print(f"[CLIENTE] Nuevo saldo: {self.saldo}")
            minimo_global = min(parametros.APUESTA_MINIMA_BLACKJACK,
                                parametros.APUESTA_MINIMA_AVIATOR)
            if self.saldo < minimo_global:
                print("[CLIENTE] Sin dinero suficiente. Volviendo al menú.")
                self.senal_bancarrota.emit()
                self.senal_volver_principal.emit()

        elif comando == "jugador_perdio":
            self.senal_jugador_perdio.emit(objeto_recibido)
            print(f"[CLIENTE] Jugador perdió: {objeto_recibido.get('nombre')}")

        elif comando == "ingreso_fallido":
            motivo = objeto_recibido.get("motivo")
            print(f"[CLIENTE] No se pudo ingresar: {motivo}")
            self.senal_ingreso_fallido.emit(motivo)

        elif comando == "inicio_apuestas":
            print("[CLIENTE] El servidor abrió las apuestas.")

        elif comando == "apuesta_aceptada":
            monto = objeto_recibido.get("monto")
            nuevo_saldo = objeto_recibido.get("nuevo_saldo")
            self.senal_apuesta_aceptada.emit(monto, nuevo_saldo)
            self.saldo = nuevo_saldo

        elif comando == "apuesta_rechazada":
            motivo = objeto_recibido.get("motivo")
            print(f"[CLIENTE] Apuesta rechazada: {motivo}")
            self.senal_apuesta_rechazada.emit(motivo)

        elif comando == "ingreso_aviator_exitoso":
            self.cache_jugadores_aviator = objeto_recibido.get(
                "jugadores", [])
            self.senal_ingreso_aviator_exitoso.emit()

        elif comando == "aviator_inicio":
            self.senal_aviator_inicio.emit()

        elif comando == "aviator_avanza":
            mult = objeto_recibido.get("multiplicador")
            tiempo = objeto_recibido.get("tiempo")
            self.senal_aviator_avanza.emit(mult, tiempo)

        elif comando == "aviator_actualizar_barra":
            self.senal_aviator_actualizar_barra.emit(objeto_recibido)

        elif comando == "aviator_crash":
            final = objeto_recibido.get("multiplicador_final")
            resultados = objeto_recibido.get("resultados")
            self.senal_aviator_crash.emit(final, resultados)

        elif comando == "aviator_retiro":
            self.senal_aviator_retiro.emit(objeto_recibido)

        elif comando == "aviator_nueva_partida":
            self.senal_aviator_nueva_partida.emit()

        elif comando == "retiro_aviator_exitoso":
            ganancia = objeto_recibido.get("ganancia")
            nuevo_saldo = objeto_recibido.get("nuevo_saldo")
            self.senal_actualizar_saldo.emit(nuevo_saldo)
            self.senal_retiro_aviator_exitoso.emit(ganancia, nuevo_saldo)

        elif comando == "apuesta_cancelada":
            nuevo_saldo = objeto_recibido.get("nuevo_saldo")
            self.saldo = nuevo_saldo
            self.senal_apuesta_cancelada.emit(nuevo_saldo)

        elif comando == "aviator_nuevo_jugador":
            self.senal_aviator_nuevo_jugador.emit(objeto_recibido)

        elif comando == "aviator_jugador_salio":
            self.senal_aviator_jugador_salio.emit(objeto_recibido)

        elif comando == "aviator_kicked":
            print("[CLIENTE] Fui expulsado de Aviator por no apostar.")
            self.senal_aviator_kicked.emit()

        elif comando == "actualizar_stats":
            lista_stats = objeto_recibido.get("resultados", [])
            self.senal_actualizar_stats.emit(lista_stats)

        elif comando == "carga_exitosa":
            monto = objeto_recibido.get("monto", 0)
            self.senal_carga_exitosa.emit(monto)

        elif comando == "carga_rechazada":
            motivo = objeto_recibido.get("motivo",
                                         "Error al cargar dinero.")
            self.senal_carga_rechazada.emit(motivo)

        else:
            print(f"[CLIENTE] Comando no reconocido: {comando}")