import threading
import time
import random
import math
import parametros

class LogicaAviator:

    def __init__(self, servidor):
        self.servidor = servidor
        self.jugadores = {}  # {nombre: {apuesta, estado, saldo, ganancia}}
        self.juego_activo = False  # True si el avión está volando
        self.fase_apuestas = True
        self.lock = threading.RLock()

        self.multiplicador_actual = 1.0
        self.tiempo_inicio = 0
        self.tiempo_crash = 0

    def agregar_jugador(self, nombre_usuario, saldo):
        with self.lock:
            if nombre_usuario not in self.jugadores:
                self.jugadores[nombre_usuario] = {
                    "apuesta": 0,
                    "estado": "esperando",  # else apostado, retirado, perdio
                    "saldo": saldo,
                    "ganancia": 0
                }
                self.servidor.enviar_mensaje_a_todos("aviator_nuevo_jugador", {
                    "nombre": nombre_usuario,
                    "saldo": saldo
                })
                lista_jugadores = []
                for nombre, datos in self.jugadores.items():
                    lista_jugadores.append({
                        "nombre": nombre,
                        "apuesta": datos["apuesta"],
                        "estado": datos["estado"],
                        "ganancia": datos["ganancia"]
                    })

                return True, lista_jugadores
            return False, []

    def remover_jugador(self, nombre_usuario):
        saldo_retorno = None
        with self.lock:
            if nombre_usuario in self.jugadores:
                datos = self.jugadores[nombre_usuario]
                if datos['estado'] == 'apostado':
                    if self.fase_apuestas:
                        print(f"[AVIATOR] Reembolsando a {nombre_usuario}")
                        datos['saldo'] += datos['apuesta']
                        saldo_retorno = datos['saldo']
                    else:
                        print(f"[AVIATOR] Jugador {nombre_usuario} "
                              f"desconectado. Penalizando.")
                        self.servidor.aplicar_penalidad_desconexion(
                            nombre_usuario,datos['apuesta'])
                        saldo_retorno = datos['saldo']
                else:
                    saldo_retorno = datos['saldo']
                del self.jugadores[nombre_usuario]
                self.servidor.enviar_mensaje_a_todos("aviator_jugador_salio", {
                    "nombre": nombre_usuario
                })
            if len(self.jugadores) == 0:
                self.juego_activo = False
                self.fase_apuestas = True
        return saldo_retorno

    def registrar_apuesta(self, nombre_usuario, monto):
        with self.lock:
            if self.juego_activo or not self.fase_apuestas:
                return False, "Ronda en curso o apuestas cerradas"

            if nombre_usuario not in self.jugadores:
                return False, "Jugador no está en la sala"

            datos = self.jugadores[nombre_usuario]

            if monto > datos["saldo"]:
                return False, "Saldo insuficiente"
            if monto < parametros.APUESTA_MINIMA_AVIATOR:
                return False, f"Mínimo ${parametros.APUESTA_MINIMA_AVIATOR}"
            if monto > parametros.APUESTA_MAXIMA_AVIATOR:
                return False, "Excede el máximo"

            datos["apuesta"] = monto
            datos["estado"] = "apostado"
            datos["saldo"] -= monto


            apostadores = [u for u in self.jugadores.values()
                           if u["estado"] == "apostado"]
            if len(apostadores) >= 3:
                self.iniciar_ronda()

            self.servidor.enviar_mensaje_a_todos("aviator_actualizar_barra", {
                "nombre": nombre_usuario,
                "monto": monto,
            })

            return True, "Apuesta registrada"

    def cancelar_apuesta(self, nombre_usuario):
        with self.lock:
            if not self.fase_apuestas:
                return False, "Ronda en curso."

            if nombre_usuario in self.jugadores:
                datos = self.jugadores[nombre_usuario]
                if datos["estado"] == "apostado":
                    monto = datos["apuesta"]
                    datos["saldo"] += monto
                    datos["apuesta"] = 0
                    datos["estado"] = "esperando"

                    self.servidor.enviar_mensaje_a_todos(
                        "aviator_actualizar_barra", {
                        "nombre": nombre_usuario,
                        "monto": 0,
                        "cancelado": True
                    })
                    return True, monto
                return False, "No hay apuesta."
            return False, "Usuario no encontrado."

    def retirar_jugador(self, nombre_usuario):
        with self.lock:
            if not self.juego_activo:
                return False, "El avión no está volando"

            if nombre_usuario not in self.jugadores:
                return False, "Usuario no encontrado"

            datos = self.jugadores[nombre_usuario]
            if datos["estado"] != "apostado":
                return False, "No estás jugando esta ronda"

            monto_ganado = int(datos["apuesta"] * self.multiplicador_actual)

            datos["estado"] = "retirado"
            datos["ganancia"] = monto_ganado
            nuevo_saldo = datos["saldo"] + monto_ganado
            if nuevo_saldo > parametros.SALDO_MAXIMO:
                nuevo_saldo = parametros.SALDO_MAXIMO
            datos["saldo"] = nuevo_saldo

            print(f"[AVIATOR] {nombre_usuario} se retiró en {self.multiplicador_actual:.2f}x")

            self.servidor.enviar_mensaje_a_todos("aviator_retiro", {
                "nombre": nombre_usuario,
                "monto": monto_ganado,
                "multiplicador": self.multiplicador_actual
            })

            return True, monto_ganado

    def iniciar_ronda(self):
        with self.lock:
            if not self.fase_apuestas:
                return
            jugadores_a_echar = []
            for nombre, datos in self.jugadores.items():
                if datos["estado"] == "esperando":
                    jugadores_a_echar.append(nombre)

            for nombre in jugadores_a_echar:
                if nombre in self.servidor.clientes_activos:
                    ccs = self.servidor.clientes_activos[nombre]
                    self.servidor.enviar_objeto_cliente(
                        {"comando": "aviator_kicked"}, ccs
                    )

                del self.jugadores[nombre]

                self.servidor.enviar_mensaje_a_todos("aviator_jugador_salio", {
                    "nombre": nombre
                })
            print("[AVIATOR] Iniciando despegue...")
            self.fase_apuestas = False

            factor = random.betavariate(1.4, 4.0)
            self.tiempo_crash = factor * parametros.DURACION_RONDA_AVIATOR

            print(f"[AVIATOR] Tiempo crash calculado: "
                  f"{self.tiempo_crash:.4f}s")

            thread_juego = threading.Thread(target=self.bucle_juego,
                                            daemon=True)
            thread_juego.start()

    def bucle_juego(self):

        with self.lock:
            self.juego_activo = True

        self.servidor.enviar_mensaje_a_todos("aviator_inicio", {})
        time.sleep(1)

        with self.lock:
            self.inicio_tiempo = time.time()

        while self.juego_activo:
            tiempo_transcurrido = time.time() - self.inicio_tiempo
            if tiempo_transcurrido >= self.tiempo_crash:
                self.evento_crash()
                break
            nuevo_mult = 1 + (math.exp(0.55 * tiempo_transcurrido) - 1)
            with self.lock:
                self.multiplicador_actual = round(nuevo_mult, 2)
            self.servidor.enviar_mensaje_a_todos(
                "aviator_avanza",
                {"multiplicador": self.multiplicador_actual,
                 "tiempo": tiempo_transcurrido})

            time.sleep(0.1)

    def evento_crash(self):
        with self.lock:
            self.juego_activo = False
            print(f"[AVIATOR] CRASH en {self.multiplicador_actual:.2f}x")

            resultados = []
            for nombre, datos in self.jugadores.items():
                if datos["estado"] == "apostado": # Perdió
                    datos["estado"] = "perdio"
                    datos["ganancia"] = 0
                    neto = -datos["apuesta"]
                elif datos["estado"] == "retirado": # Ganó
                    neto = datos["ganancia"] - datos["apuesta"]
                else:
                    continue

                resultados.append({
                    "nombre_usuario": nombre,
                    "ganancia": neto,
                    "apuesta": datos["apuesta"],
                    "retirado": (datos["estado"] == "retirado")
                })

        self.servidor.enviar_mensaje_a_todos("aviator_crash", {
            "multiplicador_final": self.multiplicador_actual,
            "resultados": resultados
        })

        self.servidor.finalizar_ronda_aviator(resultados)
        self.resetear_juego()

    def resetear_juego(self):
        print("[AVIATOR] Reseteando mesa...")
        time.sleep(5)
        with self.lock:
            self.fase_apuestas = True
            self.multiplicador_actual = 1.0
            for nombre in self.jugadores:
                self.jugadores[nombre]["apuesta"] = 0
                self.jugadores[nombre]["estado"] = "esperando"
                self.jugadores[nombre]["ganancia"] = 0
        self.servidor.enviar_mensaje_a_todos("aviator_nueva_partida", {})