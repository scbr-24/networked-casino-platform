import socket
import threading
import json
import pickle
from os.path import join, dirname
import requests
import protocolo
import parametros
import api
import time
from juegos.logica_blackjack import LogicaBlackjack
from juegos.logica_aviator import LogicaAviator
from procesador import ProcesadorInstrucciones


class ConexionClienteServidor(threading.Thread):

    # Gestiona el thread de cada cliente
    def __init__(self, socket_cliente, direccion_cliente, servidor):
        super().__init__(daemon = True)
        self.socket_cliente = socket_cliente
        self.direccion_cliente = direccion_cliente
        self.servidor = servidor
        self.conectado = True
        self.nombre_usuario = None # Depende del login
        self.saldo = 0

    def run(self):
        # Lee los datos del cliente
        print(f"[Conexion Cliente Servidor] Conexion aceptada desde "
              f"{self.direccion_cliente}")
        while self.conectado:
            try:
                largo_mensaje_bytes = self.socket_cliente.recv(4)
                if not largo_mensaje_bytes:
                    print(
                        f"[Conexion] Cliente {self.direccion_cliente} "
                        f"cerró la conexión (0 bytes).")
                    break
                largo_paquete = int.from_bytes(largo_mensaje_bytes,
                                               byteorder = "little")
                largo_paquete_esperado = (protocolo.
                                          calcular_total_paquetes(
                    largo_paquete))

                paquete_completo = bytearray()
                while len(paquete_completo) < largo_paquete_esperado:
                    bytes_por_leer = min(4096,
                                         largo_paquete_esperado -
                                         len(paquete_completo))
                    paquete_recibido = self.socket_cliente.recv(
                        bytes_por_leer)
                    if not paquete_recibido:
                        raise ConnectionResetError
                    paquete_completo.extend(paquete_recibido)

                objeto_recibido = (protocolo.
                                   decodificar_mensaje(largo_mensaje_bytes +
                                                       bytes(
                    paquete_completo)))
                try:
                    self.servidor.procesar_instruccion(objeto_recibido, self)
                except ValueError as e:
                    print(f"[ERROR LOGICA] Valor inválido en instrucción: "
                          f"{e}")
            except (ConnectionError, ConnectionResetError, socket.error):
                print(f"[Conexion] Error de conexión con "
                      f"{self.direccion_cliente}")
                break
            except (pickle.UnpicklingError, IndexError, ValueError,
                    KeyError) as e:
                print(f"[ERROR Protocolo] Cliente {self.direccion_cliente} "
                      f"envio mensaje invalido: {e}")
                break
        self.servidor.desconexion_cliente(self)


