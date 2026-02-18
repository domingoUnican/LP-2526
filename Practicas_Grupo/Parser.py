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

    @_("Clase ';'")
    def Programa(self, p):
        pass

    
    @_("Programa Clase ';'")
    def Programa(self, p):
        pass
    
    @_("CLASS TYPEID hereda '{'serie_atr_met '}'") 
    def Clase(self, p):
        pass

    @_("", "INHERITS TYPEID")
    def hereda(self, p):
        pass

    @_("", "atributo", "metodo", "serie_atr_met atributo", "serie_atr_met metodo")
    def serie_atr_met(self, p):
        pass

    
