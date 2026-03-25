# coding: utf-8

from Lexer import CoolLexer
from sly import Parser
import sys
import os
from Clases import *


class CoolParser(Parser):
    nombre_fichero = ''
    tokens = CoolLexer.tokens
    debugfile = "salida.out"
    errores = []

    @_("Clase")
    def Programa(self, p):
        prog = Programa(secuencia=[p.Clase])
        return prog

    
    @_("Programa Clase")
    def Programa(self, p):
        prog = Programa(secuencia=p.Programa.secuencia + [p.Clase])
        return prog

        
    
    @_("CLASS TYPEID hereda '{' serie_atr_met '}' ';'") 
    def Clase(self, p):
        prog = Clase(nombre=p.TYPEID, padre=p.hereda, nombre_fichero=self.nombre_fichero, caracteristicas=p.serie_atr_met)
        return prog

    @_("", "INHERITS TYPEID") 
    def hereda(self, p):
        if len(p) == 0:
            return "Object"
        else:
            return p.TYPEID

    @_("", "atributo", "metodo", "serie_atr_met atributo", "serie_atr_met metodo")
    def serie_atr_met(self, p):
        if len(p) == 0:
            return []
        else:
            return [p.atributo] 
        
    @_("OBJECTID ':' TYPEID ';'", "OBJECTID ':' TYPEID ASSIGN expresion ';'")
    def atributo(self, p):
        prog = Atributo(nombre=p.OBJECTID, tipo=p.TYPEID, cuerpo=p.expresion if len(p) == 6 else NoExpr())
        return prog

    @_("OBJECTID '(' ')' ':' TYPEID '{' '}'")
    def metodo(self, p):

        prog = Metodo(nombre=p.OBJECTID, tipo=p.TYPEID, cuerpo=NoExpr())
        return prog
    
    @_("OBJECTID '(' formal_extra formal ')' ':' TYPEID '{' expresion '}'")
    def metodo(self, p):

        prog = Metodo(nombre=p.OBJECTID, formales=p.formales + [self.formal], tipo=p.TYPEID, cuerpo=p.expresion)
        return prog
        
    @_("formal ',' formal_extra", "")
    def formal_extra(self, p):
        if len(p) == 0:
            return []
        else:
            return [p.formal] + [p.formal_extra]
        
    @_("OBJECTID ':' TYPEID")
    def formal(self, p):
        prog = Formal(nombre_variable=p.OBJECTID, tipo=p.TYPEID)
        return prog
    
    @_("OBJECTID ASSIGN expresion")
    def expresion(self, p):
        return Asignacion(nombre=p.OBJECTID, cuerpo=p[2].expresion)

"""
        "expresion '+' expresion", "expresion '-' expresion", 
       "expresion '*' expresion", "expresion '/' expresion", "expresion < expresion", 
       "expresion DARROW expresion", "expresion '=' expresion", "'(' expresion ')'", "NOT expresion",
       "ISVOID expresion", "'-' expresion", "expresion '@' TYPEID '.' OBJECTID '(' ')'",
       "expresion '@' TYPEID '.' OBJECTID '(' expresion_extra_1 expresion ')'",
       "expresion '.' OBJECTID ( expresion_extra_1 expresion )", "OBJECTID '(' expresion_extra_1 expresion ')'",
       "expresion '.' OBJECTID '(' ')'", "OBJECTID '(' ')'", "IF expresion THEN expresion ELSE expresion FI",
       "WHILE expresion LOOP expresion POOL", "LET OBJECTID : TYPEID expresion_extra_2 IN expresion",
       "LET OBJECTID ':' TYPEID ASSIGN expresion expresion_extra_2 IN expresion",
       "CASE expresion OF expresion_extra_3 ';' ESAC", "NEW TYPEID", 
       "\{ expresion_extra_4 \}", "OBJECTID", "INT_CONST", "STR_CONST", "BOOL_CONST")
    def expresion(self, p):
        pass
"""
"""
    @_("expresion , expresion_extra_1", "")
    def expresion_extra_1(self, p):
        pass

    @_(", OBJECTID : TYPEID expresion_extra_2", ", OBJECTID : TYPEID <- expresion expresion_extra_2", "")
    def expresion_extra_2(self, p):
        pass

    @_("OBJECTID : TYPEID DARROW expresion expresion_extra_3", "OBJECTID : TYPEID DARROW expresion")
    def expresion_extra_3(self, p):
        pass

    @_("expresion ; expresion_extra_4", "expresion ';'")
    def expresion_extra_4(self, p):
        pass"""

##### DOMINGO masterclass ####################
"""
# Sincronizarte cuando encuentres esta expresion, despues de haber entrado en error.
@_("error '+' NUMBER"):
def expr(self, p)
    return 0 # Devuelve 0 y continua

@_('NAME')
def error(self, p):
    print("hay error en el token", str(p))
"""
