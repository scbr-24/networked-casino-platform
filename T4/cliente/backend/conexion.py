import socket
import json
import threading
import pickle
from os.path import join, dirname
from . import protocolo
from .logica_cliente import LogicaCliente
from PyQt5.QtCore import QObject, pyqtSignal
import parametros


class ConexionCliente(QObject):

    # Conecta el cliente con el servidor
    senal_desconexion = pyqtSignal(str)
    # Conexion TCP por Socket, Threading y Protocolo de Comms de objetos
    def __init__(self, logica_cliente: LogicaCliente,
                 archivo_conexion = "conexion.json"):
        super().__init__()
        self.logica_cliente = logica_cliente
        config = self._cargar_config(archivo_conexion)
        self.host, self.port, self.port_api = config
        self.socket_cliente = self._crear_nuevo_socket()
        self.conectado = False

    def _crear_nuevo_socket(self):
        # socket TCP
        return socket.socket(socket.AF_INET,
                                            socket.SOCK_STREAM)

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

    def conexion_server(self):
        # Intenta conectar con el servidor
        self.socket_cliente.close()
        self.socket_cliente = self._crear_nuevo_socket()
        try:
            self.socket_cliente.connect((self.host, self.port))
            self.conectado = True
            texto = (f"\nCONEXIÓN ESTABLECIDA CON EL SERVIDOR EN:\n"
                  f"{self.host} : {self.port}")
            self.escuchar()
            return True, texto
        except (ConnectionRefusedError, socket.timeout):
            return False, f"ERROR DE CONEXIÓN AL SERVER: INTENTE NUEVAMENTE"
        except ConnectionError as e:
            texto = f"ERROR EN LA CONEXIÓN CON EL SERVIDOR: {e}"
            return False, texto

    def escuchar(self):
        # Thread para escuchar mensajes de servidor
        thread = threading.Thread(target = self.escuchar_thread,
                                  daemon = True)
        thread.start()

    def escuchar_thread(self):

        while self.conectado:
            try:
                largo_paquete_bytes = self.socket_cliente.recv(4)
                if not largo_paquete_bytes:
                    raise ConnectionResetError
                # Largo es multiplo de 128
                largo_paquete = int.from_bytes(largo_paquete_bytes,
                                               byteorder = "little")

                largo_paquete_esperado = (protocolo.
                                          calcular_total_paquetes(
                    largo_paquete))

                # Recibo de los bytes
                paquete_completo = bytearray()

                while len(paquete_completo) < largo_paquete_esperado:

                    bytes_por_leer = min(4096, largo_paquete_esperado -
                                         len(paquete_completo))
                    paquete_recibido = self.socket_cliente.recv(
                        bytes_por_leer)
                    if not paquete_recibido:
                        raise ConnectionResetError
                    paquete_completo.extend(paquete_recibido)

                mensaje_con_header = largo_paquete_bytes + paquete_completo
                # Decoding
                objeto_recibido = protocolo.decodificar_mensaje(
                    mensaje_con_header)
                self.logica_cliente.procesar_respuesta_servidor(
                    objeto_recibido)


            except (ConnectionError, ConnectionResetError, socket.error):
                self.desconexion_fatal("EL SERVIDOR SE DESCONECTÓ")
                break
            except (pickle.UnpicklingError, IndexError, ValueError,
                    OverflowError) as e:
                self.desconexion_fatal(f"ERROR DE PROTOCOLO O DE "
                                       f"LECTURA: {e}")
                break

    def enviar_instruccion(self, instruccion):
        # Recibe, codifica y envia dict a server
        if self.conectado:
            try:
                mensaje_codificado = protocolo.codificar_mensaje(
                    instruccion)
                self.socket_cliente.sendall(mensaje_codificado)
            except (socket.error, ConnectionError) as e:
                print(f"ERROR AL ENVIAR INSTRUCCION: {e}")
                self.desconexion_fatal("FALLO DE ENVIO DE DATOS")
        else:
            print("EL CLIENTE NO ESTÁ CONECTADO")

    def desconexion_fatal(self, motivo):
        if self.conectado:
            self.conectado = False
            try:
                self.socket_cliente.close()
            except:
                pass
            print(f"DESCONEXION FATAL: {motivo}")
            self.senal_desconexion.emit(motivo)

    def cerrar(self):
        self.conectado = False
        try:
            self.socket_cliente.close()
        except:
            pass

