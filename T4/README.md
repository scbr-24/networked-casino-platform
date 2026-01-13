# Tarea 4: DCCasino


## Consideraciones generales 

En general, la tarea cumple con todos los aspectos solicitados por el Enunciado, excepto por la Ruleta.

## Ejecución 

Se mantiene la estructura del directorio sugerida en el Enunciado. El programa se ejecuta exclusivamente con la terminal ubicada en la raíz del proyecto (T4/), y con los siguientes comandos en distintas consolas, usando python3 y "/" para este ejemplo de referencia:
* python3 servidor/main.py
* python3 cliente/main.py

No funciona ejecutando los archivos directamente desde servidor/ o cliente/, ya que esto causa problemas con la importación de archivos en el proyecto. Notar que esta implementación fue vista en clases y/o ayudantías al ver los contenidos de networking. 

Por otra parte, es necesario que la carpeta Assets/ esté en T4/cliente/. El programa NO funciona sin este recurso en la ubicación mencionada.

## Directorio 

    |-T4/
    |   |
    |   |-cliente/
    |   |   |
    |   |   |-Assets/
    |   |   |   |
    |   |   |   |-Aviator/
    |   |   |   |   | ...png
    |   |   |   |-Blackjack/
    |   |   |   |   | ...png
    |   |   |   |-Ruleta/
    |   |   |   |   | ...png
    |   |   |   |
    |   |   |-backend/
    |   |   |   |
    |   |   |   |-conexion.json
    |   |   |   |-conexion.py
    |   |   |   |-logica_cliente.py
    |   |   |   |-protocolo.py
    |   |   |   |
    |   |   |-frontend/
    |   |   |   |
    |   |   |   |-auxiliar_blackjack.py
    |   |   |   |-auxiliar_aviator.py
    |   |   |   |-v_aviator.py
    |   |   |   |-v_blackjack.py
    |   |   |   |-ventanas_e_p.py
    |   |   |   |
    |   |   |-main.py
    |   |   |-parametros.py
    |   |   |
    |   |-servidor/
    |   |   |
    |   |   |-database/
    |   |   |   |
    |   |   |   |-auxiliar_database.py
    |   |   |   | * Aquí se guardan archivos .csv
    |   |   |   |
    |   |   |-juegos/
    |   |   |   |
    |   |   |   |-\__init__.py
    |   |   |   |-logica_aviator.py
    |   |   |   |-logica_blackjack.py
    |   |   |   |
    |   |   |-conexion.json
    |   |   |-api.py
    |   |   |-logica_servidor.py
    |   |   |-procesador.py
    |   |   |-main.py
    |   |   |-parametros.py
    |   |   |-protocolo.py
    |   |   |
    |   |-README.md
    |   |-.gitignore

## Cosas implementadas y no implementadas 

### Cliente: ✅
#### Ventana de Entrada: ✅
* Se incorporan elementos mínimos del enunciado, sin superposición.
* Aparece una ventana emergente en caso de tratar de hacer login con usuario ya conectado.
* If login exitoso, pasa a Ventana Principal
* Se envía el nombre del usuario conectado al Servidor.

#### Ventana Principal: ✅
* Se incorporan los elementos mínimos del enunciado, sin superposición. Se implementan con un layout distinto a la referencia del Enunciado, entendiendo que hay cierta liberta creativa mientras la ventana cumpla con los requerimientos mínimos exigidos.
* Se muestran las últimas 5 ganancias o pérdidas de los jugadores.
    * La lista se actualiza en tiempo real si es que algún jugador del servidor recibe una ganancia o pérdida.
    * Los resultados de rondas en los juegos (BlackJack y Aviator) generan ganancias o pérdidas, y dentro de estas ganancias, puede haber una ganancia neta positiva, o también una ganancia igual a cero en caso de haber empatado en el BlackJack. Hay una diferenciación de color para visualizar mejor los distintos tipos de resultados. Para más información, dirigirse a las líneas 284 - 296 de ventanas_e_p, en T4/cliente/frontend/.
* Se muestra el nombre de usuario y el saldo actual del jugador conectado.
    * Se toma una decisión de diseño, de manejar los nombres de usuario en mayúsculas. Al ingresar un nombre, se convierte a mayúsculas, se contrasta en este formato con los nombres existentes (también en mayúsculas), y, por último, se guarda así en el archivo usuarios.csv.
    * El motivo de la decisión es para tener mayor armonía visual en la Interfaz Gráfica. Generalmente, las minúsculas hacen que el programa se vea más... tosco.
