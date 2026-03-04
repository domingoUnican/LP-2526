# coding: utf-8

from sly import Lexer
import os
import re
import sys

class MatchingString(Lexer):
    tokens = {}
    @_(r'\t')
    def TAB(self, t):
        if len(self.str_buf) + len('\\t') > 1024:
            self.begin(CoolLexer)
            return thats_a_long_string(t)
        self.str_buf += '\\t'
    @_(r'[\x00-\x1f\x7f]')
    def CONTROL_CHARS(self, t):
        # Esta regla atrapa cualquier caracter de control ASCII (0-31 y 127)
        # que no haya sido atrapado antes (como el \n o el \t que tienen sus propias reglas)
        
        # Mapeo específico de los caracteres que Cool pide de cierta forma
        mapping = {
            '\x08': r'\b',    # Backspace
            '\x0c': r'\f',    # Formfeed
            '\x0d': r'\015',  # Carriage return
            '\x1b': r'\033',  # Escape
        }
        
        val = mapping.get(t.value)
        
        # Si no está en el mapeo explícito, lo ignoramos o manejamos distinto, 
        # pero para estos test de Cool, esto debería bastar.
        if val is None:
            # Si encuentras un caracter nulo (\0), en Cool es un error dentro de un string
            if t.value == '\x00':
                t.type = "ERROR"
                t.value = '"String contains null character."'
                self.begin(CoolLexer)
                return t
            val = repr(t.value)[1:-1] # Fallback genérico

        if len(self.str_buf) + len(val) > 1024:
            self.begin(CoolLexer)
            return thats_a_long_string(t)
            
        self.str_buf += val

    @_(r'\r?\n')
    def NOT_ESCAPED(self, t):
        t.type = "ERROR"
        t.value = "\"Unterminated string constant\""
        return t
    @_(r'\\\r?\n')
    def CONTINUE_IN_NEW_LINE(self, t):
        if len(self.str_buf) + len("\\n") > 1024:
            self.begin(CoolLexer)
            return thats_a_long_string(t)
        self.lineno += 1 #siguiente linea
        self.str_buf += "\\n"
    @_(r'\\[nbtf"]')
    def ESCAPE_ESPECIAL(self,t):
        if len(self.str_buf) + len(t.value) > 1024:
            self.begin(CoolLexer)
            return thats_a_long_string(t)
        self.str_buf += t.value # los caracteres especiales
    @_(r'\\\\')
    def ESCAPE_BACKLASH(self,t):
        if len(self.str_buf) + len(t.value) > 1024:
            self.begin(CoolLexer)
            return thats_a_long_string(t)
        self.str_buf += t.value
    @_(r'\\.')
    def ESCAPE(self, t):
        char = t.value[1]
        
        # Mapeo para caracteres de control que vienen escapados con una barra (\)
        mapping = {
            '\t': r'\t',      # <--- ¡AQUÍ ESTÁ LA MAGIA PARA EL TAB!
            '\x08': r'\b',    # Escaped Backspace
            '\x0c': r'\f',    # Escaped Formfeed
            '\x0d': r'\015',  # Escaped Carriage return
            '\x1b': r'\033',  # Escaped Escape
        }
        
        val = mapping.get(char, char)
        
        # Si es un nulo escapado, en Cool es error
        if char == '\x00':
            t.type = "ERROR"
            t.value = '"String contains null character."'
            self.begin(CoolLexer)
            return t

        if len(self.str_buf) + len(val) > 1024:
            self.begin(CoolLexer)
            return thats_a_long_string(t)
            
        self.str_buf += val
    @_(r'\"')
    def CLOSE_STRING(self, t):
        if len(self.str_buf) + len(t.value) > 1024:
            self.begin(CoolLexer)
            return thats_a_long_string(t)
        t.value = self.str_buf + "\""
        t.type = "STR_CONST"
        self.str_buf = "\""
        self.char_count = 0
        self.begin(CoolLexer) # volvemos al lexer
        return t
    @_(r'\0')
    def PASAR(self,t):
        pass
    @_(r'\n')
    def NEW_LINE(self, t):
        self.lineno += 1
    @_(r'[^\x00-\x1f\x7f\\\"\n]+')
    def CHARACTER(self, t):
        if len(self.str_buf) + len(t.value) > 1024:
            self.begin(CoolLexer)
            return thats_a_long_string(t)
        self.str_buf += t.value

def thats_a_long_string(t):
    t.type = "ERROR"
    t.value = "\"String constant too long\""
    return t


class Comentario(Lexer):
    tokens = {}
    @_(r'\*\)')
    def VOLVER(self, t):
        self.begin(CoolLexer)
    @_(r'.')
    def PASAR(self, t):
        pass
    @_(r'\n')
    def LINEA(self, t):
        self.lineno += 1




