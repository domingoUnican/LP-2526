# coding: utf-8
from dataclasses import dataclass, field
from typing import List

@dataclass
class Nodo:
    linea: int = 0

    def str(self, n):
        return f'{n*" "}#{self.linea}\n'
        
    def Tipo(self, entorno=None):
        pass

@dataclass
class Formal(Nodo):
    nombre_variable: str = '_no_set'
    tipo: str = '_no_type'

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_formal\n'
        resultado += f'{(n+2)*" "}{self.nombre_variable}\n'
        resultado += f'{(n+2)*" "}{self.tipo}\n'
        return resultado
    
    def Tipo(self, entorno=None):
        # Un formal no suele tener un "tipo de retorno" evaluable, 
        # pero registra su tipo en el entorno.
        return self.tipo

@dataclass
class Expresion(Nodo):
    cast: str = '_no_type'  # Esto DEBE estar en una dataclass para heredarse bien
    
    def Tipo(self, entorno=None):
        return self.cast

@dataclass
class Asignacion(Expresion):
    nombre: str = '_no_set'
    cuerpo: Expresion = None

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_assign\n'
        resultado += f'{(n+2)*" "}{self.nombre}\n'
        resultado += self.cuerpo.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    
    def Tipo(self, entorno=None):
        # El tipo de una asignación es el tipo de la expresión asignada
        self.cast = self.cuerpo.Tipo(entorno)
        return self.cast

@dataclass
class LlamadaMetodoEstatico(Expresion):
    cuerpo: Expresion = None
    clase: str = '_no_type'
    nombre_metodo: str = '_no_set'
    argumentos: List[Expresion] = field(default_factory=list)

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_static_dispatch\n'
        resultado += self.cuerpo.str(n+2)
        resultado += f'{(n+2)*" "}{self.clase}\n'
        resultado += f'{(n+2)*" "}{self.nombre_metodo}\n'
        resultado += f'{(n+2)*" "}(\n'
        resultado += ''.join([c.str(n+2) for c in self.argumentos])
        resultado += f'{(n+2)*" "})\n'
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    
    def Tipo(self, entorno=None):
        self.cuerpo.Tipo(entorno)
        for arg in self.argumentos:
            arg.Tipo(entorno)
        # REQUIERE ENTORNO: Buscar el tipo de retorno de 'nombre_metodo' en 'clase'
        # self.cast = entorno.lookup_method_return_type(self.clase, self.nombre_metodo)
        return self.cast

@dataclass
class LlamadaMetodo(Expresion):
    cuerpo: Expresion = None
    nombre_metodo: str = '_no_set'
    argumentos: List[Expresion] = field(default_factory=list)

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_dispatch\n'
        resultado += self.cuerpo.str(n+2)
        resultado += f'{(n+2)*" "}{self.nombre_metodo}\n'
        resultado += f'{(n+2)*" "}(\n'
        resultado += ''.join([c.str(n+2) for c in self.argumentos])
        resultado += f'{(n+2)*" "})\n'
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    
    def Tipo(self, entorno=None):
        tipo_cuerpo = self.cuerpo.Tipo(entorno)
        for arg in self.argumentos:
            arg.Tipo(entorno)
        # REQUIERE ENTORNO: Buscar el tipo de retorno del método en la clase de 'tipo_cuerpo'
        # self.cast = entorno.lookup_method_return_type(tipo_cuerpo, self.nombre_metodo)
        return self.cast

@dataclass
class Condicional(Expresion):
    condicion: Expresion = None
    verdadero: Expresion = None
    falso: Expresion = None

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_cond\n'
        resultado += self.condicion.str(n+2)
        resultado += self.verdadero.str(n+2)
        resultado += self.falso.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    
    def Tipo(self, entorno=None):
        self.condicion.Tipo(entorno) # Debería chequearse que es Bool
        tipo_v = self.verdadero.Tipo(entorno)
        tipo_f = self.falso.Tipo(entorno)
        # REQUIERE ENTORNO: El tipo es el Ancestro Común Más Cercano (LCA) entre tipo_v y tipo_f
        # self.cast = entorno.lowest_common_ancestor(tipo_v, tipo_f)
        return self.cast
    
@dataclass
class Bucle(Expresion):
    condicion: Expresion = None
    cuerpo: Expresion = None

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_loop\n'
        resultado += self.condicion.str(n+2)
        resultado += self.cuerpo.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    
    def Tipo(self, entorno=None):
        self.condicion.Tipo(entorno) # Debería chequearse que es Bool
        self.cuerpo.Tipo(entorno)
        # En COOL, el tipo de retorno de un bucle while siempre es Object
        self.cast = 'Object'
        return self.cast

