"""
CLIENTE dropbox PARA RASPBERRY PI

## Resumen:

Mantiene sincronizada una carpeta local de la Raspberry con una carpeta remota
en dropbox.


## Modo de funcionamiento:

1- Al encender la Raspberry hace un escaneado de la estructura de carpetas remota.

2- Compara la estructura remota con la estructura local

3- Si hay diferencias en las estructuras se procede a la actualizacion de los archivos y
carpetas locales guiandose por la info remota y se toma la info remota como cache local

4- Se entra en un ciclo de doble vigilancia:

4.1- Por una parte el programa vigila los cambios de las carpetas locales y si se produce
alguno procede a actualizar su cache local y a subir el archivo/carpeta

4.2- Por otra parte el programa tambien vigila los cambios en una carpeta remota
(solo en una, porque vigilar todo el directorio remoto seria demasiado lento)
y si se produce algun cambio procede a actualizar la copia local de esta carpeta,
actulizando a su vez la cache local

## Implementacion:

La informacion sobre el arbol de carpetas y archivos , tambien denominado cache, 
se guarda en forma de archivo json con estructura recursiva del tipo siguiente

d = {'ruta':'/',
         'archivos': [{'ruta':'/home',
                       'archivos':[],
                       'tipo':'directorio',
                       'tiempo':30000}],
         'tiempo': 10000000,
         'tipo': 'directorio'}
         
## TODO:
0- Cuando se ha borrado un elemento en dropbox estando la Rasp apagada, al encenderla
	si descarga los nuevos elementos, pero no borra del local el elemento borrado en dropbox

1- Hay problemas cuando creo una carpeta en remoto con tildes en su nombre
2- Implementar un limitador de la cantidad de subidas y bajadas
3- Gestion de errores
4- POO

"""

import os
import stat
import time
import myDropbox
import json
from dictDiff import DictDiff
from threading import Timer
import datetime

RUTA_BASE_LOCAL = "/home/pi/Desktop/ClienteDropbox/Nube"
RUTA_BASE_REMOTA = "/Nube"

COPIA_LOCAL_INFO_LOCAL = "/home/pi/Desktop/ClienteDropbox/Programa/copiaLocalInfoLocal.json"

COPIA_LOCAL_INFO_REMOTA = "/home/pi/Desktop/ClienteDropbox/Programa/copiaLocalInfoRemota.json"

#Conexion a Dropbox
dropbox = myDropbox.connect()

#Cambio el directorio de trabajo
os.chdir(RUTA_BASE_LOCAL)
rutaAraiz = os.getcwd()

def preparaRuta(ruta, donde = 'local'):
	""" Dada una ruta  devuelve la ruta que ha de tener en la ambiente gemelo.
		Si la ruta es local , devuelve su contrapartida en dropbox
		y si la ruta es de dropbox (donde='nube') devuelve la ruta local del elemento"""
	if donde == 'local':
		rutaLocal = RUTA_BASE_LOCAL + ruta
		return rutaLocal
	else:
		rutaRelativaDeSubida = ruta.replace(RUTA_BASE_LOCAL,'')
		rutaDeSubida = RUTA_BASE_REMOTA + rutaRelativaDeSubida
		return rutaDeSubida
		
def guardaInfoArchivos(infoArchivosyCarpetas, rutaArchivoDeRutas):
    """ Guarda la info de los archivos y carpetas en un json en memoria en la ruta
    especificada """
    with open(rutaArchivoDeRutas, 'w+') as archivo:
        json.dump(infoArchivosyCarpetas, archivo, sort_keys=True, indent=2)
    
def cargaInfoArchivos(rutaArchivoDeRutas):
    """ Carga la informacion del sistema de archivos en un diccionario,
    y lo devuelve """
    with open(rutaArchivoDeRutas, 'r') as archivo:
        info = json.load( archivo)
    return info

def vigilaArbol(donde = 'local'):
	""" Se encarga de ir vigilando el arbol remoto o local
	y si hay cambios actualiza su arbol gemelo, el local o el remoto """
	if donde == 'local':
		datosOriginalesGuardados = COPIA_LOCAL_INFO_LOCAL
		datosNuevosAguardar = COPIA_LOCAL_INFO_REMOTA
		rutaBase = RUTA_BASE_LOCAL
		laOtraRutaBase = RUTA_BASE_REMOTA
	else: #donde=='nube'
		datosOriginalesGuardados = COPIA_LOCAL_INFO_REMOTA
		datosNuevosAguardar = COPIA_LOCAL_INFO_LOCAL
		rutaBase = RUTA_BASE_REMOTA
		laOtraRutaBase = RUTA_BASE_LOCAL
		
	datosOriginales = cargaInfoArchivos(datosOriginalesGuardados) 
	datosNuevos = infoArchivosyCarpetas(rutaBase,donde) 
	df = DictDiff(datosNuevos, datosOriginales) 
	
	if len(df.borrados()) > 0 or len(df.nuevos()) > 0 or len(df.cambiados()) > 0 :
		elOtroDirectorio = 'nube' if donde == 'local' else 'local'
		actualiza(df, elOtroDirectorio)
		dic = infoArchivosyCarpetas(laOtraRutaBase, elOtroDirectorio  )
		guardaInfoArchivos(dic, datosNuevosAguardar)
		imprimeInfo(df)
				
	# Para facilitar el trabajo al recolector de basura
	# borro objetos innecesarios que podrian llenar la memoria
	del df
	guardaInfoArchivos(datosNuevos, datosOriginalesGuardados)

