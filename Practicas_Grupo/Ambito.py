# coding: utf-8

class Ambito:
    def __init__(self):
        self.fichero = ""
        self.clase_actual = None
        self.errores = []
        
        # Pila de entornos locales (lista de diccionarios para manejar el Scope)
        # El índice -1 siempre es el entorno actual (el más profundo)
        self.pila = [{}]
        
        # Diccionario maestro para el Grafo de Clases
        # Estructura: nombre_clase -> { 'padre': str, 'atributos': {}, 'metodos': {} }
        self.clases = {}
        
        self._inicializar_clases_basicas()

    def error(self, mensaje):
        """Guarda un error semántico. El autocalificador espera que no detengamos el programa inmediatamente."""
        self.errores.append(mensaje)

    def _inicializar_clases_basicas(self):
        """Inyecta las clases que COOL trae por defecto."""
        # Object (La raíz de todo)
        self.clases['Object'] = {
            'padre': None,
            'atributos': {},
            'metodos': {
                'abort': {'formales': [], 'retorno': 'Object'},
                'type_name': {'formales': [], 'retorno': 'String'},
                'copy': {'formales': [], 'retorno': 'SELF_TYPE'}
            }
        }
        # IO
        self.clases['IO'] = {
            'padre': 'Object',
            'atributos': {},
            'metodos': {
                'out_string': {'formales': ['String'], 'retorno': 'SELF_TYPE'},
                'out_int': {'formales': ['Int'], 'retorno': 'SELF_TYPE'},
                'in_string': {'formales': [], 'retorno': 'String'},
                'in_int': {'formales': [], 'retorno': 'Int'}
            }
        }
        # Int, String, Bool
        for tipo_basico in ['Int', 'String', 'Bool']:
            self.clases[tipo_basico] = {'padre': 'Object', 'atributos': {}, 'metodos': {}}
            
        # String tiene métodos especiales nativos
        self.clases['String']['metodos'] = {
            'length': {'formales': [], 'retorno': 'Int'},
            'concat': {'formales': ['String'], 'retorno': 'String'},
            'substr': {'formales': ['Int', 'Int'], 'retorno': 'String'}
        }

    # --- FASE 1: REGISTRO DE CLASES Y HERENCIA ---

    def registrar_clase(self, nodo_clase):
        """Lee una clase del AST y la pre-registra (Pase 1)"""
        nombre = nodo_clase.nombre
        if nombre in self.clases:
            self.error(f'"{nodo_clase.nombre_fichero}", line {nodo_clase.linea}: Class {nombre} was previously defined.')
            return

        padre = nodo_clase.padre if nodo_clase.padre else 'Object'
        self.clases[nombre] = {'padre': padre, 'atributos': {}, 'metodos': {}}
        
        # Extraer firmas de atributos y métodos
        for feature in nodo_clase.caracteristicas:
            # Si es un Atributo
            if hasattr(feature, 'cuerpo') and not hasattr(feature, 'formales'):
                if feature.nombre in self.clases[nombre]['atributos']:
                    self.error(f'"{nodo_clase.nombre_fichero}", line {feature.linea}: Attribute {feature.nombre} is multiply defined in class.')
                self.clases[nombre]['atributos'][feature.nombre] = feature.tipo
            
            # Si es un Método
            elif hasattr(feature, 'formales'):
                if feature.nombre in self.clases[nombre]['metodos']:
                    self.error(f'"{nodo_clase.nombre_fichero}", line {feature.linea}: Method {feature.nombre} is multiply defined.')
                
                formales_tipos = [f.tipo for f in feature.formales]
                self.clases[nombre]['metodos'][feature.nombre] = {
                    'formales': formales_tipos,
                    'retorno': feature.tipo
                }

    def validar_herencia(self):
        """Comprueba reglas prohibidas y ciclos infinitos (Pase 2)"""
        for nombre, info in list(self.clases.items()):
            if nombre in ['Object', 'IO', 'Int', 'String', 'Bool']:
                continue
                
            padre = info['padre']
            # Regla: No heredar de tipos básicos
            if padre in ['Int', 'String', 'Bool']:
                self.error(f'Class {nombre} cannot inherit class {padre}.')
            
            # Regla: El padre debe existir
            if padre not in self.clases:
                self.error(f'Class {nombre} inherits from an undefined class {padre}.')
                self.clases[nombre]['padre'] = 'Object' # Recuperación de error
                
            # Regla: Sin ciclos de herencia (ej: A hereda de B, B hereda de A)
            ancestro = padre
            visitados = set()
            while ancestro:
                if ancestro == nombre:
                    self.error(f'Class {nombre}, or an ancestor of {nombre}, is involved in an inheritance cycle.')
                    self.clases[nombre]['padre'] = 'Object'
                    break
                visitados.add(ancestro)
                if ancestro in self.clases:
                    ancestro = self.clases[ancestro]['padre']
                else:
                    break

    # --- FASE 2: GESTIÓN DE VARIABLES Y SCOPE (ENTORNO O) ---

    def abrir_ambito(self):
        """Crea un nuevo nivel temporal para variables (Ej: al entrar a un Let o Método)"""
        self.pila.append({})

    def cerrar_ambito(self):
        """Destruye el nivel temporal al salir del bloque"""
        if len(self.pila) > 1:
            self.pila.pop()

    def abrir_clase(self, nombre_clase):
        """Prepara el entorno para empezar a analizar el cuerpo de una clase"""
        self.abrir_ambito()
        # En COOL, los métodos pueden acceder a los atributos propios y heredados.
        # Los recopilamos de arriba hacia abajo (del Object a la clase actual).
        actual = nombre_clase
        ancestros = []
        while actual:
            ancestros.insert(0, actual)
            if actual in self.clases:
                actual = self.clases[actual]['padre']
            else:
                break
                
        # Insertar atributos en el scope
        for anc in ancestros:
            if anc in self.clases:
                for attr, t in self.clases[anc]['atributos'].items():
                    self.añadir_variable(attr, t)
                    
        # self siempre existe dentro de una clase y es de tipo SELF_TYPE
        self.añadir_variable('self', 'SELF_TYPE')

    def añadir_variable(self, nombre, tipo):
        self.pila[-1][nombre] = tipo

    def buscar_variable(self, nombre):
        """Busca una variable desde el scope más profundo hacia afuera"""
        for entorno in reversed(self.pila):
            if nombre in entorno:
                return entorno[nombre]
        return None

    # --- FASE 3: LÓGICA DE TIPOS Y MÉTODOS ---

    def conforma(self, tipo_hijo, tipo_padre):
        """¿El tipo_hijo es igual o hereda de tipo_padre? ( tipo_hijo <= tipo_padre )"""
        if tipo_hijo == tipo_padre: return True
        if tipo_padre == 'Object': return True
        
        # Tratamiento especial para SELF_TYPE
        if tipo_hijo == 'SELF_TYPE':
            return self.conforma(self.clase_actual, tipo_padre)
        if tipo_padre == 'SELF_TYPE':
            return False 
            
        actual = tipo_hijo
        while actual:
            if actual == tipo_padre:
                return True
            if actual in self.clases:
                actual = self.clases[actual]['padre']
            else:
                break
        return False

    def LCA(self, tipo1, tipo2):
        """Lowest Common Ancestor: Encuentra el padre común más cercano entre dos tipos"""
        if tipo1 == tipo2: return tipo1
            
        t1 = self.clase_actual if tipo1 == 'SELF_TYPE' else tipo1
        t2 = self.clase_actual if tipo2 == 'SELF_TYPE' else tipo2
        
        # Recolectamos la genealogía del tipo 1
        ancestros_t1 = []
        actual = t1
        while actual:
            ancestros_t1.append(actual)
            if actual in self.clases:
                actual = self.clases[actual]['padre']
            else:
                break
                
        # Subimos por el tipo 2 hasta chocar con la genealogía del tipo 1
        actual = t2
        while actual:
            if actual in ancestros_t1:
                return actual
            if actual in self.clases:
                actual = self.clases[actual]['padre']
            else:
                break
                
        return 'Object'

    def buscar_metodo(self, clase, metodo, tipos_args, linea):
        """Verifica si un método existe, si los parámetros cuadran, y devuelve su tipo de retorno"""
        actual = self.clase_actual if clase == 'SELF_TYPE' else clase
        metodo_encontrado = None
        
        while actual:
            if actual in self.clases and metodo in self.clases[actual]['metodos']:
                metodo_encontrado = self.clases[actual]['metodos'][metodo]
                break
            if actual in self.clases:
                actual = self.clases[actual]['padre']
            else:
                break
                
        if not metodo_encontrado:
            self.error(f'"{self.fichero}", line {linea}: Dispatch to undefined method {metodo}.')
            return 'Object'
            
        formales = metodo_encontrado['formales']
        if len(formales) != len(tipos_args):
            self.error(f'"{self.fichero}", line {linea}: Method {metodo} called with wrong number of arguments.')
            return metodo_encontrado['retorno']
            
        for t_arg, t_formal in zip(tipos_args, formales):
            if not self.conforma(t_arg, t_formal):
                self.error(f'"{self.fichero}", line {linea}: In call of method {metodo}, type {t_arg} of parameter does not conform to declared type {t_formal}.')
                
        return metodo_encontrado['retorno']