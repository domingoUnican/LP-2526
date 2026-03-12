# coding: utf-8

from sly import Lexer

# Estados auxiliares o sub-lexers para manejar casos específicos como strings y comentarios anidados.

class RecuperarString(Lexer):
    """Estado de recuperación: ignora todo hasta cerrar el string roto."""
    tokens = {}
    
    @_(r'\"')
    def CERRAR_STRING(self, t):
        self.begin(CoolLexer) 
        
    @_(r'\\\r?\n')
    def IGNORAR_SALTO_ESCAPADO(self, t):
        self.lineno += 1
        
    @_(r'\r?\n')
    def SALTO_SIN_ESCAPAR(self, t):
        self.lineno += 1
        self.begin(CoolLexer) # Un salto sin escapar cierra el string roto
        
    @_(r'.')
    def PASAR(self, t):
        pass # Ignoramos


class MatchingString(Lexer):
    """Estado para el análisis de strings válidos e inválidos en progreso."""
    tokens = {}
    
    @_(r'\t')
    def TAB(self, t):
        if self.char_count + 1 > 1024:
            return self.thats_a_long_string(t)
        self.char_count += 1
        self.str_buf += '\\t'

    @_(r'[\x00-\x09\x0b-\x1f\x7f]')
    def CONTROL_CHARS(self, t):
        mapping = {
            '\x08': r'\b',    # Backspace
            '\x0c': r'\f',    # Formfeed
            '\x0d': r'\015',  # Carriage return
            '\x1b': r'\033',  # Escape
        }
        val = mapping.get(t.value)
        
        if val is None:
            if t.value == '\x00':
                t.type = "ERROR"
                t.value = '"String contains null character."'
                self.begin(RecuperarString)
                return t
            val = repr(t.value)[1:-1]
            # s05 test octales en vez de hexadecimales
            octal_val = oct(ord(t.value))[2:].zfill(3)
            val = f'\\{octal_val}'

        if self.char_count + 1 > 1024:
            return self.thats_a_long_string(t)
        
        self.char_count += 1
        self.str_buf += val

    @_(r'\r?\n')
    def NOT_ESCAPED(self, t):
        self.lineno += 1
        self.begin(CoolLexer) 
        t.type = "ERROR"
        t.value = '"Unterminated string constant"' 
        return t

    @_(r'\\\r?\n')
    def CONTINUE_IN_NEW_LINE(self, t):
        if self.char_count + 1 > 1024:
            return self.thats_a_long_string(t)
        self.char_count += 1
        self.lineno += 1 
        self.str_buf += "\\n"

    @_(r'\\[nbtf"]')
    def ESCAPE_ESPECIAL(self, t):
        if self.char_count + 1 > 1024:
            return self.thats_a_long_string(t)
        self.char_count += 1
        self.str_buf += t.value 

    @_(r'\\\\')
    def ESCAPE_BACKLASH(self, t):
        if self.char_count + 1 > 1024:
            return self.thats_a_long_string(t)
        self.char_count += 1
        self.str_buf += t.value

    @_(r'\\.')
    def ESCAPE(self, t):
        char = t.value[1]
        mapping = {
            '\t': r'\t',      # Escaped Tab
            '\x08': r'\b',    # Escaped Backspace
            '\x0c': r'\f',    # Escaped Formfeed
            '\x0d': r'\015',  # Escaped Carriage return
            '\x1b': r'\033',  # Escaped Escape
        }
        val = mapping.get(char, char)
        
        if char == '\x00':
            t.type = "ERROR"
            t.value = '"String contains escaped null character."'
            self.begin(RecuperarString)
            return t

        if self.char_count + 1 > 1024:
            return self.thats_a_long_string(t)
            
        self.char_count += 1
        self.str_buf += val

    @_(r'\"')
    def CLOSE_STRING(self, t):
        t.value = self.str_buf + "\""
        t.type = "STR_CONST"
        self.begin(CoolLexer) 
        return t

    @_(r'\0')
    def PASAR(self, t):
        pass

    @_(r'[^\x00-\x1f\x7f\\\"\n]+')
    def CHARACTER(self, t):
        if self.char_count + len(t.value) > 1024:
            return self.thats_a_long_string(t)
        self.char_count += len(t.value)
        self.str_buf += t.value

    def thats_a_long_string(self, t):
        t.type = "ERROR"
        t.value = "\"String constant too long\""
        self.begin(RecuperarString)
        return t


class Comentario(Lexer):
    """Estado para manejar comentarios multilinea anidados."""
    tokens = {}
    
    @_(r'\(\*')
    def ABRIR_NUEVO(self, t):
        self.nesting_depth += 1
        
    @_(r'\*\)')
    def VOLVER(self, t):
        self.nesting_depth -= 1
        if self.nesting_depth == 0:
            self.begin(CoolLexer)
            
    @_(r'.')
    def PASAR(self, t):
        pass
        
    @_(r'\n')
    def LINEA(self, t):
        self.lineno += 1


