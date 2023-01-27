from app.tokenizer import Tokenizer

tokenizer = Tokenizer('test.txt')
token = -1
while(token != 30):
    token = tokenizer.get_next()
    value = list(tokenizer._token_map.keys())[list(tokenizer._token_map.values()).index(token)]
    if value == 'identifier':
        value = str(tokenizer.id) + ' ' + list(tokenizer._token_map.keys())[list(tokenizer._token_map.values()).index(tokenizer.id)]
    elif value == 'number':
        value = tokenizer.number
    print(token, value)