@dataclass
class Let(Expresion):
    nombre: str = '_no_set'
    tipo: str = '_no_set'
    inicializacion: Expresion = None
    cuerpo: Expresion = None

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_let\n'
        resultado += f'{(n+2)*" "}{self.nombre}\n'
        resultado += f'{(n+2)*" "}{self.tipo}\n'
        resultado += self.inicializacion.str(n+2)
        resultado += self.cuerpo.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    
    def Tipo(self, entorno=None):
        if not isinstance(self.inicializacion, NoExpr):
            self.inicializacion.Tipo(entorno)
        # REQUIERE ENTORNO: Añadir 'nombre' con su 'tipo' al scope antes de evaluar el cuerpo
        # entorno.enter_scope()
        # entorno.add(self.nombre, self.tipo)
        self.cast = self.cuerpo.Tipo(entorno)
        # entorno.exit_scope()
        return self.cast

@dataclass
class Bloque(Expresion):
    expresiones: List[Expresion] = field(default_factory=list)

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{n*" "}_block\n'
        resultado += ''.join([e.str(n+2) for e in self.expresiones])
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    
    def Tipo(self, entorno=None):
        # El tipo de un bloque es el tipo de la ÚLTIMA expresión evaluada
        tipo_final = 'Object'
        for expr in self.expresiones:
            tipo_final = expr.Tipo(entorno)
        self.cast = tipo_final
        return self.cast

@dataclass
class RamaCase(Nodo):
    nombre_variable: str = '_no_set'
    tipo: str = '_no_set'
    cuerpo: Expresion = None

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_branch\n'
        resultado += f'{(n+2)*" "}{self.nombre_variable}\n'
        resultado += f'{(n+2)*" "}{self.tipo}\n'
        resultado += self.cuerpo.str(n+2)
        return resultado
    
    def Tipo(self, entorno=None):
        # REQUIERE ENTORNO: Añadir variable al scope, evaluar y sacar del scope
        return self.cuerpo.Tipo(entorno)

@dataclass
class Swicht(Expresion): # Nota: Tienes un pequeño typo en tu código (Swicht -> Switch), lo mantengo para no romper tu programa
    expr: Expresion = None
    casos: List[RamaCase] = field(default_factory=list)

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_typcase\n'
        resultado += self.expr.str(n+2)
        resultado += ''.join([c.str(n+2) for c in self.casos])
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    
    def Tipo(self, entorno=None):
        self.expr.Tipo(entorno)
        tipos_ramas = []
        for caso in self.casos:
            tipos_ramas.append(caso.Tipo(entorno))
        
        # REQUIERE ENTORNO: El tipo es el LCA de los tipos de todas las ramas
        # Si tienes la función: self.cast = entorno.multiple_lca(tipos_ramas)
        return self.cast

@dataclass
class Nueva(Expresion):
    tipo: str = '_no_set'

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_new\n'
        resultado += f'{(n+2)*" "}{self.tipo}\n'
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    
    def Tipo(self, entorno=None):
        # El tipo de "new Class" es "Class"
        self.cast = self.tipo
        return self.cast

@dataclass
class OperacionBinaria(Expresion):
    izquierda: Expresion = None
    derecha: Expresion = None

    def Tipo(self, entorno=None):
        self.izquierda.Tipo(entorno)
        self.derecha.Tipo(entorno)
        return self.cast

@dataclass
class Suma(OperacionBinaria):
    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_plus\n'
        resultado += self.izquierda.str(n+2)
        resultado += self.derecha.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    
    def Tipo(self, entorno=None):
        super().Tipo(entorno) # Evalúa izquierda y derecha
        self.cast = 'Int' # En COOL, las matemáticas siempre devuelven Int
        return self.cast

@dataclass
class Resta(OperacionBinaria):
    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_sub\n'
        resultado += self.izquierda.str(n+2)
        resultado += self.derecha.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    
    def Tipo(self, entorno=None):
        super().Tipo(entorno)
        self.cast = 'Int'
        return self.cast

@dataclass
class Multiplicacion(OperacionBinaria):
    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_mul\n'
        resultado += self.izquierda.str(n+2)
        resultado += self.derecha.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    
    def Tipo(self, entorno=None):
        super().Tipo(entorno)
        self.cast = 'Int'
        return self.cast

@dataclass
class Division(OperacionBinaria):
    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_divide\n'
        resultado += self.izquierda.str(n+2)
        resultado += self.derecha.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    
    def Tipo(self, entorno=None):
        super().Tipo(entorno)
        self.cast = 'Int'
        return self.cast

@dataclass
class Menor(OperacionBinaria):
    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_lt\n'
        resultado += self.izquierda.str(n+2)
        resultado += self.derecha.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    
    def Tipo(self, entorno=None):
        super().Tipo(entorno)
        self.cast = 'Bool' # Las comparaciones lógicas devuelven Bool
        return self.cast

@dataclass
class LeIgual(OperacionBinaria):
    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_leq\n'
        resultado += self.izquierda.str(n+2)
        resultado += self.derecha.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    
    def Tipo(self, entorno=None):
        super().Tipo(entorno)
        self.cast = 'Bool'
        return self.cast

@dataclass
class Igual(OperacionBinaria):
    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_eq\n'
        resultado += self.izquierda.str(n+2)
        resultado += self.derecha.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    
    def Tipo(self, entorno=None):
        super().Tipo(entorno)
        self.cast = 'Bool'
        return self.cast