class Servidor:


    def __init__(self, archivo_conexion = "conexion.json"):
        config = self._cargar_config(archivo_conexion)
        self.host, self.port, self.port_api = config

        # direccion: instancia conexion_cliente_servidor
        self.clientes_activos = {}
        self.socket_servidor = None

        self.blackjack = LogicaBlackjack(self)
        self.aviator = LogicaAviator(self)
        self.procesador = ProcesadorInstrucciones(self)

        self.api_thread = threading.Thread(target = self._iniciar_api,
                                           daemon = True)
        self.api_thread.start()
        self.iniciar_servidor()

    def _cargar_config(self, nombre_archivo):
        # Carga info de host y port desde json
        try:
            path = join(dirname(__file__), nombre_archivo)
            with open(path, "r") as a:
                config = json.load(a)
            return config["host"], config["puerto"], config["puertoAPI"]
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"ERROR EN LA CARGA DE INFORMACIÓN DE CONEXIÓN: {e}")
            exit(1)

    def iniciar_servidor(self):
        # Crea sockets, conecta, escucha y acepta threads
        try:
            self.socket_servidor = socket.socket(socket.AF_INET,
                                                  socket.SOCK_STREAM)
            self.socket_servidor.bind((self.host, self.port))
            self.socket_servidor.listen()
            print(f"Server activo y escuchando en {self.host} : "
                  f"{self.port}")
            self.thread_aceptar_clientes = threading.Thread(
                target = self.aceptar_clientes_thread,
                daemon = True
            )
            self.thread_aceptar_clientes.start()
        except socket.error as e:
            print(f"ERROR al iniciar el servidor: {e}")
            self.cerrar_servidor()

    def aceptar_clientes_thread(self):
        # Acepta nuevas conexiones
        while True:
            try:
                socket_cliente, direccion_cliente = (self.
                                                      socket_servidor.
                                                      accept())
                print(f"Nuevo cliente conectado desde {direccion_cliente}")
                ccs = ConexionClienteServidor(socket_cliente,
                                              direccion_cliente, self)
                ccs.start()
            except socket.error as e:
                print(f"ERROR al aceptar conexión: {e}")
                break

    def desconexion_cliente(self, ccs):
        # Desconecta y elimina a cliente
        if ccs.nombre_usuario:
            self.blackjack.remover_jugador(ccs.nombre_usuario)
            self.aviator.remover_jugador(ccs.nombre_usuario)
            if ccs.nombre_usuario in self.clientes_activos:
                self.clientes_activos.pop(ccs.nombre_usuario)
        id = ccs.nombre_usuario if ccs.nombre_usuario else (
            ccs.direccion_cliente)
        print(f"Desconexión: {id} ha sido eliminado de la lista")
        try:
            ccs.socket_cliente.close()
        except:
            pass

    def procesar_instruccion(self, instruccion, ccs):
        self.procesador.procesar(instruccion, ccs)

    def enviar_objeto_cliente(self, objeto, ccs):
        # se ejecuta en procesar_instruccion
        try:
            mensaje_codificado = protocolo.codificar_mensaje(objeto)
            ccs.socket_cliente.sendall(mensaje_codificado)
        except (socket.error, ConnectionError) as e:
            print(f"ERROR al enviar mensaje a {ccs.direccion_cliente}: {e}")
            ccs.conectado = False # Cierra conexion cliente servidor thread

    def enviar_mensaje_a_todos(self, comando, data):
        mensaje = data.copy()
        mensaje["comando"] = comando
        for nombre, ccs in list(self.clientes_activos.items()):
            self.enviar_objeto_cliente(mensaje, ccs)

    def finalizar_ronda_blackjack(self, resultados, puntaje_dealer):
        # Maneja el fin de ronda: actualiza base de datos y notifica clientes
        print("[BLACKJACK] Fin de ronda. Resultados:")
        for r in resultados:
            print(f"Nombre: {r.get('nombre_usuario', '')}")
            print(f"Ganancia: {r.get('ganancia', '')}")
            print(f"Puntaje: {r.get('puntaje', '')}")
            print(f"Saldo Final: {r.get('saldo_final', '')}")
            print()
        # Notifica a todos los clientes
        msj_clientes = {
            "resultados": resultados,
            "puntaje_dealer": puntaje_dealer}
        self.enviar_mensaje_a_todos("fin_ronda_blackjack",
                                    msj_clientes)

        # Actualizar base de datos (API)
        url_base = f"http://{self.host}:{self.port_api}"
        headers = {"Authorization": parametros.TOKEN_AUTENTICACION}
        try:
            requests.post(f"{url_base}/games/B",
                          json={"resultados": resultados},
                          headers=headers)
        except requests.exceptions.RequestException as e:
            print(f"[ERROR API] Fallo al guardar historial Blackjack: {e}")
        for r in resultados:
            nombre = r["nombre_usuario"]
            nuevo_saldo = r["saldo_final"]

            try:
                requests.patch(f"{url_base}/users/{nombre}",
                               json={"nuevo_saldo": nuevo_saldo},
                               headers=headers)
                if nombre in self.clientes_activos:
                    ccs = self.clientes_activos[nombre]
                    ccs.saldo = nuevo_saldo
                    self.enviar_objeto_cliente({
                        "comando": "actualizar_saldo",
                        "nuevo_saldo": nuevo_saldo
                    }, ccs)

            except requests.exceptions.RequestException as e:
                print(f"[ERROR API] Al actualizar saldo de {nombre}: {e}")
        self.notificar_actualizacion_estadisticas()

    def cerrar_servidor(self):
        if self.socket_servidor:
            self.socket_servidor.close()
        print(f"CIERRE DE SERVIDOR")

    def _iniciar_api(self):
        print(f"[API] Iniciando servicio web en puerto {self.port_api}...")
        app = api.crear_app(self.host, self.port_api)
        app.run(host = self.host, port = self.port_api, debug = False,
                use_reloader = False)

    def aplicar_penalidad_desconexion(self, nombre_usuario, monto_perdido):
        print(
            f"[SERVIDOR] Aplicando penalidad de desconexión a "
            f"{nombre_usuario}: -${monto_perdido}")
        url_base = f"http://{self.host}:{self.port_api}"
        headers = {"Authorization": parametros.TOKEN_AUTENTICACION}

        try:
            respuesta = requests.get(f"{url_base}/users/{nombre_usuario}")
            if respuesta.status_code == 200:
                saldo_actual = respuesta.json()["saldo"]
                nuevo_saldo = saldo_actual - monto_perdido

                requests.patch(f"{url_base}/users/{nombre_usuario}",
                               json={"nuevo_saldo": nuevo_saldo},
                               headers=headers)
                requests.post(f"{url_base}/games/P",
                              json={"resultados": {
                                  "nombre_usuario": nombre_usuario,
                                  "ganancia": -monto_perdido,
                                  "timestamp": time.time()
                              }},
                              headers=headers)
                print(f"[SERVIDOR] Penalidad registrada en historial.")
                self.notificar_actualizacion_estadisticas()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR SERVIDOR] No se pudo aplicar penalidad: {e}")

    def finalizar_ronda_aviator(self, resultados):
        # resultados = lista de dicts con llaves: nombre_usuario,
            # ganancia (neto), apuesta, retirado

        url_base = f"http://{self.host}:{self.port_api}"
        headers = {"Authorization": parametros.TOKEN_AUTENTICACION}

        try:
            requests.post(f"{url_base}/games/A",
                          json={"resultados": resultados},
                          headers=headers)
        except requests.exceptions.RequestException as e:
            print(f"[ERROR API] Fallo al guardar historial Aviator: {e}")

        for r in resultados:
            nombre = r["nombre_usuario"]
            ganancia_neta = r["ganancia"]

            if ganancia_neta != 0:
                try:
                    resp = requests.get(f"{url_base}/users/{nombre}")
                    if resp.status_code == 200:
                        saldo_actual_db = resp.json()["saldo"]
                        nuevo_saldo_final = saldo_actual_db + ganancia_neta

                        requests.patch(f"{url_base}/users/{nombre}",
                                       json={"nuevo_saldo": nuevo_saldo_final},
                                       headers=headers)

                        if nombre in self.clientes_activos:
                            ccs = self.clientes_activos[nombre]
                            ccs.saldo = nuevo_saldo_final

                            self.enviar_objeto_cliente({
                                "comando": "actualizar_saldo",
                                "nuevo_saldo": nuevo_saldo_final
                            }, ccs)
                except requests.exceptions.RequestException as e:
                    print(f"[ERROR API] Al actualizar saldo Aviator "
                          f"{nombre}: {e}")
        self.notificar_actualizacion_estadisticas()

    def notificar_actualizacion_estadisticas(self):
        url_base = f"http://{self.host}:{self.port_api}"
        try:
            resp = requests.get(f"{url_base}/games?n=5")
            if resp.status_code == 200:
                stats = resp.json().get("resultados", [])
                (self.
                 enviar_mensaje_a_todos("actualizar_stats", {
                    "resultados": stats
                }))
        except requests.exceptions.RequestException as e:
            print(f"[SERVER] Error broadcast stats: {e}")
