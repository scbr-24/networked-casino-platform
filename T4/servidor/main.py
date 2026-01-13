import time
import sys
from logica_servidor import Servidor


if __name__ == "__main__":

    server = Servidor()

    print("Servidor inicializado. Presione Ctrl+C para detener.")

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[CIERRE] Señal de interrupción recibida. "
              "Cerrando servidor...")
        server.cerrar_servidor()
        sys.exit(0)