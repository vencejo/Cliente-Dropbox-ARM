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
         


"""

import os
import stat
import time
import myDropbox
import json
from dictDiff import DictDiff
from ConfigParser import SafeConfigParser
import logging

logging.basicConfig(filename='registro.log',format='%(asctime)s %(message)s', \
						 level=logging.INFO)

parser = SafeConfigParser()
parser.read('datosDeTrabajo.ini')

ruta_base_local = parser.get('rutas', 'RUTA_BASE_LOCAL')
ruta_base_remota = parser.get('rutas', 'RUTA_BASE_REMOTA')
copia_local_info_local = parser.get('rutas', 'COPIA_LOCAL_INFO_LOCAL')
copia_local_info_remota = parser.get('rutas', 'COPIA_LOCAL_INFO_REMOTA')

class ClienteDropbox():
	
	def __init__(self, RUTA_BASE_LOCAL= ruta_base_local,
						RUTA_BASE_REMOTA = ruta_base_remota ):
							
		self.RUTA_BASE_LOCAL = RUTA_BASE_LOCAL 
		self.RUTA_BASE_REMOTA = RUTA_BASE_REMOTA

		self.COPIA_LOCAL_INFO_LOCAL = copia_local_info_local
		self.COPIA_LOCAL_INFO_REMOTA = copia_local_info_remota

		#Conexion a Dropbox
		self.dropbox = myDropbox.connect()

		#Cambio el directorio de trabajo
		os.chdir(self.RUTA_BASE_LOCAL)

	def preparaRuta(self, ruta, donde = 'local'):
		""" Prepara una ruta para que represente un elemento en local 
		o en dropbox (donde='nube') """
		if donde == 'local':
			rutaLocal = self.RUTA_BASE_LOCAL + ruta
			return rutaLocal
		else:
			rutaRelativaDeSubida = ruta.replace(self.RUTA_BASE_LOCAL,'')
			rutaDeSubida = self.RUTA_BASE_REMOTA + rutaRelativaDeSubida
			return rutaDeSubida
			
	def guardaInfoArchivos(self, infoArchivosyCarpetas, rutaArchivoDeRutas):
		""" Guarda la info de los archivos y carpetas en un json en memoria en la ruta
		especificada """
		with open(rutaArchivoDeRutas, 'w+') as archivo:
			json.dump(infoArchivosyCarpetas, archivo, sort_keys=True, indent=2)
		
	def cargaInfoArchivos(self,rutaArchivoDeRutas):
		""" Carga la informacion del sistema de archivos en un diccionario,
		y lo devuelve """
		with open(rutaArchivoDeRutas, 'r') as archivo:
			info = json.load( archivo)
		return info

	def sincroniza(self,donde = 'local'):
		"""		
		El proceso de sincronizacion se compone de dos fases, una en la que mirando la estructura
		remota , se compara con info de COPIA_LOCAL_INFO_REMOTA , y si hay discrepancias se procede
		a la descarga de archivos hacia el local y a la actualizacion de COPIA_LOCAL_INFO_REMOTA y
		de COPIA_LOCAL_INFO_LOCAL con  la nueva estructura creada.

		Y la otra fase en   la que mirando la estructura local , se compara con info de 
		COPIA_LOCAL_INFO_LOCAL , y si hay discrepancias se procede
		a la subida de archivos hacia la nube y a la actualizacion de COPIA_LOCAL_INFO_LOCAL y
		COPIA_LOCAL_INFO_REMOTA con  la nueva estructura creada.

		Ejemplo de ejecucion:
		1- Comparo la estructura de la Nube con la Informacion de la Nube guardada en .json
			y guardo la info de la nueva estructura en el .json
		2. Si hay discrepancias, traspaso los archivos de la Nube al Local
			(Si hay muchos archivos a traspasar lo mas seguro es que, 
			por la propia latencia de la red, no se traspasen todos de una sola vez)
		3. Debido a las pegas del anterior punto, tenemos que montar un ciclo donde
			comparamos la informacion de la nube con la estructura Local
		4. Mientras halla discrepancias sigo traspasando archivos de la nube a local
		5. Guardo la nueva informacion de la estructura local en su .json correspondiente
		6. Repito los pasos del 1 al 5 , pero ahora cambiando los papeles de nube por local
			y viceversa, pero esto se hara en una nueva llamada a la funcion con el argumento
			'local'.
		"""
		if donde == 'local':
			datosDeEsteLadoGuardados = self.COPIA_LOCAL_INFO_LOCAL
			datosDelOtroLadoAguardar = self.COPIA_LOCAL_INFO_REMOTA
			rutaBase = self.RUTA_BASE_LOCAL
			laOtraRutaBase = self.RUTA_BASE_REMOTA
		else: #donde=='nube'
			datosDeEsteLadoGuardados = self.COPIA_LOCAL_INFO_REMOTA
			datosDelOtroLadoAguardar = self.COPIA_LOCAL_INFO_LOCAL
			rutaBase = self.RUTA_BASE_REMOTA
			laOtraRutaBase = self.RUTA_BASE_LOCAL
		
		# 1	
		datosGuardados = self.cargaInfoArchivos(datosDeEsteLadoGuardados) 
		datosNuevos = self.infoArchivosyCarpetas(rutaBase,donde) 
		self.guardaInfoArchivos(datosNuevos, datosDeEsteLadoGuardados)
		df = DictDiff(datosNuevos, datosGuardados) 
		
		# 2
		if len(df.borrados()) > 0 or len(df.nuevos()) > 0 or len(df.cambiados()) > 0 :
			
			elOtroLado = 'nube' if donde == 'local' else 'local'
			self.actualiza(df, elOtroLado)
			
			# 3 y 4
			datosDelOtroLado = self.infoArchivosyCarpetas(laOtraRutaBase, elOtroLado  )
			df = DictDiff(datosNuevos, datosDelOtroLado) 
			self.imprimeInfo(df)
			while len(df.borrados()) > 0 or len(df.nuevos()) > 0 :
				self.imprimeInfo(df)
				self.actualiza(df, elOtroLado)
				datosDelOtroLado = self.infoArchivosyCarpetas(laOtraRutaBase, elOtroLado  )
				df = DictDiff(datosNuevos, datosDelOtroLado)
				self.imprimeInfo(df)
			# 5
			datosDelOtroLado = self.infoArchivosyCarpetas(laOtraRutaBase, elOtroLado  )
			self.guardaInfoArchivos(datosDelOtroLado, datosDelOtroLadoAguardar)
			
										
		# Para facilitar el trabajo al recolector de basura
		# borro objetos innecesarios que podrian llenar la memoria
		del df
		
			
	def imprimeInfo(self,df):
		""" Imprime la info del df """
		print ""
		print "********************************"
		print "borrados: " + str(df.borrados())
		print "nuevos: " + str(df.nuevos())
		print "cambiados: " + str(df.cambiados())
		print  "********************************"
		print ""
		
		logging.info('\nborrados: {0}  \nnuevos: {1}  \ncambiados:{2}\n'.format( \
						str(df.borrados()),str(df.nuevos()),str(df.cambiados())))
	
		
	def actualiza(self, df, donde = 'local'):
		""" Actualiza el contenido del directorio local o remoto segun los valores del 
		DictDiff (df) """
		try:
			# Creacion de directorios 
			for e in df.nuevos():
				if df.dicRutas_actual[e].tipo == 'directorio':
					self.creaDirectorio(e, donde)
			# Creacion de archivos
			for e in df.nuevos():
				if df.dicRutas_actual[e].tipo == 'archivo':
					self.mueveArchivoHacia(e, donde)
			# borrado de archivos y directorios
			for e in df.borrados():
				self.borraArchivoOdirectorio(e, donde)
			# actualizacion de archivos cambiados
			for e in df.cambiados():
				if df.dicRutas_actual[e].tipo == 'archivo':
					self.borraArchivoOdirectorio(e, donde) # Borra el archivo  que esta desactualizado
					self.mueveArchivoHacia(e, donde)  # Actualiza el archivo 
					
		except Exception, e:
				print e
				
			
	def mueveArchivoHacia(self,ruta, donde='local'):
		""" Mueve un archivo de la nube hacia la ruta del sistema local si donde='local'
		o lo mueve hacia el dropbox si donde='nube' """
		
		if donde == 'local':
			try:
				rutaLocal = self.preparaRuta(ruta, donde = 'local')
				#logging.info('\nIntentando crear archivo en {}\n'.format(rutaLocal))
				self.dropbox.get(self.RUTA_BASE_REMOTA + ruta,rutaLocal)
				logging.info('\nCreado archivo en {}\n'.format(rutaLocal))
			except Exception, e:
				print e, rutaRemota
						
		elif donde == 'nube':
			rutaRemota = self.preparaRuta(ruta, donde = 'nube')
			self.dropbox.put(self.RUTA_BASE_LOCAL + ruta,rutaRemota)
			logging.info('\nCreado archivo en {}\n'.format(rutaRemota))
			
		else:
			print "Perdone, orden de movimiento del archivo no entendida"		
			
		

	def borraArchivoOdirectorio(self, ruta, donde='local'):
		""" Borra un archivo en la ruta del sistema local si donde='local'
		y en dropbox si donde='nube' """
		
		if donde == 'local':
			rutaLocal = self.preparaRuta(ruta, donde = 'local')
			try:
				if os.path.isdir(rutaLocal):
					os.rmdir(rutaLocal)
				else:
					os.remove(rutaLocal)
				logging.info('\nBorrado archivo en {}\n'.format(rutaLocal))
			except Exception, e:
				print e , rutaLocal
				
		elif donde == 'nube':
			rutaRemota = self.preparaRuta(ruta, donde = 'nube')
			self.dropbox.rm(rutaRemota)
			logging.info('\nBorrado archivo en {}\n'.format(rutaRemota))
			
		else:
			print "Perdone, orden de borrado del archivo no entendida"
			
	def creaDirectorio(self,ruta, donde='local'):
		""" Crea un directorio en la ruta del sistema local si donde='local'
		y en dropbox si donde='nube' """
		
		if donde == 'local':
			rutaLocal = self.preparaRuta(ruta, donde = 'local')
			try:
				os.mkdir(rutaLocal)
				logging.info('\nCreado directorio en {}\n'.format(rutaLocal))
			except Exception, e:
				print e	
				
		elif donde == 'nube':
			rutaRemota = self.preparaRuta(ruta, donde = 'nube')
			self.dropbox.mkdir(rutaRemota)
			logging.info('\nCreado directorio en {}\n'.format(rutaRemota))
			
		else:
			print "Perdone, orden de creacion del directorio no entendida"
				
						  
	def infoArchivosyCarpetas(self,ruta,donde = 'local', tipo = 'directorio' , tiempo = 0):
		""" Explora el arbol de archivos y carpetas y devuelve la informacion del mismo 
		en un diccionario subceptible de ser pasado a json
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
			d = {'ruta': ruta.replace(self.RUTA_BASE_REMOTA,'')}
			d['tipo'] = tipo
			d['tiempo'] = tiempo
			if tipo == 'directorio':
				d['archivos'] = [self.infoArchivosyCarpetas(os.path.join(ruta,x[0]),
					donde ='nube', tipo=x[1],tiempo=x[2]) for x in self.dropbox.ls(ruta)]
			return d 
		else:
			d = {'ruta': ruta.replace(self.RUTA_BASE_LOCAL,'')}
			fileStats = os.stat(ruta)
			d['tiempo'] = fileStats[stat.ST_MTIME]  #time.ctime(fileStats[.... para ver el tiempo en formato legible    
			if os.path.isdir(ruta):
				d['tipo'] = 'directorio'
				d['archivos'] = [self.infoArchivosyCarpetas(os.path.join(ruta,x), 
					donde='local') for x in os.listdir(ruta)]
			else:
				d['tipo'] = 'archivo'
								 
			return d

			
			
	def mueveTodoHacia(self, d, donde='local'):
		""" Mueve todos los archivos y carpetas registrados en d hacia donde marque
		el argumento donde. Si donde='local' los descarga de Dropbox hacia el local
		y si donde='nube' sube los archivos locales a la nube """
		try:
			if d == [] or d == None:
				return 
			
			ruta = d['ruta']
				
			if d['tipo'] == 'directorio':
				if donde == 'local':
					rutaLocal = self.preparaRuta(ruta, donde = 'local')
					if  not os.path.exists(rutaLocal):
						self.creaDirectorio(ruta, donde='local')
				else:
					self.creaDirectorio(ruta, donde='nube') 
					
				for archivo in d.get('archivos'):
					self.mueveTodoHacia(archivo , donde)
			else:
				self.mueveArchivoHacia(ruta, donde)
					
		except Exception, e:
			print e
	

		
