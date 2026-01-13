import time
from os import path
import threading
import parametros

base_de_datos_lock = threading.Lock()
usuarios = parametros.USUARIOS_PATH
saldo = parametros.SALDO_INICIAL

def obtener_usuario(nombre_usuario):
    # Busca usuario en csv, retorna sus datos
    # nombre_usuario, timestamp, saldo_actual
    if not path.exists(usuarios):
        return None # No existe archivo -> no existe usuario

    with base_de_datos_lock:
        with open(usuarios, "r", encoding = "utf-8") as archivo:
            for linea in archivo:
                linea = linea.strip()
                if not linea:
                    continue
                try:
                    separada = linea.split(",")
                    nombre, timestamp, saldo = separada

                    if nombre_usuario == nombre:
                        return {
                            "nombre_usuario": nombre,
                            "timestamp_creacion" : float(timestamp),
                            "saldo": int(saldo)
                        }
                except ValueError:
                    print(f"[ERROR BASE DE DATOS] Línea inválida en "
                          f"usuarios.csv: {linea}")
                    continue
    return None

def crear_usuario(nombre_usuario):
    # Registra un usuario en csv con el saldo inicial -> True
    if obtener_usuario(nombre_usuario) is not None:
        print(f"[BASE DE DATOS] El usuario ya existe: {nombre_usuario}")
        return False

    timestamp_actual = time.time()
    linea_usuario = (f"{nombre_usuario},{timestamp_actual},{saldo}\n")

    with base_de_datos_lock:
        try:
            with open(usuarios, "a", encoding = "utf-8") as archivo:
                archivo.write(linea_usuario)
            return True
        except (IOError, OSError) as e:
            print(f"[ERROR BASE DE DATOS] No se pudo escribir en "
                  f"usuarios.csv: {e}")
            return False

def actualizar_usuario(nombre_usuario, nuevo_saldo):
    # Actualiza el saldo de un usuario -> True
    if not path.exists(usuarios):
        return False # no hay archivos
    with base_de_datos_lock:
        lineas_actualizadas = []
        encontrado = False
        try:
            with open(usuarios, "r", encoding = "utf-8") as archivo:
                for linea in archivo:
                    linea = linea.strip()
                    if not linea:
                        continue
                    separada = linea.split(",")
                    nombre = separada[0]
                    if nombre == nombre_usuario:
                        timestamp_creacion = separada[1]
                        linea_nueva = (f"{nombre_usuario},"
                                       f"{timestamp_creacion},"
                                       f"{nuevo_saldo}")
                        lineas_actualizadas.append(linea_nueva)
                        encontrado = True
                    else:
                        lineas_actualizadas.append(linea)

            if encontrado: # Se reescribe el archivo
                with open(usuarios, "w", encoding = "utf-8") as archivo:
                    archivo.write("\n".join(lineas_actualizadas) + "\n")
                return True
            else:
                print(f"[BASE DE DATOS] Usuario no encontrado: "
                      f"{nombre_usuario}")
                return False
        except IOError as e:
            print(f"[ERROR BASE DE DATOS] Fallo actualización: {e}")
            return False

def obtener_ultimas_ganancias(numero_registros = 3,
                              usuario_filtro = None):
    # Numero_registros -> cuantas ultimas ganancias/perdidas
    # Retorna lista -> letra_juego, nombre_usuario, timestamp_salida, monto
    ganancias = parametros.GANANCIAS_PATH
    if not path.exists(ganancias):
        return []

    with base_de_datos_lock:
        with open(ganancias, "r", encoding = "utf-8") as archivo:
            lineas = [linea.strip() for linea in archivo if linea.strip()]

    registros_recientes = []
    for linea in reversed(lineas):
        if len(registros_recientes) >= numero_registros:
            break
        try:
            separada = linea.split(",")
            juego, nombre, timestamp, monto = separada
            registros_recientes.append({
                "juego": juego,
                "nombre_usuario": nombre,
                "timestamp": float(timestamp),
                "monto": int(monto)
            })
        except ValueError:
            continue

    return registros_recientes

def registrar_juego(juego_id, datos):
    # datos: lista de dicts {nombre_usuario, ganancia, timestamp}
    # juego_id: A (Aviator), B (Blackjack), P (Penalidad/Carga)
    ganancias = parametros.GANANCIAS_PATH
    lineas_a_escribir = []
    if isinstance(datos, dict):
        datos = [datos]

    for d in datos: # d = dato
        nombre = d.get("nombre_usuario")
        timestamp = d.get("timestamp", time.time())
        monto = d.get("ganancia")  # Puede ser positivo o negativo

        if nombre and monto is not None:
            linea = f"{juego_id},{nombre},{timestamp},{monto}\n"
            lineas_a_escribir.append(linea)

    with base_de_datos_lock:
        try:
            with open(ganancias, "a", encoding="utf-8") as archivo:
                archivo.writelines(lineas_a_escribir)
            return True
        except (IOError, OSError) as e:
            print(f"[ERROR BASE DE DATOS] No se pudo escribir en "
                  f"ganancias.csv: {e}")
            return False