from PyQt5.QtCore import (pyqtSignal, Qt, QTimer)
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout,
    QDesktopWidget, QLineEdit,
    QSizePolicy, QMessageBox, QInputDialog,
    QListWidget, QListWidgetItem)
from backend.conexion import ConexionCliente
from backend.logica_cliente import LogicaCliente


class VEntrada(QWidget):


    senal_ingresar = pyqtSignal(str)

    def __init__(self, conexion_cliente: ConexionCliente,
                 logica_cliente: LogicaCliente):
        super().__init__()
        self.resize(612, 408)  # Tamaño de ventana
        self.conexion = conexion_cliente
        self.logica = logica_cliente
        self._centrar_en_pantalla()  # Centra ventana en pantalla
        self._inicializa_gui()  # Inicia objetos de la ventana
        self._conectar_senales()
        self.show()

    def _centrar_en_pantalla(self):
        marco = self.frameGeometry()  # Referencia al marco de la ventana
        centro = QDesktopWidget().availableGeometry().center()
        marco.moveCenter(centro)  # Mueve el marco al centro de la pantalla
        self.move(marco.topLeft())  # Ajusta la ventana al marco

    def _inicializa_gui(self):
        self.setWindowTitle("Ventana de Entrada")
        self._crear_widgets()  # Crea objetos
        self._crear_layout()  # Crea un layout para objetos
        self._estetica()  # Aplica cambios de apariencia

    def _crear_widgets(self):
        texto_entrada = ("BIENVENIDO A LOS JUEGOS DE DCCASINO")

        texto_dinamico = ("ESCRIBA SU NOMBRE Y PRESIONE "
                 "CONTINUAR")

        self.mensaje_bienvenida = QLabel(texto_entrada)
        self.mensaje_bienvenida.setAlignment(Qt.AlignHCenter)

        self.mensaje_dinamico = QLabel(texto_dinamico)
        self.mensaje_dinamico.setAlignment(Qt.AlignHCenter)

        self.input_nombre = QLineEdit(self)

        self.boton_ingreso = QPushButton("\nINGRESAR\n")

    def _estetica(self):
        self.setStyleSheet("background-color: #D3D3D3")
        self.input_nombre.setPlaceholderText("ESPERANDO INPUT")
        tamano_fuente = ["28px", "20px"]
        for _ in [self.mensaje_bienvenida, self.mensaje_dinamico]:
            _.setStyleSheet("font-weight: bold; "
                            "color: black; "
                            f"font-size: {tamano_fuente[0]}")
            tamano_fuente.pop(0)
        self.input_nombre.setStyleSheet(
            "border-style: solid; "
            "border-width: 2px; "
            "border-color: black; "
            "background-color: white; "
            "font-weight: bold; "
            "color: black; "
            "font-size: 18px")
        self.boton_ingreso.setStyleSheet(
            "background-color: #D3D3D3; "
            "font-weight: bold; "
            "color: black; "
            "font-size: 18px")
        self.input_nombre.setMinimumWidth(400)
        self.input_nombre.setMinimumHeight(60)

    def _crear_layout(self):
        vbox_entrada = QVBoxLayout()  # Layout vertical
        vbox_entrada.addStretch(1)
        for _ in [self.mensaje_bienvenida, self.mensaje_dinamico,
                  self.input_nombre, self.boton_ingreso]:
            vbox_entrada.addWidget(_)
            vbox_entrada.addStretch(1)
        self.setLayout(vbox_entrada)  # Se fija el layout

    def _conectar_senales(self):
        self.boton_ingreso.clicked.connect(self.intentar_login)
        self.logica.senal_login_fallido.connect(self.mostrar_error)
        self.logica.senal_login_exitoso.connect(self.abrir_ventana_principal)

    def intentar_login(self):
        nombre = self.input_nombre.text().strip()
        if not nombre:
            self.mostrar_error("Debe ingresar un nombre de usuario.")
            return
        instruccion = {
            "comando": "login_request",
            "nombre_usuario": nombre
        }

        if self.conexion.conectado:
            self.conexion.enviar_instruccion(instruccion)
            self.mensaje_dinamico.setText(f"Intengando ingresar como "
                                          f"{nombre}...")
        else:
            self.mostrar_error("Error: Cliente no conectado al servidor.")

    def mostrar_error(self, msj):
        mensaje = QMessageBox(self)
        mensaje.setIcon(QMessageBox.Warning)
        mensaje.setWindowTitle("ERROR DE INGRESO")
        mensaje.setText(msj)
        mensaje.setStyleSheet("QLabel { color: black; }"
                              "QPushButton { color: black; "
                              "background-color: gold; }")
        mensaje.exec_()
        self.mensaje_dinamico.setText("ESCRIBA SU NOMBRE Y "
                                      "PRESIONE\nCONTINUAR")

    def abrir_ventana_principal(self, nombre_usuario, saldo):
        self.hide()
        self.ventana_principal = VPrincipal(nombre_usuario, saldo,
                                            self.conexion)
        self.ventana_principal.show()


