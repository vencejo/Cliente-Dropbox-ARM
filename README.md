Cliente-Dropbox-para-Raspberry-Pi
=================================

Ciente Dropbox para Raspberry PI

### Resumen:

Mantiene sincronizada una carpeta local de la Raspberry con una carpeta remota
en dropbox.


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

d = {'ruta':'/',
         'archivos': [{'ruta':'/home',
                       'archivos':[],
                       'tipo':'directorio',
                       'tiempo':30000}],
         'tiempo': 10000000,
         'tipo': 'directorio'}
         
### TODO:

* POO
* Cuando se ha borrado un elemento en dropbox estando la Rasp apagada, 
al encenderla si descarga los nuevos elementos, 
pero no borra del local el elemento borrado en dropbox
* Hay problemas cuando creo una carpeta en remoto con tildes en su nombre
* Implementar un limitador de la cantidad de subidas y bajadas
* Gestion de errores
