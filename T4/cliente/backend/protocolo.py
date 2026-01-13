import pickle
import parametros

clave_casino = parametros.CLAVE_CASINO

tcc = parametros.tamano_chunk_contenido
tch = parametros.tamano_chunk_header
tamano_paquete = tcc + tch

def operacion_xor(data):
    # desencripta
    return bytes([byte ^ llave for byte, llave in zip(data, clave_casino)])

def codificar_mensaje(data):

    # Serializacion
    msj_serializado = pickle.dumps(data)
    largo_original = len(msj_serializado)
    ultimo_chunk = largo_original % tcc
    diferencia = (
                tcc - ultimo_chunk) if ultimo_chunk != 0 else 0
    ajuste = b"\x00" * diferencia
    msj_final = msj_serializado + ajuste

    # Chunks, Header, Encriptacion
    paquetes_encriptados = bytearray()
    numero_paquetes = len(msj_final) // tcc
    for _ in range(numero_paquetes):
        inicio = _ * tcc
        fin = inicio + tcc
        chunk_contenido = msj_final[inicio:fin]
        numero_paquete_bytes = _.to_bytes(tch, byteorder='big')
        paquete_completo = numero_paquete_bytes + chunk_contenido  # 128 b
        paquete_encriptado = operacion_xor(paquete_completo)
        paquetes_encriptados.extend(paquete_encriptado)

    largo_original_bytes = largo_original.to_bytes(4,
                                                   byteorder='little')
    mensaje_final = largo_original_bytes + paquetes_encriptados
    return bytes(mensaje_final)

def decodificar_mensaje(datos):
    if len(datos) < 4:
        raise ValueError("Datos insuficientes para decodificar header.")
    # Recibe bytes, decodifica y desencripta msj recibido
    # Lee Header de 4 bytes en little endian
    largo_original_bytes = datos[0:4]
    largo_original = int.from_bytes(largo_original_bytes,
                                    byteorder='little')

    paquetes_encriptados_bites = datos[4:]

    # Desencriptar, analizar n° de paquete y guardarlo
    num_paquetes = len(paquetes_encriptados_bites) // tamano_paquete
    paquetes_descifrados = {}  # {numero_de_chunk: contenido}

    for i in range(num_paquetes):
        inicio_paquete = i * tamano_paquete
        fin_paquete = inicio_paquete + tamano_paquete

        paquete_encriptado = paquetes_encriptados_bites[
            inicio_paquete:fin_paquete]
        paquete_descifrado = operacion_xor(paquete_encriptado)

        # Lee el chunk de 4 bytes en big endian
        numero_paquete_bytes = paquete_descifrado[0:tch]
        numero_paquete = int.from_bytes(numero_paquete_bytes,
                                        byteorder='big')

        # Obtiene el contenido de 124 bytes
        chunk_contenido = paquete_descifrado[tch:]

        paquetes_descifrados[numero_paquete] = chunk_contenido

    # Vuelve a unir el contenido
    contenido_con_ajuste = b"".join([
        paquetes_descifrados[i] for i in range(num_paquetes)])

    # Cambia el tamano de bytes con ajuste al len original
    contenido_serializado = contenido_con_ajuste[:largo_original]

    # Deserializar
    objeto_original = pickle.loads(contenido_serializado)

    return objeto_original

def calcular_total_paquetes(largo_original):
    numero_chunks = (largo_original + tcc - 1) // tcc
    return numero_chunks * tamano_paquete