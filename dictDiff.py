# Idea del programa tomada de https://github.com/hughdbrown/dictdiffer

import math
import collections

Datos = collections.namedtuple('Datos', 'tipo tiempo')

class DictDiff(object):
	""" Toma una version actual y otra pasada de un diccionario del tipo:
	
	d = {'ruta':'/',
         'archivos': [{'ruta':'/home',
                       'archivos':[],
                       'tipo':'directorio',
                       'tiempo':30000}],
         'tiempo': 10000000,
         'tipo': 'directorio'}
	
	y mira si el diccionario actual ha cambiado respecto al pasado.
	
	La diferencia puede ser de cinco tipos:
	1- En el actual hay un nuevo archivo
	2- En el actual ha dejado de estar un archivo 
	3- En el actual hay un archivo que estaba en el antiguo 
	pero con el tiempo cambiado (ha sido actualizado)
	4- En el actual hay un directorio que no estaba en el antiguo
	5- En el actual NO hay un directorio que estaba en el antiguo 
	"""
	
	def __init__(self, d_actual, d_pasado):
		self.d_actual_aplanado = []
		self.d_pasado_aplanado = []	
		self.aplana(d_actual, self.d_actual_aplanado)
		self.aplana(d_pasado, self.d_pasado_aplanado)
		self.dicRutas_actual = self.creaDicRutas(self.d_actual_aplanado)
		self.dicRutas_pasado = self.creaDicRutas(self.d_pasado_aplanado)
		
		self.conjunto_actual = set(self.dicRutas_actual.keys())
		self.conjunto_pasado = set(self.dicRutas_pasado.keys())
		self.conjunto_interseccion = self.conjunto_actual.intersection(self.conjunto_pasado)
		
		
	def aplana(self,d, d_aplanado):
		""" Aplana el diccionario d y lo guarda en d_aplanado con el formato de lista
		de tuplas [ ('/ruta', 'directorio', '1200000'), (,,), ...] """
		if d == None:
			return
		d_aplanado.append((d['ruta'], d['tipo'], d['tiempo']))
		if d.get('archivos') != None:
			for a in d.get('archivos'):
				self.aplana(a,d_aplanado)
				
	def creaDicRutas(self, listaTuplas):
		""" Toma un una lista de tuplas entregadas del tipo 
		[ ('/ruta', 'directorio', '1200000'), (,,), ...]
		y las transforma en un diccionario con estructura 
		d['ruta'] = ('tipo', 'tiempo') """
		d ={}
		for t in listaTuplas:	
			d[t[0]] = Datos(tipo=t[1], tiempo=t[2])
			
		return d
			
			
	def nuevos(self):
		""" Devuelve un conjunto con los elementos nuevos del conjunto actual 
		respecto al pasado """
		return self.conjunto_actual - self.conjunto_pasado
	
	def borrados(self):
		""" Devuelve un conjunto con los elementos borrados del conjunto actual 
		respecto al pasado """
		return self.conjunto_pasado - self.conjunto_interseccion
		
	def cambiados(self):
		""" Elementos que estan tanto en la estructura pasada como presente
		pero que han sido cambiados 
		"""
		return set(o for o in self.conjunto_interseccion
			if self.dicRutas_pasado[o].tiempo != self.dicRutas_actual[o].tiempo )
	
	def sinCambiar(self):
		""" Elementos que estan tanto en la estructura pasada como presente
		y que NO han sido cambiados """
		return set(o for o in self.conjunto_interseccion
			if self.dicRutas_pasado[o].tiempo == self.dicRutas_actual[o].tiempo ) 

    
    
if __name__ == "__main__":
    # Casos de prueba
		
	d0 = {'ruta':'/',
			 'archivos': [],
			 'tiempo': 100,
			 'tipo': 'directorio'}
			 
	d1 = {'ruta':'/',
		'archivos': [{'ruta':'/a.txt',	 
		'archivos':[],    
		'tipo':'archivo', 
		'tiempo':300}],   
		'tiempo': 100,                    
		'tipo': 'directorio'}
					   
	d2 = {'ruta':'/', 'archivos': [{'ruta':'/a.txt',
									'archivos':[],
									'tipo':'archivo',
									'tiempo':400}],
		 'tiempo': 100,
		 'tipo': 'directorio'}
		 
	d3 = {'ruta':'/','archivos': [{'ruta':'/a',
					   'archivos':[],
					   'tipo':'directorio',
					   'tiempo':400}],
		 'tiempo': 100,
		 'tipo': 'directorio'}
		 
	d4 = {'ruta':'/','archivos': [{'ruta':'/a','archivos':[{'ruta':'/a/b.txt',
															'archivos':[],
															'tipo':'archivo',
															'tiempo':500}],
									'tipo':'directorio',
									'tiempo':400}],
		 'tiempo': 100,
		 'tipo': 'directorio'}
	
	
	df = DictDiff(d1, d0)
	print "borrados: " + str(df.borrados())
	print "nuevos: " + str(df.nuevos())
	print "cambiados: " + str(df.cambiados())
	print "sin cambiar: " + str(df.sinCambiar())
	print ""

	df = DictDiff(d2, d1)
	print "borrados: " + str(df.borrados())
	print "nuevos: " + str(df.nuevos())
	print "cambiados: " + str(df.cambiados())
	print "sin cambiar: " + str(df.sinCambiar())

	print ""

	df = DictDiff(d3, d2)
	print "borrados: " + str(df.borrados())
	print "nuevos: " + str(df.nuevos())
	print "cambiados: " + str(df.cambiados())
	print "sin cambiar: " + str(df.sinCambiar())

	print ""

	df = DictDiff(d4, d3)
	print "borrados: " + str(df.borrados())
	print "nuevos: " + str(df.nuevos())
	print "cambiados: " + str(df.cambiados())
	print "sin cambiar: " + str(df.sinCambiar())

	print ""

	df = DictDiff(d3, d4)
	print "borrados: " + str(df.borrados())
	print "nuevos: " + str(df.nuevos())
	print "cambiados: " + str(df.cambiados())
	print "sin cambiar: " + str(df.sinCambiar())

	

