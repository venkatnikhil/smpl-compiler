from .tokens import *
from .error_handling import CustomSyntaxError

# File_Reader class for reading the input file
class File_Reader:
    # File_Reader for the Tokenizer class
    def __init__(self, file_name) -> None:
        self._file_reader = open(file_name, 'r')

    # return the next char from the input file
    def get_next(self):
        sym = self._file_reader.read(1)
        # When the end of file is reached, returns the end-of-file message/token
        if not sym:
            return EOF
        return sym

# Tokenizer class for generating the tokens from input file
class Tokenizer:
    # Initializer for the Tokenizer class
    def __init__(self, file_name) -> None:
        self._token_map = DEFAULT_TOKENS
        self._file_reader = File_Reader(file_name=file_name)
        self._new_token_id = DEFAULT_TOKENS[EOF] + 1
        self.next_char()
        
    # Convert a string key in the _token_map to the corresponding id value
    def string2id(self, token):
        # Raise error if no such string/token exists
        if self._token_map.get(token) == None:
            raise CustomSyntaxError(message=f"No token '{token}' found")
        
        return self._token_map[token]
    
    # Convert an id value in the _token_map to the corresponding string key
    def id2string(self, id):
        # Raise error if no such id exists
        if id not in list(self._token_map.values()):
            raise CustomSyntaxError(message=f"No id {id} found")
        
        index = list(self._token_map.values()).index(id)
        return list(self._token_map.keys())[index]
        
    # Move to the next character from the input file
    def next_char(self):
        self._sym = self._file_reader.get_next()
        
    # Return the next token generated from the input file
    def get_next(self):
        # Ignore all spaces at front
        while self._sym.isspace():
            self.next_char()
        
        # Check for end of file
        if self._sym == EOF:
            raise CustomSyntaxError(message=f"Reached end before finding '.'")
    
        # For when the token starts with a letter
        if self._sym in LETTER:
            # Create the alpha numeric token
            token = ''
            while (self._sym in LETTER or self._sym in DIGIT):
                token += self._sym
                self.next_char()
            
            # When the token is new add the token to _token_map and return type as 'identifier
            if self._token_map.get(token) == None:
                self._token_map[token] = self._new_token_id
                self.id = self._new_token_id
                self._new_token_id += 1
                return self._token_map[TYPE_IDENTIFIER]
            
            # When the token exists and is greater than 255 implies that it is a previously encountered identifier
            if self._token_map[token] > DEFAULT_TOKENS[EOF]:
                self.id = self._token_map[token]
                return self._token_map[TYPE_IDENTIFIER]
            
            # When none of the above conditions match i.e it exists in _token_map and has value <= 255, this implies it is a keyword
            return self._token_map[token]
        
        # For when the token starts with a letter
        if self._sym in DIGIT:
            # Create the number token
            token = 0
            while (self._sym in DIGIT):
                token = token * 10 + int(self._sym)
                self.next_char()
            
            # set the number field to the token value and return
            self.number = token
            return self._token_map[TYPE_NUMBER]
        
        # If the token is the starting of a multi char operator
        if self._sym in MULTI_OPERATOR_START:
            token = self._sym
            self.next_char()
            if self._token_map.get(token + self._sym) == None:
                if self._token_map.get(token) == None:
                    raise CustomSyntaxError(message=f"No token '{token}' found")
                
                # If there is no following symbol to complete the multi-char operator return the token as an operator
                return self._token_map[token]
            
            # If the following symbol completes the multi-char operator, update the current token to include the next symbol and return
            token = token + self._sym
            self.next_char()
            return self._token_map[token]
        
        # If the token matches any other key from the token mapping(should be a operator), return the token
        if self._token_map.get(self._sym) != None:
            token = self._sym
            self.next_char()
            return self._token_map[token]
        
        # If the current symbol doesn't exist in the _token_map and is neither an identifier or a number, raise error
        raise CustomSyntaxError(message=f"No token '{self._sym}' found")