* El botón de cargar dinero funciona de manera simple y cumple con la (ambigua) especificación del Enunciado. Se abre una ventana emergente desde la Ventana Principal donde el usuario puede ingresar un input para cargar dinero, monto que es contrastado y validado por el servidor, para luego ser guardado y visualizado en el frontend. Se implementaron límites máximos de carga de dinero y de saldo de jugadores. Estos se almacenan en parámetros.py. Si el usuario excede la carga máxima, se visualiza un mensaje y se niega la carga. Si el usuario llega al saldo máximo, este simplemente funciona como una cota superior (pensar en los $999.999.999 de Gta San Andreas), el resto del programa sigue funcionando con normalidad.
* Botones de juegos BlackJack y Aviator funcionan de manera correcta. Se niega el ingreso en caso de que la mesa esté jugando. Respecto a esto, hay que notar que, si bien en el Enunciado se declara la expulsión de jugadores por falta de saldo para realizar una apuesta mínima, no se menciona que esta restricción aplique también para ingresar a una sala de apuestas. Es decir, un jugador sin saldo puede ingresar a un juego, y en el caso del BlackJack, va a paralizar la mesa para el resto de jugadores. Esto es acorde al Enunciado, que no prohibe esta situación. En su lugar, se menciona en este README, para que quién corriga esta tarea lo tenga en cuenta a la hora de testear el programa (y cargue dinero al jugador sin saldo).A pesar de esto, los jugadores no quedan atrapados en la ventana, algo que se busca evitar según el Enunciado, ya que aún pueden volver a la ventana principal. Es decir, no se paraliza el flujo del programa.

#### Ventana de Recarga: ✅
* Como se mencionó anteriormente, se implementa la ventana emergente, restricciones a la carga de dinero, mensajes en la interfaz en caso de una carga demasiado alta, y también, lógicamente, la correcta implementación del nuevo saldo, validado por el servidor y visualizado en el frontend.

#### Inicio de Juego: ✅
* Tanto en BlackJack como en Aviator, se implementan todos los elementos solicitados por el Enunciado. Además, ambos juegos cumplen con las instrucciones relativas a la apuesta.
* BlackJack:
    * Se implementan 6 espacios vacíos donde las cartas podrán aparecer para cada jugador, y para el dealer. Notar que, por la lógica del mazo infinito con repetición, sería posible que los 6 espacios vacíos se queden cortos, y que, en la sexta carta de un jugador, este aún no tenga 21 puntos, por lo que tendría que seguir pidiendo cartas. En ese caso, las cartas desde la séptima en adelante, no se van a mostrar, pero la lógica interna será correcta, y es la misma por la cual se determinan los resultados con 6 cartas o menos. 
    
    Esta limitación se da por el espacio en pantalla y también por la complejidad que se espera en la tarea. En un juego online de BlackJack real, los mazos son finitos y, por ejemplo, si el juego funcionara con un mazo, entonces la máxima cantidad de cartas que un jugador podría tener serían 6, ya que obteniendo las cartas de menor valor posible, sumaría 1 + 2 + 3 + 4 + 5 + 6 = 21, llegando al límite de puntaje. 

    En la implementación de esta tarea, la simplificación del mazo respecto a un BlackJack real, tiene como consecuencia este caso borde en donde la Interfaz no representa correctamente las cartas de un jugador. Las alternativas hubieran sido, o agregar más espacios disponibles a los mazos para hacer más improbable que este caso llegue a suceder, o implementar una solución en donde las cartas se van apilando una encima de otra. Descartando esta segunda opción por su alta complejidad, y la primera opción por no agregar demasiado valor a la Interfaz, y, de hecho, haciéndola menos atractiva, se decidió mantener los 6 espacios disponibles, declarando en este README la situación, en caso de que, por mala suerte, llegue a ocurrir en la corrección que un jugador tenga 7 cartas. Este caso tiene una probabilidad aproximada de 1/5000 de ocurrir. 
    * Se implementan también las etiquetas de jugadores que muestran sus nombres de usuario, el botón de volver, salir, apostar, cancelar, pedir carta, y de plantarse. Además, se implementa un texto dinámico que muestra la apuesta actual del jugador en esa ronda, junto a su saldo. Por último, también aparece el nombre de usuario del jugador en el título de la ventana.
