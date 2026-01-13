import random
import time
import parametros

class LogicaBlackjack:


    def __init__(self, servidor):
        self.servidor = servidor
        self.jugadores = {} # nombre_usuario: {cartas, apuesta, estado}
        self.orden_turnos = []
        self.turno_actual = 0
        self.dealer_cartas = []
        self.juego_activo = False
        self.apuestas_cerradas = False

        self.pintas = ["hearts", "spades", "diamonds", "clubs"]
        self.valores = [f"{n:02}" for n in range(2, 11)] + ["J", "Q", "K", "A"]

    def agregar_jugador(self, nombre_usuario, saldo):
        # Agregar jugador a la sala de espera
        if self.juego_activo:
            return False, "El juego ya está en curso"
        if len(self.jugadores) >= 4:
            return False, "La mesa está llena (Max 4)"
        if nombre_usuario not in self.jugadores:
            self.jugadores[nombre_usuario] = {
                "cartas": [],
                "apuesta": 0,
                "estado": "esperando",
                "saldo": saldo
            }
            return True, "Ingreso exitoso"
        return False, "Ya estás dentro de la sala"

    def remover_jugador(self, nombre_usuario):
        saldo_actual = None
        if nombre_usuario in self.jugadores:
            datos = self.jugadores[nombre_usuario]
            if datos['estado'] in ['apostado', 'jugando', 'plantado']:
                if not self.juego_activo:
                    print(f"[BLACKJACK] Reembolsando apuesta a "
                          f"{nombre_usuario}.")
                    datos['saldo'] += datos['apuesta']
                else:
                    print(f"[BLACKJACK] Jugador {nombre_usuario} se "
                          f"desconectó en juego. Penalizando.")
                    self.servidor.aplicar_penalidad_desconexion(
                        nombre_usuario, datos['apuesta'])
            saldo_actual = datos['saldo']

            if self.juego_activo and self.orden_turnos:
                try:
                    id_jugador = self.orden_turnos.index(nombre_usuario)
                    if id_jugador == self.turno_actual:
                        print(f"[BLACKJACK] El jugador actual "
                              f"{nombre_usuario} salió. Avanzando lógica.")
                except ValueError:
                    pass

            del self.jugadores[nombre_usuario]
            if nombre_usuario in self.orden_turnos:
                id_salida = self.orden_turnos.index(nombre_usuario)
                self.orden_turnos.remove(nombre_usuario)
                if self.juego_activo:
                    if id_salida < self.turno_actual:
                        self.turno_actual -= 1
                    elif id_salida == self.turno_actual:
                        if self.turno_actual >= len(self.orden_turnos):
                            self.turno_dealer()
                        else:
                            self.notificar_turno_actual()
            return saldo_actual

        if len(self.jugadores) == 0:
            print(f"[BLACKJACK] Mesa vacía. Reiniciando estado del juego.")
            self.juego_activo = False
            self.apuestas_cerradas = False
            self.orden_turnos = []
            self.dealer_cartas = []
            self.turno_actual = 0
        return None

    def registrar_apuesta(self, nombre_usuario, monto):
        # Inicia el juego if 4 jugadores
        if self.juego_activo:
            return False, "El juego ya está en curso"
        if nombre_usuario in self.jugadores:
            datos_jugador = self.jugadores[nombre_usuario]
            apuesta_anterior = datos_jugador["apuesta"]
            saldo_total = datos_jugador["saldo"] + apuesta_anterior
            if monto > saldo_total:
                return False, "Saldo insuficiente"
            if monto > parametros.APUESTA_MAXIMA_BLACKJACK:
                return False, f"Apuesta excede el máx ({parametros.APUESTA_MAXIMA_BLACKJACK})"
            if monto < parametros.APUESTA_MINIMA_BLACKJACK:
                return False, f"La apuesta mínima es {parametros.APUESTA_MINIMA_BLACKJACK}."

            self.jugadores[nombre_usuario]['apuesta'] = monto
            self.jugadores[nombre_usuario]['estado'] = 'apostado'
            self.jugadores[nombre_usuario]['saldo'] = saldo_total - monto
            jugadores_apostados = [u for u in self.jugadores.values() if
                                   u['estado'] == 'apostado']
            if (len(jugadores_apostados) == len(self.jugadores) and
                    len(jugadores_apostados) == 4):
                self.iniciar_ronda()
            return True, "Apuesta registrada"
        return False, "Jugador no encontrado"

    def cancelar_apuesta(self, nombre_usuario):
        if self.juego_activo:
            return False, "El juego ya comenzó, no se puede cancelar."
        if nombre_usuario in self.jugadores:
            datos = self.jugadores[nombre_usuario]
            if datos['estado'] == 'apostado':
                monto = datos['apuesta']
                datos['saldo'] += monto
                datos['apuesta'] = 0
                datos['estado'] = 'esperando'
                return True, monto
            return False, "No tienes apuesta activa."
        return False, "Usuario no encontrado."

    def generar_carta(self):
        pinta = random.choice(self.pintas)
        valor = random.choice(self.valores)
        return pinta, valor

    def calcular_puntaje(self, cartas):
        valor_total = 0
        ases = 0

        for pinta, valor in cartas:
            if valor in ["J", "Q", "K"]:
                valor_total += 10
            elif valor == "A":
                ases += 1
                valor_total += 11
            else:
                valor_total += int(valor)

        while valor_total > 21 and ases > 0:
            valor_total -= 10
            ases -= 1

        return valor_total

    def iniciar_ronda(self):
        print("[BLACKJACK] Iniciando ronda...")
        self.juego_activo = True
        self.apuestas_cerradas = True
        self.dealer_cartas = []
        self.orden_turnos = [u for u in self.jugadores if
                             self.jugadores[u]['estado'] == 'apostado']
        self.turno_actual = 0

        # Se reinician las manos
        for nombre in self.orden_turnos:
            self.jugadores[nombre]['cartas'] = []
            self.jugadores[nombre]['estado'] = 'jugando'

        time.sleep(1)
        # Repartición de 2 primeras cartas
        for _ in range(2):
            es_segunda_carta = (_ == 1)
            for nombre in self.orden_turnos:
                carta = self.generar_carta()
                self.jugadores[nombre]['cartas'].append(carta)
                self.notificar_carta(nombre, carta, oculta = es_segunda_carta)
                time.sleep(0.2)

        # Repartición inicial dealer
        carta_visible = self.generar_carta()
        carta_oculta = self.generar_carta()
        self.dealer_cartas = [carta_visible, carta_oculta]

        self.notificar_carta("dealer", carta_visible,
                             oculta=False)
        self.notificar_carta("dealer", carta_oculta,
                             oculta=True)

        # Inicia turnos
        self.notificar_turno_actual()

    def manejar_accion(self, nombre_usuario, accion):
        # Maneja pedir o plantarse
        if (not self.juego_activo or not self.orden_turnos or
                self.turno_actual >= len(self.orden_turnos)):
            return

        # Verificar que sea el turno del jugador
        jugador_actual = self.orden_turnos[self.turno_actual]
        if nombre_usuario != jugador_actual:
            print(f"[ERROR] {nombre_usuario} intentó jugar pero es el "
                  f"turno de {jugador_actual}")
            return

        if accion == "pedir":
            carta = self.generar_carta()
            self.jugadores[nombre_usuario]['cartas'].append(carta)
            self.notificar_carta(nombre_usuario, carta)

            puntaje = self.calcular_puntaje(self.jugadores[
                                                nombre_usuario]['cartas'])
            if puntaje > 21:
                # Jugador perdió
                self.jugadores[nombre_usuario]['estado'] = 'perdio'
                self.servidor.enviar_mensaje_a_todos("jugador_perdio",
                                                     {"nombre":
                                                          nombre_usuario})
                self.siguiente_turno()

        elif accion == "plantarse":
            self.jugadores[nombre_usuario]['estado'] = 'plantado'
            self.siguiente_turno()

    def siguiente_turno(self):
        self.turno_actual += 1
        # Si ya jugaron todos, turno del dealer
        if self.turno_actual >= len(self.orden_turnos):
            self.turno_dealer()
        else:
            self.notificar_turno_actual()

    def turno_dealer(self):
        print("[BLACKJACK] Turno del Dealer")
        self.servidor.enviar_mensaje_a_todos("aviso_turno_dealer", {})
        time.sleep(3)
        carta_oculta = self.dealer_cartas[1]
        # Instrucción a todos -> revelar carta dealer
        self.servidor.enviar_mensaje_a_todos("revelar_carta_dealer", {
            "pinta": carta_oculta[0],
            "valor": carta_oculta[1]
        })

        time.sleep(1)

        # Dealer -> pedir hasta 17 o más
        while True:
            puntaje = self.calcular_puntaje(self.dealer_cartas)
            if puntaje < 17:
                carta = self.generar_carta()
                self.dealer_cartas.append(carta)
                self.notificar_carta("dealer", carta)
                time.sleep(1)
            else:
                break
        # Resultados
        time.sleep(3)
        self.calcular_resultados()

    def calcular_resultados(self):
        puntaje_dealer = self.calcular_puntaje(self.dealer_cartas)
        resultados = []  # Lista de dicts para enviar a clientes/API

        for nombre in self.orden_turnos:
            datos = self.jugadores[nombre]
            puntaje_jugador = self.calcular_puntaje(datos['cartas'])
            apuesta = datos['apuesta']
            ganancia = 0

            if puntaje_dealer > 21:
                # Caso 1: Dealer se pasa
                if datos['estado'] == 'perdio':
                    # Si el jugador también se pasó, recupera su apuesta
                    ganancia = apuesta
                else:
                    # Si el jugador no se pasó, gana x2
                    ganancia = apuesta * 2
            else:
                # Caso 2: Dealer no se pasa (<= 21)
                if datos['estado'] == 'perdio':
                    ganancia = 0  # Jugador se pasó, pierde
                elif puntaje_jugador > puntaje_dealer:
                    ganancia = apuesta * 2  # Jugador tiene más que dealer
                elif puntaje_jugador == puntaje_dealer:
                    ganancia = apuesta  # Empate, recupera
                else:
                    ganancia = 0  # Dealer tiene más, pierde
            neto = ganancia - apuesta
            nuevo_saldo = self.jugadores[nombre]["saldo"] + ganancia
            if nuevo_saldo > parametros.SALDO_MAXIMO:
                nuevo_saldo = parametros.SALDO_MAXIMO
            self.jugadores[nombre]["saldo"] = nuevo_saldo
            self.jugadores[nombre]["estado"] = "esperando"
            self.jugadores[nombre]["apuesta"] = 0
            saldo_final = self.jugadores[nombre]["saldo"]
            # Actualizar saldo en memoria del servidor
            resultados.append({
                "nombre_usuario": nombre,
                "ganancia": neto,
                "puntaje": puntaje_jugador,
                "saldo_final": saldo_final
            })

        # Notificar fin de juego
        self.servidor.finalizar_ronda_blackjack(resultados, puntaje_dealer)
        print("[BLACKJACK] Esperando 5 segundos para reiniciar ronda...")

        time.sleep(5)

        self.juego_activo = False
        self.apuestas_cerradas = False
        self.dealer_cartas = []
        self.orden_turnos = []
        self.turno_actual = 0

        self.servidor.enviar_mensaje_a_todos("inicio_apuestas", {})
        print("[BLACKJACK] Ronda finalizada. Apuestas abiertas.")

    def notificar_carta(self, destinatario_carta, carta,
                        oculta=False):
        # Mensaje a jugadores para dibujar carta
        pinta, valor = carta
        mensaje = {
            "comando": "dibujar_carta",
            "quien": destinatario_carta,  # Nombre de usuario o dealer
            "pinta": pinta,
            "valor": valor,
            "oculta": oculta
        }
        self.servidor.enviar_mensaje_a_todos("dibujar_carta", mensaje)

    def notificar_turno_actual(self):
        jugador_actual = self.orden_turnos[self.turno_actual]
        self.servidor.enviar_mensaje_a_todos("cambio_turno", {
            "turno_actual": jugador_actual})
