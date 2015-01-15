Cliente-Dropbox-ARM
===================

Ciente Dropbox para arquitecturas ARM (Raspberry Pi, CubieBoards, etc ...)

### Resumen:

Mantiene sincronizada una carpeta local del ARM  con una carpeta remota
en dropbox.

### Instalacion:

0. Has de instalar el modulo Dropbox SDK para Python con la sentencia
	'sudo pip install dropbox'
	
1. Evidentemente tienes que crearte una cuenta Dropbox

2. Luego tienes que informar a Dropbox de que una de tus aplicaciones
va a acceder a esta cuenta para lo que tienes que ir a 
la pagina de apps de Dropbox [https://www.dropbox.com/developers/apps] 
y pinchar en 'create app' , tendras que elegir si quieres que 
tu aplicacion tenga un acceso completo  a todo tu Dropbox o solo a una carpeta 
y has de marcar el 'access type' como 'Dropbox'

3. Con la 'app_key' y la 'app_secret' que obtienes en el paso anterior tienes que
rellenar los campos correspondientes en el archivo 'datosDeTrabajo.ini'

4. Tambien debes  poner en 'datosDeTrabajo.ini' las rutas de las carpetas
locales y remotas que vas a sincronizar con Dropbox

5. Tras esto ya puedes ejecutar el programa, que se pondra en contacto con 
Dropbox para que este autorice a la maquina con las que estas trabajanco a 
acceder a tu aplicacion. Para ello hay que copiar en un navegador la direccion
que te dara el programa en la terminal, una vez visitada esta direccion, Dropbox ya esta al tanto
de que esta maquina esta asociada con tu app y puedes darle al intro en el terminal
y el programa se descargara el 'AccessToken' que guardara en un archivo de texto 
y que servira como llave para futuros accesos a la aplicacion sin necesidad de 
repetir estos cinco pasos
 
### Modo de funcionamiento:

1. Al encender la Raspberry hace un escaneado de la estructura de carpetas remota.

2. Compara la estructura remota con la estructura local

3. Si hay diferencias en las estructuras se procede a la actualizacion de los archivos y
carpetas locales guiandose por la info remota y se toma la info remota como cache local

4. Se entra en un ciclo de doble vigilancia:

5. Por una parte el programa vigila los cambios de las carpetas locales y si se produce
alguno procede a actualizar su cache local y a subir el archivo/carpeta

6. Por otra parte el programa tambien vigila los cambios en una carpeta remota
(solo en una, porque vigilar todo el directorio remoto seria demasiado lento)
y si se produce algun cambio procede a actualizar la copia local de esta carpeta,
actulizando a su vez la cache local

### Implementacion:

La informacion sobre el arbol de carpetas y archivos , tambien denominado cache, 
se guarda en forma de archivo json con estructura recursiva del tipo siguiente

~~~
		d = {'ruta':'/',
			 'archivos': [{'ruta':'/home',
						   'archivos':[],
						   'tipo':'directorio',
						   'tiempo':30000}],
			 'tiempo': 10000000,
			 'tipo': 'directorio'} 
~~~
         
### Inspiraciones y agradecimientos:

A Hughdbrown y su elegante [Comparacion de diccionaros][1]

y a Vaslabs por su [Cliente Dropbox grafico][2]

[1]: https://github.com/hughdbrown/dictdiffer
[2]: http://sourceforge.net/projects/raspybox

### Probado en ...

* Raspberry Pi (Debian)
* CubieBoard  (Debian)

### TODO:

* Cuando se borran muchos archivos locales a la vez solo se borran unos pocos 
en Dropbox
* Cuando se suben muchos archivos locales al Dropbox falta informacion mostrada
por el cliente para saber lo que esta pasando
* Cuando se ha borrado un elemento en dropbox estando la Rasp apagada, 
al encenderla si descarga los nuevos elementos, 
pero no borra del local el elemento borrado en dropbox
* Hay problemas cuando creo una carpeta en remoto con tildes en su nombre
* Implementar un limitador de la cantidad de subidas y bajadas
* Implementar un registro de logs
* Gestion de errores