* Aviator: 
    * Se implementa la sección de datos de jugadores, en donde aparecen los nombres de usuario de jugadores que se van uniendo a la sala de espera, sin límite, de acuerdo al enunciado. Una vez que hay 3 apuestas, se echa a los jugadores que no apostaron, y permanecen los que sí lo hicieron. Se muestra su apuesta y, al final de la ronda, se muestra cuánto retiran y su ganancia neta. Estos datos se reinician al comenzar la siguiente fase de apuestas.
    * Se implementa un cuadro de texto dinámico que dice Periodo de Apuestas en el periodo respectivo, y que también va mostrando el tiempo de ronda actual cuando el avión comienza a volar.
    * Se implementa el botón para volver al menú principal, y también la sección gráfica del avión. En esta sección, se va actualizando el multiplicador y, al momento del choque, se muestra el resultado para el jugador de esa ventana. Esta visualización del resultado es permanente hasta la siguiente etapa de vuelo. La decisión es intencional, ya que es más cómodo tener visible el resultado de la ronda anterior, sin límite de tiempo (con tope hasta la siguiente fase de vuelo), que tener que regresar a la ventana principal para ver el último resultado. 
    * Se implementa el sistema de apuestas de acuerdo al enunciado. Hay un cuadro de texto con el saldo, un cuadro de input para ingresar la apuesta, y un botón para apostar. Una vez realizada la apuesta, el botón de apostar funciona como botón para cancelar la apuesta. Este botón, a su vez, funciona como botón para retirar el dinero en la etapa de vuelo.

#### Aviator ✅
* El tiempo de crash y el multiplicador utilizan la fórmula entregada en el enunciado. Los parámetros relevantes se almacenan en parametros.py. 
* La actualización de la posición del avión en el Widget gráfico, así como también el dinero multiplicado en cada instante (visualizado en el botón de retirar), se actualizan constantemente, y el camino del avión queda demarcado.
* Como se mencionó anteriormente, el jugador se puede retirar con el mismo botón de apuesta (el texto y función cambian dependiendo del contexto).
* Después del crash, se aplican los pagos respectivos y se visualizan los resultados de todos los jugadores de la ronda en la lista descrita anteriormente, a la izquierda de la ventana. En el Enunciado no se define una duración específica para ver los resultados, por lo que el valor es arbitrario e igual a 5 segundos.

#### BlackJack ✅
* Repartición de cartas sigue la especificación del Enunciado y de la pauta. La repartición inicial (primera y segunda) es de 2 cartas por jugador y para el dealer, una visible para todos, y una privada (visible solo para cada uno).
* La tercera repartición es por turno, según quién entró a la ventana de BlackJack primero. En este turno, por jugador, este puede pedir cartas hasta que supere 21, o plantarse (pasar). Si se pasa de 21, el jugador pierde pero queda esperando los resultados de la mesa completa. Se implementan las condiciones de pago (pierde, se devuelve la apuesta, o gana) de acuerdo al Enunciado.
* La repartición del Dealer también sigue las reglas del Enunciado.
* Después de la repartición del Dealer, se evalúan y muestran los resultados en pantalla a todos los jugadores por 6 segundos.

#### Fin de Juego ✅
* Como se mencionó, es posible repetir la ronda reseteando la mesa y volviendo a la fase de apuestas en el caso de BlackJack, e implementando los pagos correspondientes. 
* En el caso del Aviator funciona de la misma forma, pero por conveniencia para el usuario, los resultados de la ronda anterior (NO la tabla de jugadores, sino que el resultado de cada jugador en su ventana, en el área del avión) permanencen en la ventana hasta que finalice la siguiente fase de apuestas, en donde los resultados se reemplazan por el avión volando.

### Bonus ❌
#### Ruleta ❌
* No se implementa la Ruleta. Existe el botón en la ventana principal, que se muestra y se declara que está inactivo, pero nada más.

### Networking ✅
#### Networking general ✅
* Correcto uso de TCP/IP
* Correcto uso de sockets.
* El servidor sigue funcionando si es que un cliente se desconecta. Los programas de los clientes se cierran si es que se desconecta el servidor.

#### Codificación y Decodificación ✅
* Se envía el largo del contenido y luego el contenido en Chunks.
* Se respetan los valores correctos de largo de contenido, números de paquetes y cantidad de bytes en el contenido.
* Se rellena con ceros correctamente.
* Se usa el XOR sobre el paquete antes de enviarlo.
Se recibe y obtiene correctamente el objeto desde los bytes.