def imprimeInfo(df):
	""" Imprime la info del df """
	print ""
	print "********************************"
	print "borrados: " + str(df.borrados())
	print "nuevos: " + str(df.nuevos())
	print "cambiados: " + str(df.cambiados())
	print  "********************************"
	print ""
	
def actualiza(df, donde = 'local'):
	""" Actualiza el contenido del directorio local o remoto segun los valores del 
	DictDiff (df) """
	try:
		# Creacion de directorios 
		for e in df.nuevos():
			if df.dicRutas_actual[e].tipo == 'directorio':
				creaDirectorio(e, donde)
		# Creacion de archivos
		for e in df.nuevos():
			if df.dicRutas_actual[e].tipo == 'archivo':
				mueveArchivoHacia(e, donde)
		# borrado de archivos y directorios
		for e in df.borrados():
			borraArchivoOdirectorio(e, donde)
		# actualizacion de archivos cambiados
		for e in df.cambiados():
			if df.dicRutas_actual[e].tipo == 'archivo':
				borraArchivoOdirectorio(e, donde) # Borra el archivo  que esta desactualizado
				mueveArchivoHacia(e, donde)  # Actualiza el archivo 
				
	except Exception, e:
            print e
			
		
def mueveArchivoHacia(ruta, donde='local'):
	""" Mueve un archivo de la nube hacia la ruta del sistema local si donde='local'
	o lo mueve hacia el dropbox si donde='nube' """
	
	if donde == 'local':
		try:
			rutaLocal = preparaRuta(ruta, donde = 'local')
			dropbox.get(RUTA_BASE_REMOTA + ruta,rutaLocal)
		except Exception, e:
			print e, rutaRemota
					
	elif donde == 'nube':
		rutaRemota = preparaRuta(ruta, donde = 'nube')
		dropbox.put(RUTA_BASE_LOCAL + ruta,rutaRemota)
		
	else:
		print "Perdone, orden de movimiento del archivo no entendida"		
        
	

def borraArchivoOdirectorio(ruta, donde='local'):
	""" Borra un archivo en la ruta del sistema local si donde='local'
	y en dropbox si donde='nube' """
	
	if donde == 'local':
		rutaLocal = preparaRuta(ruta, donde = 'local')
		try:
			if os.path.isdir(rutaLocal):
				os.rmdir(rutaLocal)
			else:
				os.remove(rutaLocal)
		except Exception, e:
			print e , rutaLocal
			
	elif donde == 'nube':
		rutaRemota = preparaRuta(ruta, donde = 'nube')
		dropbox.rm(rutaRemota)
		
	else:
		print "Perdone, orden de borrado del archivo no entendida"
		
def creaDirectorio(ruta, donde='local'):
	""" Crea un directorio en la ruta del sistema local si donde='local'
	y en dropbox si donde='nube' """
	
	if donde == 'local':
		rutaLocal = preparaRuta(ruta, donde = 'local')
		try:
			os.mkdir(rutaLocal)
		except Exception, e:
			print e	
			
	elif donde == 'nube':
		rutaRemota = preparaRuta(ruta, donde = 'nube')
		dropbox.mkdir(rutaRemota)
		
	else:
		print "Perdone, orden de creacion del directorio no entendida"
	        
                      
def infoArchivosyCarpetas(ruta,donde = 'local', tipo = 'directorio' , tiempo = 0):
	""" Guarda la informacion del arbol de archivos y carpetas en un diccionario
	subceptible de ser pasado a json
	El diccionario devuelto tiene la forma recursiva siguiente:
	
	d = {'ruta':'/',
		 'archivos': [{'ruta':'/home',
					   'archivos':[],
					   'tipo':'directorio',
					   'tiempo':30000}],
		 'tiempo': 10000000,
		 'tipo': 'directorio'}
	"""	
	if donde == 'nube':
		d = {'ruta': ruta.replace(RUTA_BASE_REMOTA,'')}
		d['tipo'] = tipo
		d['tiempo'] = tiempo
		if tipo == 'directorio':
			d['archivos'] = [infoArchivosyCarpetas(os.path.join(ruta,x[0]),
				donde ='nube', tipo=x[1],tiempo=x[2]) for x in dropbox.ls(ruta)]
		return d 
	else:
		d = {'ruta': ruta.replace(RUTA_BASE_LOCAL,'')}
		fileStats = os.stat(ruta)
		d['tiempo'] = fileStats[stat.ST_MTIME]  #time.ctime(fileStats[.... para ver el tiempo en formato legible    
		if os.path.isdir(ruta):
			d['tipo'] = 'directorio'
			d['archivos'] = [infoArchivosyCarpetas(os.path.join(ruta,x), 
				donde='local') for x in os.listdir(ruta)]
		else:
			d['tipo'] = 'archivo'
							 
		return d


