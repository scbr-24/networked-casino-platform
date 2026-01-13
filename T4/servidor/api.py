from flask import Flask, jsonify, request, Response
from functools import wraps
import json

from database import auxiliar_database
import parametros

token = parametros.TOKEN_AUTENTICACION

def necesita_auth(f):

    @wraps(f)
    def decorada(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if auth_header != token:
            return Response(
                response = json.dumps({"error": "No Autorizado"}),
                status = 401,
                mimetype = "application/json"
            )
        return f(*args, **kwargs)
    return decorada

def crear_app(api_host, api_port):
    app = Flask(__name__)

    # ENDPOINTS PÚBLICOS

    # Get usuarios
    @app.route("/users/<string:nombre_usuario>", methods = ["GET"])
    def obtener_usuario(nombre_usuario):
        datos_usuario = auxiliar_database.obtener_usuario(nombre_usuario)
        if datos_usuario:
            return jsonify({
                "nombre_usuario": datos_usuario["nombre_usuario"],
                "saldo": datos_usuario["saldo"]
            }), 200
        else:
            return jsonify({"error": "Usuario no encontrado"}), 404

    # Get juegos
    @app.route("/games", methods = ["GET"])
    def obtener_juegos():
        # Últimas N gananciaso pérdidas, por defecto N = 3
        try:
            n_registros = request.args.get("n", default = 5, type = int)
            if n_registros <= 0:
                return jsonify({"error": "Parámetro N negativo"}), 400
        except ValueError:
            return jsonify({"error": "Parámetro N inválido"}), 400

        resultados = auxiliar_database.obtener_ultimas_ganancias(n_registros)
        return jsonify({"resultados": resultados}), 200

    # ENDPOINTS PRIVADOS

    # Post (crear) usuario
    @app.route("/users", methods = ["POST"])
    @necesita_auth
    def crear_usuario():
        # Registra info de usuario en base de datos
        datos = request.get_json()
        nombre_usuario = datos.get("nombre_usuario")

        if not nombre_usuario:
            return jsonify({"erorr": "Falta el nombre de usuario "
                                     "en el body"}), 400
        if auxiliar_database.crear_usuario(nombre_usuario):
            return jsonify({"status": "Usuario creado exitósamente"}), 200
        else:
            return jsonify({"error": "Usuario ya existe o error "
                                     "en base de datos"}), 400

    # Patch (actualizar) usuario
    @app.route("/users/<string:nombre_usuario>", methods=["PATCH"])
    @necesita_auth
    def actualizar_usuario(nombre_usuario):
        datos = request.get_json()
        nuevo_saldo = datos.get("nuevo_saldo")
        if nuevo_saldo is None:
            return jsonify({"error": "Falta 'nuevo_saldo' en el body"}), 400
        try:
            nuevo_saldo = int(nuevo_saldo)
        except ValueError:
            return jsonify({"error": "'nuevo_saldo' debe ser entero"}), 400
        if auxiliar_database.actualizar_usuario(nombre_usuario, nuevo_saldo):
            return jsonify({"status": "Balance actualizado exitósamente"}), 200
        else:
            return jsonify({"error": "Usuario ya existe o error "
                                     "en base de datos"}), 400

    # Post (crear) info juego
    @app.route("/games/<string:juego_id>", methods=["POST"])
    @necesita_auth
    def registro_resultado_juego(juego_id): # id: Letra
        datos = request.get_json()
        resultados = datos.get("resultados") # Esperamos una lista o dict
        if not resultados:
             return jsonify({"error": "Faltan resultados"}), 400
        if auxiliar_database.registrar_juego(juego_id, resultados):
            return jsonify({"status": "Juego registrado exitosamente"}), 200
        else:
            return jsonify({"error": "Error al escribir en CSV"}), 500
    return app