@dataclass
class Neg(Expresion): # Negación aritmética (~)
    expr: Expresion = None
    
    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_neg\n'
        resultado += self.expr.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    
    def Tipo(self, entorno=None):
        self.expr.Tipo(entorno)
        self.cast = 'Int'
        return self.cast

@dataclass
class Not(Expresion): # Negación lógica (not)
    expr: Expresion = None
    
    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_comp\n'
        resultado += self.expr.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
        
    def Tipo(self, entorno=None):
        self.expr.Tipo(entorno)
        self.cast = 'Bool'
        return self.cast

@dataclass
class EsNulo(Expresion):
    expr: Expresion = None
    
    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_isvoid\n'
        resultado += self.expr.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    
    def Tipo(self, entorno=None):
        self.expr.Tipo(entorno)
        self.cast = 'Bool'
        return self.cast

@dataclass
class Objeto(Expresion):
    nombre: str = '_no_set'
    
    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_object\n'
        resultado += f'{(n+2)*" "}{self.nombre}\n'
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    
    def Tipo(self, entorno=None):
        if self.nombre == 'self':
            self.cast = 'SELF_TYPE'
        else:
            # REQUIERE ENTORNO: Buscar el tipo de la variable en la tabla de símbolos
            # self.cast = entorno.lookup(self.nombre)
            pass
        return self.cast

@dataclass
class NoExpr(Expresion):
    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_no_expr\n'
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    
    def Tipo(self, entorno=None):
        self.cast = '_no_type'
        return self.cast

@dataclass
class Entero(Expresion):
    valor: int = 0
    
    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_int\n'
        resultado += f'{(n+2)*" "}{self.valor}\n'
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    
    def Tipo(self, entorno=None):
        self.cast = 'Int'
        return self.cast

@dataclass
class String(Expresion):
    valor: str = '_no_set'
    
    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_string\n'
        resultado += f'{(n+2)*" "}{self.valor}\n'
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    
    def Tipo(self, entorno=None):
        self.cast = 'string'
        return self.cast

@dataclass
class Booleano(Expresion):
    valor: bool = False
    
    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_bool\n'
        resultado += f'{(n+2)*" "}{1 if self.valor else 0}\n'
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    
    def Tipo(self, entorno=None):
        self.cast = 'Bool'
        return self.cast

@dataclass
class Programa(Nodo):
    secuencia: List = field(default_factory=list)
    
    def str(self, n):
        resultado = super().str(n)
        resultado += f'{" "*n}_program\n'
        resultado += ''.join([c.str(n+2) for c in self.secuencia])
        return resultado
    
    def Tipo(self, entorno=None):
        for clase in self.secuencia:
            clase.Tipo(entorno)

@dataclass
class Caracteristica(Nodo):
    nombre: str = '_no_set'
    tipo: str = '_no_set'
    cuerpo: Expresion = None

    def Tipo(self, entorno=None):
        return super().Tipo(entorno)

@dataclass
class Clase(Nodo):
    nombre: str = '_no_set'
    padre: str = '_no_set'
    nombre_fichero: str = '_no_set'
    caracteristicas: List[Caracteristica] = field(default_factory=list)

    def Tipo(self, entorno=None):
        # Aqui deberías establecer el entorno para la clase actual 
        # (para que 'self' sepa de qué tipo es)
        for caracteristica in self.caracteristicas:
            caracteristica.Tipo(entorno)

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_class\n'
        resultado += f'{(n+2)*" "}{self.nombre}\n'
        resultado += f'{(n+2)*" "}{self.padre}\n'
        resultado += f'{(n+2)*" "}"{self.nombre_fichero}"\n'
        resultado += f'{(n+2)*" "}(\n'
        resultado += ''.join([c.str(n+2) for c in self.caracteristicas])
        resultado += f'{(n+2)*" "})\n'
        return resultado

@dataclass
class Metodo(Caracteristica):
    formales: List[Formal] = field(default_factory=list)

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_method\n'
        resultado += f'{(n+2)*" "}{self.nombre}\n'
        resultado += ''.join([c.str(n+2) for c in self.formales])
        resultado += f'{(n + 2) * " "}{self.tipo}\n'
        resultado += self.cuerpo.str(n+2)
        return resultado
    
    def Tipo(self, entorno=None):
        # REQUIERE ENTORNO: Añadir los formales al scope antes de evaluar el cuerpo
        self.cuerpo.Tipo(entorno)
        return self.tipo

@dataclass
class Atributo(Caracteristica):
    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_attr\n'
        resultado += f'{(n+2)*" "}{self.nombre}\n'
        resultado += f'{(n+2)*" "}{self.tipo}\n'
        resultado += self.cuerpo.str(n+2)
        return resultado
    
    def Tipo(self, entorno=None):
        if not isinstance(self.cuerpo, NoExpr):
            self.cuerpo.Tipo(entorno)
        return self.tipo