# Lexer principal para Cool, con manejo de errores y estados auxiliares para strings y comentarios anidados.

class CoolLexer(Lexer):
    # Tokens
    tokens = {
        OBJECTID, INT_CONST, BOOL_CONST, TYPEID,
        ELSE, IF, FI, THEN, NOT, IN, CASE, ESAC, CLASS,
        INHERITS, ISVOID, LET, LOOP, NEW, OF,
        POOL, WHILE, STR_CONST, LE, DARROW, ASSIGN
    }
    
    # variables de control para el manejo de caracteres especiales, literales, palabras clave e invalidos
    ignore = '\t '

    literals = {'.', '==', '=', '+', '-', '*', '/', '(', ')', '<', '>', ' ', '„', ';', ':', '@', ',', '{', '}', '~'}
    
    invalid_characters = {'!', '#', '$', '%', '^', '&', '_', '>', '?', '`', '[', ']', '\\', '|', '\\001', '\\002', '\\003', '\\004'} 
    
    palabras_clave = {"else", "if", "fi", "not", "in", "case", "esac", "class",
                      "inherits", "isvoid", "let", "loop", "new", "of", "pool", 
                      "then", "while"}

    # expresiones regulares simples (Palabras Clave)
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
    
    @_(r'\b[wW][hH][iI][lL][eE]\b')
    def WHILE(self, t):
        return t

    # operadores
    @_(r'<-')
    def ASSIGN(self, t):
        t.type = "ASSIGN"
        return t

    @_(r'=>')
    def DARROW(self, t):
        t.type = "DARROW"
        return t

    @_(r'<=')
    def LE(self, t):
        t.type = "LE"
        return t

    # constantes e Identificadores
    @_(r't[rR][uU][eE]\b|f[aA][lL][sS][eE]\b')
    def BOOL_CONST(self, t):
        t.value = str(t.value).lower() == "true"
        return t
    
    @_(r'[0-9]+')
    def INT_CONST(self, t):
        return t

    @_(r'[a-z][A-Z0-9_a-z]*\b')
    def OBJECTID(self, t):
        if t.value.lower() in self.palabras_clave:
            t.type = t.value.upper()
        return t

    @_(r'[A-Z][a-zA-Z0-9_]*\b')
    def TYPEID(self, t):
        return t

    # comentarios y Strings (Transiciones de estado)
    @_(r'--.*')
    def ignore_one_line_comment(self, t):
        pass

    @_(r'\(\*')
    def IR(self, t):
        self.nesting_depth = 1 
        self.begin(Comentario)

    @_(r'\*\)')
    def UNMATCHED_COMMENT(self, t):
        t.type = 'ERROR'
        t.value = "\"Unmatched *)\""
        return t

    @_(r'"')
    def STR_CONST(self, t):
        self.str_buf = "\""
        self.char_count = 0
        self.begin(MatchingString)

    # caracteres Especiales y Control
    @_(r'\n')
    def LINEBREAK(self, t):
        self.lineno += 1

    @_(r'_')
    def ERROR_UNDERSCORE(self, t):
        t.type = "ERROR"
        t.value = f"\"{t.value}\""
        return t

    @_(r'[\x01\x02\x03\x04\x00]')
    def INVISIBLE_CHARS(self, t):
        t.type = "ERROR"
        octal_val = oct(ord(t.value))[2:].zfill(3)
        t.value = f'"\\{octal_val}"'
        return t

    @_(r'.')
    def LITERALS(self, t):
        if str(t.value) in self.invalid_characters:
            t.type = "ERROR"
            t.value = f"\"{t.value}\""
            if t.value == '\"\\\"':
                t.value = "\"\\\\\""
            return t
        if str(t.value) in self.literals:
            t.type = str(t.value)
            t.value = ""
            return t

    # métodos Generales
    def error(self, t):
        self.index += 1

    def tokenize(self, text, *args, **kwargs):
        """Reescribimos tokenize para manejar el EOF según el estado."""
        for tok in super().tokenize(text, *args, **kwargs):
            yield tok
            
        if self.__class__.__name__ == 'MatchingString':
            class EOFToken: pass
            t = EOFToken()
            t.type = "ERROR"
            t.value = '"EOF in string constant"'
            t.lineno = self.lineno
            yield t
            self.begin(CoolLexer) 

        elif self.__class__.__name__ == 'Comentario':
            class EOFToken: pass
            t = EOFToken()
            t.type = "ERROR"
            t.value = '"EOF in comment"'
            t.lineno = self.lineno
            yield t
            self.begin(CoolLexer)
        
    def salida(self, texto):
        """Procesa el texto y devuelve una lista con el output formateado."""
        list_strings = []
        for token in self.tokenize(texto): 
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
                
            list_strings.append(result.strip())
        return list_strings