class CoolLexer(Lexer):
    tokens = {OBJECTID, INT_CONST, BOOL_CONST, TYPEID,
              ELSE, IF, FI, THEN, NOT, IN, CASE, ESAC, CLASS,
              INHERITS, ISVOID, LET, LOOP, NEW, OF,
              POOL, THEN, WHILE, STR_CONST, LE, DARROW, ASSIGN}
    ignore = '\t '
    literals = {'.','==', '=','+','-','*', '/', '(', ')', '<', '>', ' ', '„', ';', ':', '@', ',', '{','}','~'}
    ELSE = r'\b[eE][lL][sS][eE]\b'
    IF = r'\b[iI][fF]\b'
    FI = r'\b[fF][iI]\b'
    THEN = r'\b[tT][hH][eE][nN]\b'
    CLASS = r'\b[cC][lL][aA][sS][sS]\b'
    NOT = r'\b[nN][oO][tT]\b'
    ISVOID = r'\b[iI][sS][vV][oO][iI][dD]\b'
    LET = r'\b[lL][eE][tT]\b'
    LOOP = r'\b[lL][oO][oO][pP]\b'
    POOL = r'\b[pP][oO][oO][lL]\b'
    IN = r'\b[iI][nN]\b'
    CASE = r'\b[cC][aA][sS][eE]\b'
    ESAC = r'\b[eE][sS][aA][cC]\b'
    INHERITS = r'\b[iI][nN][hH][eE][rR][iI][tT][sS]\b'
    NEW = r'\b[nN][eE][wW]\b'
    OF = r'\b[oO][fF]\b'
    

    @_(r'_')
    def ERROR_UNDERSCORE(self,t):
        t.type = "ERROR"
        t.value = f"\"{t.value}\""
        return t

    @_(r't[rR][uU][eE]\b|f[aA][lL][sS][eE]\b')
    def BOOL_CONST(self,t):
        t.type = "BOOL_CONST"
        if str(t.value).lower() == "true":
            t.value = True
        elif str(t.value).lower() == "false":
            t.value = False
        return t
    
    @_(r'[0-9]+')
    def INT_CONST(self,t):
        t.type = "INT_CONST"
        t.value = t.value
        return t
    
    @_(r'--.*')
    def ignore_one_line_comment(self, t):
        pass
    
    @_(r'"')
    def STR_CONST(self,t):
        self.str_buf = "\""
        self.begin(MatchingString)
    
    @_(r'<-')
    def ASSIGN(self,t):
        t.type = "ASSIGN"
        return t

    @_(r'=>')
    def DARROW(self,t):
        t.type = "DARROW"
        return t

    @_(r'<=')
    def LE(self,t):
        t.type = "LE"
        return t

    @_(r'[a-z][A-Z0-9_a-z]*\b')
    def OBJECTID(self, t):
        palabras_clave = ["else", "if", "fi", "not", "in", "case", "esac", "class",
                          "inherits", "isvoid", "let", "loop", "new", "of", "pool", 
                          "then", "while"]
        if t.value.lower() in palabras_clave:
            t.type = t.value.upper()
            return t
        return t

    @_(r'\(\*')
    def IR(self, t):
        self.begin(Comentario)

    @_(r'\n')
    def LINEBREAK(self, t):
        self.lineno += 1

    @_(r'\b[wW][hH][iI][lL][eE]\b')
    def WHILE(self, t):
        t.value = (t.value) + 'dddd'
        return t
    
    @_(r'\*\)')
    def UNMATCHED_COMMENT(self, t):
        t.type = 'ERROR'
        t.value = "\"Unmatched *)\""
        return t
    
    @_(r'\w+')
    def TYPEID(self, t):
        return t

    @_(r'.')
    def LITERALS(self, t):
        if str(t.value) in self.literals:
            t.type = str(t.value)
            t.value = ""
            return t


    def error(self, t):
        self.index += 1
    
    
    CARACTERES_CONTROL = [bytes.fromhex(i+hex(j)[-1]).decode('ascii')
                          for i in ['0', '1']
                          for j in range(16)] + [bytes.fromhex(hex(127)[-2:]).decode("ascii")]

    def error(self, t):
        self.index += 1
        
    def salida(self, texto):
        lexer = CoolLexer()
        list_strings = []
        for token in lexer.tokenize(texto):
            result = f'#{token.lineno} {token.type} '
            if token.type == 'OBJECTID':
                result += f"{token.value}"
            elif token.type == 'BOOL_CONST':
                result += "true" if token.value else "false"
            elif token.type == 'TYPEID':
                result += f"{str(token.value)}"
            elif token.type in self.literals:
                result = f'#{token.lineno} \'{token.type}\' '
            elif token.type == 'STR_CONST':
                result += token.value
            elif token.type == 'INT_CONST':
                result += str(token.value)
            elif token.type == 'ERROR':
                result = f'#{token.lineno} {token.type} {token.value}'
            else:
                result = f'#{token.lineno} {token.type}'
            list_strings.append(result)
        return list_strings