class VPrincipal(QWidget):


    senal_ingresar = pyqtSignal(str)

    def __init__(self, nombre_usuario, saldo, conexion):
        super().__init__()
        self.nombre_usuario = nombre_usuario
        self.saldo = saldo
        self.conexion = conexion
        self._centrar_en_pantalla() # Centra ventana en pantalla
        self._inicializa_gui() # Elementos interfaz
        self._conectar_senales()

    def _centrar_en_pantalla(self):
        marco = self.frameGeometry() # Anotaciones en VEntrada class
        centro = QDesktopWidget().availableGeometry().center()
        marco.moveCenter(centro)
        self.move(marco.topLeft())

    def _inicializa_gui(self):
        self.setWindowTitle(f"DCCASINO - {self.nombre_usuario.upper()}")
        self._crear_widgets()  # Crea objetos
        self._crear_layout()  # Crea un layout para objetos
        self._estetica() # Apariencia de widgets

    def _crear_widgets(self):
        self.lista_stats = QListWidget()
        self.datos_usuario = QLabel(f"Usuario: {self.nombre_usuario}\n"
                                    f"Saldo: ${self.saldo}")
        self.ultimos = QLabel("ÚLTIMOS 5 MOVIMIENTOS = ")

        self.datos_usuario = QLabel(f"Usuario: {self.nombre_usuario}\n"
                                    f"Saldo: ${self.saldo}")

        self.boton_a = QPushButton("BLACKJACK") # BlackJack
        self.boton_b = QPushButton("AVIATOR") # Aviator
        self.boton_c = QPushButton("RULETA INACTIVA") # Ruleta
        self.boton_d = QPushButton("CARGAR DINERO") # Cargar Dinero

    def _estetica(self):
        self.setStyleSheet("""
                    VPrincipal { background-color: grey; }
                    QDialog { background-color: white; color: black; }
                    QMessageBox { background-color: white; color: black; }
                """)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.lista_stats.setStyleSheet(
            "background-color: #D3D3D3; color: black; "
            "border: 2px solid black;"
            "font-weight: bold; font-size: 15px")
        color_borde = ["black", "black", "black", "black", "black"]
        colores_fondo = ["#228B22", "#B22222", "grey", "gold",
                         "grey", "black"]
        colores_letras = ["white", "white", "black", "black",
                          "black", "white"]
        self.ultimos.setAlignment(Qt.AlignCenter)
        self.ultimos.setStyleSheet("background-color: #D3D3D3; color: black; "
                                   "border: 2px solid black; "
                                   "font-weight: bold;"
                                   "font-size: 18px")
        self.ultimos.setMinimumHeight(50)
        self.ultimos.setMinimumWidth(200)

        for _ in [self.boton_a, self.boton_b,
                  self.boton_c, self.boton_d]:
            _.setStyleSheet(f"background-color: {colores_fondo[0]};"
                            "border-style: solid; "
                            "border-width: 2px; "
                            f"border-color: {color_borde[0]}; "
                            f"color: {colores_letras[0]}; "
                            "font-weight: bold; "
                            "font-size: 20px")
            _.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
            _.setMinimumHeight(50)
            _.setMinimumWidth(200)
            color_borde.pop(0)
            colores_fondo.pop(0)
            colores_letras.pop(0)

        for _ in ([self.datos_usuario]):
            _.setStyleSheet("background-color: #D3D3D3; "
                            "color: black; border: 2px solid black; "
                            "font-weight: bold; font-size: 20px")
            _.setMinimumHeight(50)
            _.setMinimumWidth(200)

    def _crear_layout(self):
        vbox_resultados = QVBoxLayout()
        vbox_derecha = QVBoxLayout()
        hbox_principal = QHBoxLayout()

        vbox_derecha.setSpacing(30)
        hbox_principal.setSpacing(10)

        vbox_resultados.addWidget(self.datos_usuario)
        vbox_resultados.addWidget(self.ultimos)
        vbox_resultados.addWidget(self.lista_stats)

        for _ in (self.boton_a, self.boton_b, self.boton_c,
                  self.boton_d):
            vbox_derecha.addWidget(_)

        hbox_principal.addLayout(vbox_resultados, 1)
        hbox_principal.addLayout(vbox_derecha, 1)
        self.setLayout(hbox_principal)

    def _conectar_senales(self):
        self.boton_a.clicked.connect(self.solicitar_ingreso_blackjack)
        self.boton_b.clicked.connect(self.solicitar_ingreso_aviator)
        self.boton_d.clicked.connect(self.iniciar_carga_dinero)
        self.conexion.logica_cliente.senal_ingreso_aviator_exitoso.connect(
            self.hide)
        self.conexion.logica_cliente.senal_abrir_blackjack.connect(
            self.hide)
        self.conexion.logica_cliente.senal_volver_principal.connect(
            self.show)
        self.conexion.logica_cliente.senal_actualizar_saldo.connect(
            self.actualizar_saldo_label)
        self.conexion.logica_cliente.senal_actualizar_stats.connect(
            self.actualizar_lista_stats)
        self.conexion.logica_cliente.senal_ingreso_fallido.connect(
            self.mostrar_error_ingreso)
        self.conexion.logica_cliente.senal_carga_exitosa.connect(
            self.mostrar_exito_carga)
        self.conexion.logica_cliente.senal_carga_rechazada.connect(
            self.mostrar_error_carga)
        QTimer.singleShot(500, self.solicitar_stats)

    def solicitar_stats(self):
        if self.conexion.conectado:
            self.conexion.enviar_instruccion({"comando": "solicitar_stats"})

    def actualizar_lista_stats(self, lista):
        self.lista_stats.clear()
        mapa_juegos = { # id juego -> nombre
            "A": "AVIATOR",
            "B": "BLACKJACK"
        }
        for item in lista: # lista de últimos movs
            juego = item.get("juego", "?")
            monto = item.get("monto", 0)
            usuario = item.get("nombre_usuario", "Desconocido")

            if juego in mapa_juegos:
                razon = mapa_juegos[juego]
            elif juego == "P": # desconexion o carga de dinero
                if monto >= 0:
                    razon = "CARGA"
                else:
                    razon = "DESCONEXIÓN"
            else:
                razon = "OTRO"

            if monto > 0: # ganó plata
                accion = "GANÓ"
                color = QColor("#228B22") # Verde
            elif monto < 0: # perdió plata
                accion = "PERDIÓ"
                color = QColor("#D9534F") # Rojo
            else: # ganó $0
                accion = "EMPATE"
                color = QColor("#B8860B") # Amarillo

            texto = f"[{usuario}] [{razon}] {accion} ${abs(monto)}"
            # [Usuario] [CARGA, BLACKJACK, AVIATOR, DESCONEXION] + ...
            # ... GANÓ, PERDIÓ ${monto}
            list_item = QListWidgetItem(texto)
            list_item.setForeground(color)

            self.lista_stats.addItem(list_item)

    def solicitar_ingreso_blackjack(self):
        if self.conexion.conectado:
            print("[VPrincipal] Solicitando ingreso a Blackjack...")
            (self.conexion.
             enviar_instruccion({"comando": "ingresar_blackjack"}))
        else:
            print("[ERROR] No hay conexión con el servidor")

    def actualizar_saldo_label(self, nuevo_saldo):
        self.saldo = nuevo_saldo
        self.datos_usuario.setText(f"Usuario: {self.nombre_usuario}\n"
                                   f"Saldo: ${self.saldo}")

    def solicitar_ingreso_aviator(self):
        if self.conexion.conectado:
            print("[VPrincipal] Solicitando ingreso a Aviator...")
            (self.conexion.
             enviar_instruccion({"comando": "ingresar_aviator"}))
        else:
            print("[ERROR] No hay conexión con el servidor")

    def iniciar_carga_dinero(self):
        monto, ok = QInputDialog.getInt(self, "Cargar Dinero",
                                        "Ingrese monto a cargar:",
                                        min=1)
        if ok:
            if self.conexion.conectado:
                print(f"[VPrincipal] Solicitando carga de ${monto}...")
                self.conexion.enviar_instruccion({
                    "comando": "cargar_dinero",
                    "monto": monto
                })
            else:
                QMessageBox.warning(self, "Error", "No hay conexión "
                                                   "con el servidor.")

    def mostrar_error_ingreso(self, motivo):
        QMessageBox.warning(self, "Ingreso Fallido",
                            f"No se pudo ingresar a la sala.\n"
                            f"Motivo: {motivo}")

    def mostrar_exito_carga(self, monto):
        QMessageBox.information(self, "Carga Exitosa",
                                f"Se han cargado <b>${monto}</b> a "
                                f"tu cuenta correctamente.")

    def mostrar_error_carga(self, motivo):
        QMessageBox.warning(self, "Carga Rechazada", motivo)