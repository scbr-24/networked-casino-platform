import threading
import requests
import time
import parametros


class ProcesadorInstrucciones:


    def __init__(self, servidor):
        self.servidor = servidor

    def procesar(self, instruccion, ccs):
        if not isinstance(instruccion, dict):
            print(f"[ADVERTENCIA] Se recibió un objeto que no es dict:"
                  f"{type(instruccion)}")
            return

        accion = instruccion.get("comando")

        if accion == "login_request":
            thread_login = threading.Thread(
                target=self._procesar_login, args=(instruccion, ccs),
                daemon=True)
            thread_login.start()

        elif accion == "cargar_dinero":
            self._manejar_carga_dinero(instruccion, ccs)

        elif accion == "solicitar_stats":
            self._manejar_stats(ccs)

        # Instrucciones BlackJack

        elif accion == "ingresar_blackjack":
            if ccs.nombre_usuario:
                exito, motivo = self.servidor.blackjack.agregar_jugador(
                    ccs.nombre_usuario, ccs.saldo)
                if exito:
                    self.servidor.enviar_objeto_cliente(
                        {"comando": "ingreso_blackjack_exitoso"}, ccs)
                else:
                    self.servidor.enviar_objeto_cliente(
                        {"comando": "ingreso_fallido", "motivo":
                            "Sala llena o ya estás adentro"},
                        ccs)

        elif accion == "apostar_blackjack":
            self._manejar_apuesta_blackjack(instruccion, ccs)

        elif accion == "cancelar_apuesta_blackjack":
            if ccs.nombre_usuario:
                exito, resultado = self.servidor.blackjack.cancelar_apuesta(
                    ccs.nombre_usuario)
                if exito:
                    ccs.saldo += resultado
                    self.servidor.enviar_objeto_cliente({
                        "comando": "apuesta_cancelada",
                        "nuevo_saldo": ccs.saldo
                    }, ccs)
                    print(f"[BLACKJACK] Apuesta cancelada "
                          f"{ccs.nombre_usuario}")

        elif accion == "accion_blackjack":
            tipo = instruccion.get("tipo")
            if ccs.nombre_usuario and tipo:
                self.servidor.blackjack.manejar_accion(ccs.nombre_usuario,
                                                       tipo)

        elif accion == "salir_blackjack":
            if ccs.nombre_usuario:
                saldo_final = self.servidor.blackjack.remover_jugador(
                    ccs.nombre_usuario)
                if saldo_final is not None:
                    ccs.saldo = saldo_final
                    self.servidor.enviar_objeto_cliente({
                        "comando": "actualizar_saldo",
                        "nuevo_saldo": ccs.saldo
                    }, ccs)
                    print(f"[SERVER] {ccs.nombre_usuario} salió de Blackjack.")

        # Instrucciones Aviator

        elif accion == "ingresar_aviator":
            if ccs.nombre_usuario:
                exito, lista_jugadores = (self.servidor.aviator.
                agregar_jugador(
                    ccs.nombre_usuario, ccs.saldo))
                if exito:
                    self.servidor.enviar_objeto_cliente({
                        "comando": "ingreso_aviator_exitoso",
                        "jugadores": lista_jugadores
                    }, ccs)
                else:
                    self.servidor.enviar_objeto_cliente(
                        {"comando": "ingreso_fallido",
                         "motivo": "Sala llena (Máx 3) o ya estás dentro"},
                        ccs)

        elif accion == "apostar_aviator":
            self._manejar_apuesta_aviator(instruccion, ccs)

        elif accion == "cancelar_apuesta_aviator":
            if ccs.nombre_usuario:
                exito, resultado = self.servidor.aviator.cancelar_apuesta(
                    ccs.nombre_usuario)
                if exito:
                    ccs.saldo += resultado
                    self.servidor.enviar_objeto_cliente({
                        "comando": "apuesta_cancelada",
                        "nuevo_saldo": ccs.saldo
                    }, ccs)
                    print(f"[AVIATOR] Apuesta cancelada {ccs.nombre_usuario}")

        elif accion == "retirar_aviator":
            if ccs.nombre_usuario:
                exito, ganancia = self.servidor.aviator.retirar_jugador(
                    ccs.nombre_usuario)
                if exito:
                    ccs.saldo += ganancia
                    self.servidor.enviar_objeto_cliente({
                        "comando": "retiro_aviator_exitoso",
                        "ganancia": ganancia,
                        "nuevo_saldo": ccs.saldo
                    }, ccs)

        elif accion == "salir_aviator":
            if ccs.nombre_usuario:
                saldo_final = self.servidor.aviator.remover_jugador(
                    ccs.nombre_usuario)
                if saldo_final is not None:
                    ccs.saldo = saldo_final
                    self.servidor.enviar_objeto_cliente({
                        "comando": "actualizar_saldo",
                        "nuevo_saldo": ccs.saldo
                    }, ccs)
                    print(f"[SERVER] {ccs.nombre_usuario} salió de Aviator.")

        else:
            print(f"Comando desconocido: {accion}")

    def _procesar_login(self, instruccion, ccs):
        nombre_usuario = instruccion.get("nombre_usuario").strip().upper()
        if nombre_usuario in self.servidor.clientes_activos:
            self.servidor.enviar_objeto_cliente({
                "comando": "login_fallido",
                "motivo": "El usuario ya está conectado"
            }, ccs)
            return

        url_base = f"http://{self.servidor.host}:{self.servidor.port_api}"

        try:
            respuesta_get = requests.get(f"{url_base}/users/{nombre_usuario}")
            saldo_usuario = 0
            if respuesta_get.status_code == 200:
                datos = respuesta_get.json()
                saldo_usuario = datos["saldo"]
                print(f"[LOGIN] Usuario encontrado: {nombre_usuario}, "
                      f"Saldo: {saldo_usuario}")
            elif respuesta_get.status_code == 404:
                print(f"[LOGIN] Usuario nuevo, registrando: {nombre_usuario}")
                headers = {"Authorization": parametros.TOKEN_AUTENTICACION}
                entregar = {"nombre_usuario": nombre_usuario}
                respuesta_post = requests.post(f"{url_base}/users",
                                               json=entregar,
                                               headers=headers)
                if respuesta_post.status_code == 200:
                    saldo_usuario = parametros.SALDO_INICIAL
                else:
                    self.servidor.enviar_objeto_cliente({
                        "comando": "login_fallido",
                        "motivo": "Error al registrar usuario nuevo"
                    }, ccs)
                    return
            else:
                self.servidor.enviar_objeto_cliente({
                    "comando": "login_fallido",
                    "motivo": f"Error interno (API: "
                              f"{respuesta_get.status_code})"
                }, ccs)
                return

            ccs.nombre_usuario = nombre_usuario
            self.servidor.clientes_activos[nombre_usuario] = ccs
            ccs.saldo = saldo_usuario
            self.servidor.enviar_objeto_cliente({
                "comando": "login_exitoso",
                "nombre_usuario": nombre_usuario,
                "saldo": saldo_usuario
            }, ccs)
        except requests.exceptions.RequestException as e:
            print(f"[ERROR LOGIN] Fallo de conexión con la API: {e}")
            self.servidor.enviar_objeto_cliente({
                "comando": "login_fallido",
                "motivo": "El servidor de datos no responde."
            }, ccs)

    def _manejar_carga_dinero(self, instruccion, ccs):
        monto = instruccion.get("monto")
        if ccs.nombre_usuario and monto:
            try:
                monto = int(monto)
                if monto > parametros.MONTO_MAXIMO_CARGA:
                    print(f"[SERVER] Carga rechazada: Excede "
                          f"máximo ({monto})")
                    self.servidor.enviar_objeto_cliente({
                        "comando": "carga_rechazada",
                        "motivo": f"El monto excede el máximo permitido "
                                  f"de ${parametros.MONTO_MAXIMO_CARGA}"
                    }, ccs)
                    return
                nuevo_saldo = ccs.saldo + monto
                if nuevo_saldo > parametros.SALDO_MAXIMO:
                    nuevo_saldo = parametros.SALDO_MAXIMO
                    print(f"[SERVER] Saldo tope alcanzado para {ccs.nombre_usuario}")

                url_base = f"http://{self.servidor.host}:{self.servidor.port_api}"
                headers = {"Authorization": parametros.TOKEN_AUTENTICACION}
                respuesta = requests.patch(
                    f"{url_base}/users/{ccs.nombre_usuario}",
                    json={"nuevo_saldo": nuevo_saldo},
                    headers=headers)

                if respuesta.status_code == 200:
                    ccs.saldo = nuevo_saldo
                    self.servidor.enviar_objeto_cliente({
                        "comando": "actualizar_saldo",
                        "nuevo_saldo": ccs.saldo
                    }, ccs)
                    self.servidor.enviar_objeto_cliente({
                        "comando": "carga_exitosa",
                        "monto": monto
                    }, ccs)
                    try:
                        requests.post(f"{url_base}/games/P",
                                      json={"resultados": {
                                          "nombre_usuario": ccs.
                                      nombre_usuario,
                                          "ganancia": int(monto),
                                          "timestamp": time.time()
                                      }},
                                      headers=headers)
                        self.servidor.notificar_actualizacion_estadisticas()
                    except:
                        print("[SERVER] Error guardando historial carga")
                    print(f"[SERVER] Carga exitosa para {ccs.nombre_usuario}: +${monto}")
                else:
                    print(f"[SERVER] Error API al cargar dinero: {respuesta.status_code}")
            except ValueError:
                print(f"[SERVER] Error: Monto inválido recibido de {ccs.nombre_usuario}")
            except requests.exceptions.RequestException as e:
                print(f"[SERVER] Error procesando carga de dinero: {e}")

    def _manejar_stats(self, ccs):
        url_base = f"http://{self.servidor.host}:{self.servidor.port_api}"
        try:
            resp = requests.get(f"{url_base}/games?n=5&user={ccs.nombre_usuario}")
            if resp.status_code == 200:
                stats = resp.json().get("resultados", [])
                self.servidor.enviar_objeto_cliente({
                    "comando": "actualizar_stats",
                    "resultados": stats
                }, ccs)
        except:
            pass

    def _manejar_apuesta_blackjack(self, instruccion, ccs):
        monto = instruccion.get("monto")
        if ccs.nombre_usuario and monto:
            monto = int(monto)
            exito, mensaje = self.servidor.blackjack.registrar_apuesta(
                ccs.nombre_usuario, monto)

            if exito:
                datos_jugador = self.servidor.blackjack.jugadores.get(
                    ccs.nombre_usuario)
                if datos_jugador is not None:
                    ccs.saldo = datos_jugador["saldo"]
                self.servidor.enviar_objeto_cliente({
                    "comando": "apuesta_aceptada",
                    "monto": monto,
                    "nuevo_saldo": ccs.saldo
                }, ccs)
                print(f"[BLACKJACK] Apuesta aceptada {ccs.nombre_usuario}: "
                      f"${monto}")
            else:
                self.servidor.enviar_objeto_cliente({
                    "comando": "apuesta_rechazada",
                    "motivo": mensaje
                }, ccs)
                print(f"[BLACKJACK] Apuesta rechazada {ccs.nombre_usuario}: "
                      f"{mensaje}")

    def _manejar_apuesta_aviator(self, instruccion, ccs):
        monto = instruccion.get("monto")
        if ccs.nombre_usuario and monto:
            exito, mensaje = self.servidor.aviator.registrar_apuesta(
                ccs.nombre_usuario, int(monto))
            if exito:
                ccs.saldo -= int(monto)
                self.servidor.enviar_objeto_cliente({
                    "comando": "apuesta_aceptada",
                    "monto": int(monto),
                    "nuevo_saldo": ccs.saldo
                }, ccs)
                print(f"[AVIATOR] Apuesta aceptada {ccs.nombre_usuario}: "
                      f"${monto}")
            else:
                print(f"[AVIATOR] Apuesta RECHAZADA {ccs.nombre_usuario}: "
                      f"{mensaje}")
                self.servidor.enviar_objeto_cliente({
                    "comando": "apuesta_rechazada",
                    "motivo": mensaje
                }, ccs)