### Funcionalidades Servidor ✅
#### Inicio Sesión ✅
* El servidor verifica el nombre de usuario de acuerdo a las especificaciones. Como se mencionó anteriormente, todo lo relativo a nombres de usuario se hace en mayúsculas. Si el usuario ingresa un nombre en minúsculas o capitalizado, se convierte a mayúsculas. Se contrasta con otros nombres en el csv de esta forma, y se guarda también en mayúsculas. El motivo es estético, ya que las minúsculas no se ven bien en las ventanas de juego al mostrar los nombres de usuario.

#### Administración de Partidas ✅
* El servidor tiene una única sala de juego por cada juego, y ambas salas (de cada juego) pueden funcionar en paralelo.
* El servidor diferencia entre las etapas de cada juego, y el estado se puede visualizar en la GUI. En BlackJack, por ejemplo, el título de la ventana cambia dependiendo de si el juego está en fase de apuestas o en mitad de un juego. Al mismo tiempo, en la fase de resultados, los resultados son visibles para todos los jugadores. Está lógica está en el servidor.
* El servidor diferencia entre apostadores y no apostadores. En Aviator, se implementa la lógica de permitir infinitos usuarios y, al alcanzar 3 apuestas, eliminar de la sala a los que no apostaron. Esta lógica NO se implementa en el BlackJack porque no es requerido según el Enunciado. Se explicita únicamente para el Aviator: "Si el jugador no realizó una apuesta durante el periodo anterior, el jugador es enviado a la
ventana principal inmediatamente". 
* Parámetros de juego en parametros.py del server, manejados y validados en el Servidor. 
* El servidor controla correctamente las dinámicas necesarias para que el juego funcione. Retiros, desconexiones, solicitud de cartas, plantarse (pasar de turno), etc.

#### Durante la partida ✅
* El servidor calcula ganancias o pérdidas y las envía al cliente.
* El servidor modifica las bases de datos respectivas de acuerdo al Enunciado.

#### WebServices ✅
* El servidor utiliza correctamente los end points de /users y /games.
* El servidor no modifica los .csv manualmente. Utiliza requests a la API.

### WebServices ✅
* Las funciones de cada EndPoint se implementan de acuerdo a la pauta y al Enunciado.
* Se asegura la integridad de los archivos implementando threads en el archivo auxiliar de la API (archivo que contiene las funciones que manejan las bases de datos).

### Archivos ✅
* Se respeta la organización mínima del directorio expuesta en el Enunciado.
* Se implementa correctamente el archivo conexion.json.
* Se implementa correctamente el archivo parametros.py. El archivo de parámetros del cliente NO contiene el token de autenticación, según la instrucción del Enunciado.

## Descuentos ✅
* Como se describe al inicio de este README, la estructura de archivos es la del Enunciado, y se indica claramente los archivos necesarios y la ubicación de Assets/ requerida para el funcionamiento del programa.
* Se respetan normas de PEP8. 
    * Límite de 80 carácteres por línea, más estricto que el límite de la pauta, y acorde a las normas PEP8 reales.
    * Variables declarativas y aclarativas o, en su defecto, anotaciones.
    * CamelCase y snake_case.
    * Espacios después de la coma.
    * Espacios para indentación.
    * Imports manejados correctamente:
        * import "_"
        * from "_" import "_", ...
        * NO se utilizan from "_" import *
    * Se respetan las normas de saltos de líneas. Una línea entre funciones o métodos, dos líneas antes y después de definir una clase (a menos que una de las líneas posteriores sea una anotación, en cuyo caso es solo una línea después de la definición).
* Correcto uso de .gitignore.
* Se respetan las 400 líneas máximas por archivo.
* Se respetan buenas prácticas:
    * Paths relativos
    * No se usan except Exceptions.



## Librerías
### Librerías externas utilizadas
La lista de librerías externas que utilicé fue la siguiente:

1. Módulos de `PyQt5`: 
    * QtCore: 
        * pyqtSignal
        * Qt
        * QTimer
        * QObject
        * QRectF
        * QPointF
    * QtWidgets:
        * QApplication
        * QMessageBox
        * QWidget
        * QLabel
        * QPushButton
        * QVBoxLayout
        * QHBoxLayout
        * QDesktopWidget
        * QLineEdit
        * QSizePolicy
        * QInputDialog
        * QListWidget
        * QListWidgetItem
        * QGraphicsView
        * QGraphicsViewRectItem
        * QGraphicsTextItem
        * QGraphicsRectItem
        * QGraphicsSceneMouseEvent
        * QMainWindow
        * QFrame
        * QScrollArea
        * QGraphicsScene
        * QGraphicsPixmapItem
        * QGraphicsPathItem
    * QtGui:
        * QColor
        * QPainter
        * QFont
        * QPen
        * QBrush
        * QPainterPath
        * QPixmap