if __name__ == "__main__":
	
	clienteDropbox = ClienteDropbox()
	### Paso 0: Lo siguiente solo en la primera vez que se ejecute el programa 
	if  not os.path.exists(clienteDropbox.COPIA_LOCAL_INFO_LOCAL) or not os.path.exists(clienteDropbox.COPIA_LOCAL_INFO_REMOTA): 
		print "Primera ejecucion del cliente ... descargando informacion remota "
		logging.info("\nPrimera ejecucion del cliente ... descargando informacion remota \n")
		dic_remoto = clienteDropbox.infoArchivosyCarpetas(clienteDropbox.RUTA_BASE_REMOTA,donde = 'nube')
		clienteDropbox.guardaInfoArchivos(dic_remoto, clienteDropbox.COPIA_LOCAL_INFO_REMOTA)
		clienteDropbox.mueveTodoHacia( dic_remoto, donde='local')
		dic_local = clienteDropbox.infoArchivosyCarpetas(clienteDropbox.RUTA_BASE_LOCAL,donde = 'local')
		clienteDropbox.guardaInfoArchivos(dic_local, clienteDropbox.COPIA_LOCAL_INFO_LOCAL)
			
	### Paso 1, 2 y 3: Se hacen cada vez que se arranca la maquina.
	### Escaneo de la estructura de archivos remota y comparacion con la
	### 	copia de la misma guardada en local, si son distintas , descargar los nuevos archivos
	print "Escaneando directorio remoto buscando nuevos elementos ..."
	logging.info("\nArrancando cliente ...Escaneando directorio remoto buscando nuevos elementos ... \n")
	clienteDropbox.sincroniza(donde = 'nube')
		
	### Paso 4- Se entra en un ciclo de doble vigilancia:
	#4.1- Por una parte el programa vigila los cambios de las carpetas locales y si se produce
	#alguno procede a actualizar su cache local y a subir el archivo/carpeta
	#4.2- Por otra parte el programa tambien vigila los cambios en una carpeta remota
	#y si se produce algun cambio procede a actualizar la copia local de esta carpeta,
	
	while True:
		print "Vigilando directorios locales ..."
		clienteDropbox.sincroniza(donde = 'local')
		print "Vigilando directorios remotos ..."
		clienteDropbox.sincroniza(donde = 'nube')
		
		

		



