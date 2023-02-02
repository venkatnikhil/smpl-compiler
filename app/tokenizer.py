from .tokens import *
from .error_handling import CustomSyntaxError
from typing import Optional
from copy import deepcopy


# FileReader class for reading the input file
class FileReader:
    # FileReader for the Tokenizer class
    def __init__(self, file_name: str) -> None:
        self._file_reader = open(file_name, 'r')

    # return the next char from the input file
    def get_next(self) -> str:
        sym: str = self._file_reader.read(1)
        # When the end of file is reached, returns the end-of-file message/token
        if not sym:
            return END_OF_FILE
        return sym


# Tokenizer class for generating the tokens from input file
class Tokenizer:
    # Initializer for the Tokenizer class
    token_map: Optional[dict[str, int]] = None

    def __init__(self, file_name) -> None:
        Tokenizer.token_map = deepcopy(DEFAULT_TOKENS)
        self.token_map = Tokenizer.token_map
        self.number: Optional[int] = None  # store the latest constant value
        self._sym: Optional[str] = None  # current character from FileReader
        self.id: Optional[int] = None  # store the unique id assigned to the last encountered identifier
        self._file_reader: FileReader = FileReader(file_name=file_name)
        self._new_token_id: int = DEFAULT_TOKENS[END_OF_FILE] + 1
        self.next_char()
        
    # Convert a string key in the _token_map to the corresponding id value
    @staticmethod
    def string2id(token: str) -> int:
        # Raise error if no such string/token exists
        if Tokenizer.token_map.get(token) is None:
            raise CustomSyntaxError(message=f"No token '{token}' found")
        
        return Tokenizer.token_map[token]
    
    # Convert an id value in the _token_map to the corresponding string key
    @staticmethod
    def id2string(ident: int) -> str:
        # Raise error if no such id exists
        if ident not in list(Tokenizer.token_map.values()):
            raise CustomSyntaxError(message=f"No id {ident} found")
        
        index = list(Tokenizer.token_map.values()).index(ident)
        return list(Tokenizer.token_map.keys())[index]
        
    # Move to the next character from the input file
    def next_char(self) -> None:
        self._sym = self._file_reader.get_next()
        
    # Return the next token generated from the input file
    def get_next(self) -> int:
        # Ignore all spaces at front
        while self._sym.isspace():
            self.next_char()
        
        # Check for end of file
        if self._sym == END_OF_FILE:
            # raise CustomSyntaxError(message=f"Reached end before finding '.'")
            return self.token_map[END_OF_FILE]
    
        # For when the token starts with a letter
        if self._sym in LETTER:
            # Create the alphanumeric token
            token = ''
            while self._sym in LETTER or self._sym in DIGIT:
                token += self._sym
                self.next_char()
            
            # When the token is new add the token to _token_map and return type as 'identifier
            if self.token_map.get(token) is None:
                self.token_map[token] = self._new_token_id
                self.id = self._new_token_id
                self._new_token_id += 1
                return self.token_map[TYPE_IDENTIFIER]
            
            # When the token exists and is greater than 255 implies that it is a previously encountered identifier
            if self.token_map[token] > self.token_map[END_OF_FILE]:
                self.id = self.token_map[token]
                return self.token_map[TYPE_IDENTIFIER]
            
            # When none of the above conditions match i.e. it exists in _token_map and has value <= 255, this implies it is a keyword
            return self.token_map[token]
        
        # For when the token starts with a digit
        if self._sym in DIGIT:
            # Create the number token
            token = 0
            while self._sym in DIGIT:
                token = token * 10 + int(self._sym)
                self.next_char()
            
            # set the number field to the token value and return
            self.number = token
            return self.token_map[TYPE_NUMBER]
        
        # If the token is the starting of a multi char operator
        if self._sym in MULTI_OPERATOR_START:
            token = self._sym
            self.next_char()
            if self.token_map.get(token + self._sym) is None:
                if self.token_map.get(token) is None:
                    raise CustomSyntaxError(message=f"No token '{token}' found")
                
                # If there is no following symbol to complete the multi-char operator return the token as an operator
                return self.token_map[token]
            
            # If the following symbol completes the multi-char operator, update the current token to include the next symbol and return
            token = token + self._sym
            self.next_char()
            return self.token_map[token]
        
        # If the token matches any other key from the token mapping(should be an operator), return the token
        if self.token_map.get(self._sym) is not None:
            token = self._sym
            self.next_char()
            return self.token_map[token]
        
        # If the current symbol doesn't exist in the _token_map and is neither an identifier nor a number, raise error
        raise CustomSyntaxError(message=f"No token '{self._sym}' found")
