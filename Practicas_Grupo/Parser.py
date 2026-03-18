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
        pass

    
    @_("Programa Clase")
    def Programa(self, p):
        pass
    
    @_("CLASS TYPEID hereda '{'serie_atr_met '}' ';'") 
    def Clase(self, p):
        pass

    @_("", "INHERITS TYPEID")
    def hereda(self, p):
        pass

    @_("", "atributo", "metodo", "serie_atr_met atributo", "serie_atr_met metodo")
    def serie_atr_met(self, p):
        pass

    @_("OBJECTID : TYPEID ';'", "OBJECTID : TYPEID ASSIGN expresion ';'")
    def atributo(self, p):
        pass

    @_("OBJECTID ( ) : TYPEID \{ expresion \}", "OBJECTID ( formal_extra formal ) : TYPEID \{ expresion \}")
    def metodo(self, p):
        pass

    @_("formal , formal_extra", "")
    def formal_extra(self, p):
        pass

    @_("OBJECTID : TYPEID")
    def formal(self, p):
        pass

    @_("OBJECTID ASSIGN expresion", "expresion + expresion", "expresion - expresion", 
       "expresion * expresion", "expresion / expresion", "expresion < expresion", 
       "expresion DARROW expresion", "expresion = expresion", "( expresion )", "NOT expresion",
       "ISVOID expresion", "- expresion", "expresion @ TYPEID . OBJECTID ( )",
       "expresion @ TYPEID . OBJECTID ( expresion_extra_1 expresion )",
       "expresion . OBJECTID ( expresion_extra_1 expresion )", "OBJECTID ( expresion_extra_1 expresion )",
       "expresion . OBJECTID ( )", "OBJECTID ( )", "IF expresion THEN expresion ELSE expresion FI",
       "WHILE expresion LOOP expresion POOL", "LET OBJECTID : TYPEID expresion_extra_2 IN expresion",
       "LET OBJECTID : TYPEID <- expresion expresion_extra_2 IN expresion",
       "CASE expresion OF expresion_extra_3 ';' ESAC", "NEW TYPEID", 
       "\{ expresion_extra_4 \}", "OBJECTID", "INT_CONST", "STR_CONST", "BOOL_CONST")
    def expresion(self, p):
        pass

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
        pass
