# coding: utf-8

from sly import Lexer
import os
import re
import sys


class Comentario(Lexer):
    tokens = {}

    @_(r'\(\*')
    def ABRIR(self, t):
        pass

    @_(r'\*\)')
    def VOLVER(self, t):
        self.begin(CoolLexer)

    @_(r'\n')
    def LINEA(self, t):
        self.lineno += 1

    @_(r'.')
    def PASAR(self, t):
        pass

    def error(self, t):
        self.index += 1


class CoolLexer(Lexer):
    tokens = {OBJECTID, INT_CONST, BOOL_CONST, TYPEID,
              ELSE, IF, FI, THEN, NOT, IN, CASE, ESAC, CLASS,
              INHERITS, ISVOID, LET, LOOP, NEW, OF,
              POOL, WHILE, STR_CONST, LE, DARROW, ASSIGN}

    # \f (0x0C) y \v (0x0B) se ignoran fuera de strings como whitespace
    ignore = '\t \r\x0c\x0b'

    # COOL literals válidos: NO incluye > (no es operador de COOL)
    literals = {'+', '-', '*', '/', '(', ')', '<', '.', ',', ';',
                ':', '@', '{', '}', '~', '='}

    # Operadores compuestos (deben ir antes que literales)
    DARROW = r'=>'
    LE     = r'<='
    ASSIGN = r'<-'

    # Comentarios de línea
    @_(r'--[^\n]*')
    def COMENTARIO_LINEA(self, t):
        pass

    # *) sin (* previo → ERROR "Unmatched *)"
    @_(r'\*\)')
    def UNMATCHED(self, t):
        t.type = 'ERROR'
        t.value = f'#{self.lineno} ERROR "Unmatched *)"'
        return t

    # Comentarios de bloque anidados (*...*) con conteo de niveles
    @_(r'\(\*')
    def IR(self, t):
        nivel = 1
        i = self.index
        texto = self.text
        while i < len(texto) and nivel > 0:
            if texto[i] == '\n':
                self.lineno += 1
                i += 1
            elif texto[i] == '\r':
                i += 1
            elif texto[i:i+2] == '(*':
                nivel += 1
                i += 2
            elif texto[i:i+2] == '*)':
                nivel -= 1
                i += 2
            else:
                i += 1
        self.index = i
        if nivel != 0:
            t.type = 'ERROR'
            t.value = f'#{self.lineno} ERROR "EOF in comment"'
            return t

    # Strings — procesado carácter a carácter
    @_(r'"')
    def STR_CONST(self, t):
        result = ''
        i = self.index
        texto = self.text
        error = None

        while i < len(texto):
            c = texto[i]

            if c == '"':
                i += 1
                break

            elif c == '\x00':
                error = f'#{self.lineno} ERROR "String contains null character."'
                i += 1
                while i < len(texto) and texto[i] != '"' and texto[i] != '\n':
                    i += 1
                if i < len(texto) and texto[i] == '"':
                    i += 1
                break

            elif c == '\n':
                self.lineno += 1
                error = f'#{self.lineno} ERROR "Unterminated string constant"'
                i += 1
                break

            elif c == '\r':
                # CR+LF (Windows EOL) → ignorar el CR; el \n lo procesará la siguiente iteración
                if i + 1 < len(texto) and texto[i + 1] == '\n':
                    i += 1
                else:
                    # CR solo (sin LF) → incluirlo como carácter del string
                    result += c
                    i += 1

            elif c == '\\':
                i += 1
                # Saltar CRs de Windows antes del siguiente carácter real
                while i < len(texto) and texto[i] == '\r':
                    i += 1
                if i >= len(texto):
                    error = f'#{self.lineno} ERROR "EOF in string constant"'
                    break
                nc = texto[i]
                if nc == '\x00':
                    error = f'#{self.lineno} ERROR "String contains escaped null character."'
                    i += 1
                    while i < len(texto) and texto[i] != '"' and texto[i] != '\n':
                        i += 1
                    if i < len(texto) and texto[i] == '"':
                        i += 1
                    break
                elif nc == '\n':
                    # Newline escapado: válido, se incluye como \n
                    self.lineno += 1
                    result += '\n'
                elif nc == 'n':
                    result += '\n'
                elif nc == 't':
                    result += '\t'
                elif nc == 'b':
                    result += '\b'
                elif nc == 'f':
                    result += '\f'
                else:
                    # \c → c para cualquier otro char (\r→'r', \a→'a', \\→'\', etc.)
                    result += nc
                i += 1

            else:
                result += c
                i += 1
        else:
            error = f'#{self.lineno} ERROR "EOF in string constant"'

        self.index = i
        t.lineno = self.lineno  # Report line number at end of string

        if error:
            t.type = 'ERROR'
            t.value = error
            return t

        if len(result) > 1024:
            t.type = 'ERROR'
            t.value = f'#{self.lineno} ERROR "String constant too long"'
            return t

        t.value = result
        return t

    # Enteros: preservar representación original (01, 0777, etc.)
    @_(r'\d+')
    def INT_CONST(self, t):
        t.value = t.value  # string, para preservar ceros iniciales
        return t

    # Salto de línea
    @_(r'\n')
    def LINEBREAK(self, t):
        self.lineno += 1

    # Identificadores y palabras reservadas
    # COOL: identificadores empiezan por letra (NO por _)
    @_(r'[a-zA-Z][a-zA-Z0-9_]*')
    def OBJECTID(self, t):
        upper = t.value.upper()

        # true/false: BOOL_CONST solo si empiezan por minúscula
        if upper == 'TRUE':
            if t.value[0].islower():
                t.type = 'BOOL_CONST'
                t.value = True
                return t
            else:
                t.type = 'TYPEID'
                return t

        if upper == 'FALSE':
            if t.value[0].islower():
                t.type = 'BOOL_CONST'
                t.value = False
                return t
            else:
                t.type = 'TYPEID'
                return t

        # Palabras reservadas (case-insensitive)
        keywords = {
            'CLASS', 'ELSE', 'FI', 'IF', 'IN', 'INHERITS', 'ISVOID',
            'LET', 'LOOP', 'NEW', 'NOT', 'OF', 'POOL', 'THEN',
            'WHILE', 'CASE', 'ESAC',
        }

        if upper in keywords:
            t.type = upper
            return t

        # TYPEID: empieza por mayúscula; OBJECTID: empieza por minúscula
        if t.value[0].isupper():
            t.type = 'TYPEID'
        else:
            t.type = 'OBJECTID'
        return t

    def error(self, t):
        char = t.value[0]
        code = ord(char)
        if code < 32 or code == 127:
            repr_char = f'\\{code:03o}'
        elif char == '\\':
            repr_char = '\\\\'
        else:
            repr_char = char
        t.type = 'ERROR'
        t.value = f'#{self.lineno} ERROR "{repr_char}"'
        self.index += 1
        return t

    # ------------------------------------------------------------------
    # Método de salida
    # ------------------------------------------------------------------
    def salida(self, texto):
        lexer = CoolLexer()
        list_strings = []

        for token in lexer.tokenize(texto):
            lineno = token.lineno

            if token.type == 'ERROR':
                list_strings.append(token.value)
                continue

            if token.type == 'OBJECTID':
                result = f'#{lineno} OBJECTID {token.value}'

            elif token.type == 'TYPEID':
                result = f'#{lineno} TYPEID {token.value}'

            elif token.type == 'BOOL_CONST':
                val = "true" if token.value else "false"
                result = f'#{lineno} BOOL_CONST {val}'

            elif token.type == 'STR_CONST':
                escaped = _escape_string(token.value)
                result = f'#{lineno} STR_CONST "{escaped}"'

            elif token.type == 'INT_CONST':
                result = f'#{lineno} INT_CONST {token.value}'

            elif token.type in lexer.literals:
                result = f"#{lineno} '{token.type}'"

            else:
                result = f'#{lineno} {token.type}'

            list_strings.append(result)

        return list_strings


def _escape_string(s):
    """
    Convierte el valor interno de un STR_CONST a la representación de salida COOL.
    Sigue la convención del compilador de referencia coolc.
    """
    result = ''
    for c in s:
        code = ord(c)
        if c == '\n':
            result += '\\n'
        elif c == '\t':
            result += '\\t'
        elif c == '\b':
            result += '\\b'
        elif c == '\f':
            result += '\\f'
        elif c == '\\':
            result += '\\\\'
        elif c == '"':
            result += '\\"'
        elif code < 32 or code == 127:
            # Otros chars de control → octal \NNN
            result += f'\\{code:03o}'
        else:
            result += c
    return result


if __name__ == '__main__':
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', newline='') as f:
            texto = f.read()
        lexer = CoolLexer()
        print(f'#name "{sys.argv[1]}"')
        for linea in lexer.salida(texto):
            print(linea)