def subidaInicial(d):
    """ Realiza la subida inicial de archivos y directorios a la web tomando
    como argumento el diccionario que guarda la informacion de los archivos """
    if d == [] or d == None:
        return
    ruta = d['ruta']
 
    if d['tipo'] == 'directorio':     
        creaDirectorio(ruta, donde='nube') 
        for a in d.get('archivos'):
            subidaInicial(a)
    else:
        mueveArchivoHacia(ruta, donde='nube')

def descargaInicial(d,rutaLocal):
	
	try:
		
		if d == [] or d == None:
			return
		rutaRemota = d['ruta']
		rutaLocal = preparaRuta(rutaRemota, donde = 'local')
		
		if d['tipo'] == 'directorio':  
			if  not os.path.exists(rutaLocal):
				os.mkdir(rutaLocal)
			for a in d.get('archivos'):
				descargaInicial(a, rutaLocal)
		else:
			mueveArchivoHacia(rutaRemota, donde='local')
		
	except Exception, e:
		print e
		
class Vigila:
	"""Paso 4- Se entra en un ciclo de doble vigilancia:
		4.1- Por una parte el programa vigila los cambios de las carpetas locales y si se produce
			alguno procede a actualizar su cache local y a subir el archivo/carpeta
		4.2- Por otra parte el programa tambien vigila los cambios en una carpeta remota
			y si se produce algun cambio procede a actualizar la copia local de esta carpeta"""
	def __init__(self, cadaCuantoTiempo):
		self.cadaCuantoTiempo = cadaCuantoTiempo # Son segundos
		self.last_updated = None
		self.update()
		
	def update(self):
		print "Vigilando directorios locales ..."
		vigilaArbol(donde = 'local')
		print "Vigilando directorios remotos ..."
		vigilaArbol(donde = 'nube')
		self.last_updated = datetime.datetime.now()
		self.schedule()
		
	def schedule(self):
		self.timer = Timer(self.cadaCuantoTiempo, self.update)
		#self.timer.setDaemon(True)
		self.timer.start()
		
                          
if __name__ == "__main__":
	
	### Paso 0: Lo siguiente solo en la primera vez que se ejecute el programa en la Rasp
	if  not os.path.exists(COPIA_LOCAL_INFO_LOCAL) or not os.path.exists(COPIA_LOCAL_INFO_REMOTA): 
		print "Primera ejecucion del cliente ... descargando informacion remota "
		dic_remoto = infoArchivosyCarpetas(RUTA_BASE_REMOTA,donde = 'nube')
		guardaInfoArchivos(dic_remoto, COPIA_LOCAL_INFO_LOCAL)
		guardaInfoArchivos(dic_remoto, COPIA_LOCAL_INFO_REMOTA)
		descargaInicial(dic_remoto,RUTA_BASE_LOCAL)
	
	### Paso 1, 2 y 3: Se hacen cada vez que se arranca la Raspberry.
	### Escaneo de la estructura de archivos remota y comparacion con la
	### 	copia de la misma guardada en local, si son distintas , descargar los nuevos archivos
	print "Escaneando directorio remoto buscando nuevos elementos ..."
	dic_remoto = infoArchivosyCarpetas(RUTA_BASE_REMOTA, donde = 'nube')
	dic_CopiaLocal_remoto = cargaInfoArchivos(COPIA_LOCAL_INFO_REMOTA)
	
	df = DictDiff( dic_remoto, dic_CopiaLocal_remoto)
	actualiza(df, donde='local')
	del df	# Para facilitar el trabajo al recolector de basura

	# Despues de actualizar el sistema local , volvemos a mirar su estrutura y a guardarla
	dic_local = infoArchivosyCarpetas(RUTA_BASE_LOCAL )
	guardaInfoArchivos(dic_local, COPIA_LOCAL_INFO_LOCAL)
	
	# Guardo una copia local de la info remota de la que ya se tiene replica en local
	guardaInfoArchivos(dic_remoto, COPIA_LOCAL_INFO_REMOTA)
	
	### Paso 4- Se entra en un ciclo de doble vigilancia:
	#4.1- Por una parte el programa vigila los cambios de las carpetas locales y si se produce
	#alguno procede a actualizar su cache local y a subir el archivo/carpeta
	#4.2- Por otra parte el programa tambien vigila los cambios en una carpeta remota
	#y si se produce algun cambio procede a actualizar la copia local de esta carpeta,
	vigilancia = Vigila(5)
	
		