2. `flask`:
    * Flask
    * jsonify
    * request
    * Response
3. `functools`:
    * wraps
4. `os`:
    * path
5. `os.path`:
    * join
    * dirname
6. `pathlib`:
    * Path
7. `threading`
8. `sys`
9. `pickle`
10. `json`
11. `socket`
12. `random`
13. `math`
14. `time`
15. `requests`
16. Además, se importan los propios archivos del proyecto entre sí, cuando corresponde y evitando importaciones circulares.

### Librerías propias
Por otro lado, los módulos que fueron creados fueron los siguientes:

1. ```protocolo.py```: Módulo encargado de la codificación, serialización y encriptación de mensajes entre el cliente y el servidor.
2. ```auxiliar_database.py```: Módulo del servidor que gestiona las modificaciones a los archivos .csv, y es utilizado por ```api.py```.
3. ```api.py```: WebServices de Flask.
4. ```auxiliar_blackjack``: Módulo del cliente que se encarga del apartado gráfico y de los widgets personalizados para el juego.
5. ```auxiliar_aviator```: Análogo para del item anterior.
6. ```procesador```: Procesa instrucciones de ```logica_servidor.py```. 

## Supuestos y consideraciones adicionales :thinking:
Los supuestos que realicé durante la tarea son los siguientes:

1. La carpeta de Assets/ se encuentra en T4/cliente/.
2. La ejecución del programa se realiza ejecutando los archivos main.py desde la carpeta T4/, NO desde las carpetas cliente/ y servidor/.
3. No se niega el acceso a los juegos, a jugadores sin saldo suficiente para la apuesta mínima, ya que esta no es una restricción del Enunciado. Lo que sí se implementa, es la instrucción que sí se menciona, de expulsar a los jugadores que, estando dentro de una sala de juego, se quedan sin saldo después de perder su apuesta. 
4. La lógica de jugadores infinitos y que el programa diferencia entre apostadores y no apostadores (echando a los no apostadores cuando empieza el juego), se implementa para el Aviator y NO para el BlackJack, ya que el Enunciado explicita el comportamiento solo para el Aviator. En BlackJack se implementa una lógica de que el juego / la sala espere la conexión de 4 usuarios y limite la entrada a nuevos usuarios cuando alcance este número. Una vez que los 4 apuestan, comienza el juego. Hay que recalcar que este supuesto se hace únicamente por la ambiguedad del Enunciado. Se entiende que si entrega una instrucción explícita y específica sobre el comportamiento del Aviator, y NO sobre el BlackJack, entonces no se espera que se implemente este comportamiento en ambos juegos. En ese sentido, me excuso ante un posible descuento en el puntaje del item correspondiente, ya que la lógica está implementada en el Aviator tal como se pide en el Enunciado, y la decisión de no implementarla en BlackJack no es una omisión accidental o por no saber implementar la función, sino que es una decisión intencional frente a la interpretación subjetiva que se puede hacer sobre el Enunciado.


### Consideraciones adicionales

* Al ejecutar múltiples clientes a la vez, ocurre algo que podría considerarse un bug visual, pero desconozco si es por motivo de mi código, de Python o de mi sistema operativo. Por ejemplo, al ejecutar los 4 jugadores en una mesa de BlackJack, al mover el mouse por las ventanas de los clientes en la barra del dock en el sistema, sin presionarlas, todas muestran la misma previsualización (de un solo cliente). Esto podría causar la impresión de que las 4 ventanas son iguales. No lo son. Al presionar cada una por separado, se abren clientes distintos, lógicamente, a pesar de que en la preview, aparezcan como la misma instancia.


-------


## Referencias de código externo :book:

Para realizar mi tarea saqué código de:
1. Mi propia entrega de la T3, donde reciclé parte de la estructura del código de las ventanas de entrada y ventana principal: funciones que llamo en el init, funciones que llamo en el método inicializa_gui, que este último llame a los métodos para crear widgets, para aplicar estética, para centrar la ventana en la pantalla, etc. Copié parcialmente la forma en que estructué las clases y métodos respectivos donde esto fue posible, y también copíe 1:1 el método para centrar la ventana en la pantalla. 
