import random
import string

''' Output looks like
main {
    let a <- 10;
    if a < 11
    then
        let f <- 15 + 11;
    fi
}.
'''

letter = random.choice(string.ascii_lowercase)
digit = random.randint(0, 9)
op = ['==', '!=', '<', '<=', '>=', '>']


def generate_ident():
    exp = ''
    exp += letter
    nest1 = random.randint(0, 1)
    
    if nest1:
        nest2 = random.randint(1, 2)
        while nest2 > 0:
            nest3 = random.randint(0,1)    
            if nest3:
                exp += str(random.randint(0, 9))
            else:
                exp += random.choice(string.ascii_lowercase) 
            nest2 -= 1   
    
    #print(exp)
    return exp

#generate_ident()

def generate_number():
    exp = ''
    exp += str(digit)
    nest1 = random.randint(0, 1)
    
    # This may give 08, 09, etc?
    if nest1:
        nest2 = random.randint(1,2)
        while nest2 > 0:
            exp += str(random.randint(0, 9))
            nest2 -= 1
    
    #print(exp)

    return exp

#generate_number()

def generate_designator():
    exp = ''
    exp = generate_ident()
    
    #print(exp)
    return exp
#generate_designator()

def generate_factor():
    exp = ''

    nest = random.randint(0, 2)
    
    if nest == 0:
        exp = generate_designator()
    elif nest == 1:
        exp = generate_number()
    elif nest == 2:
        exp = '( ' + generate_expression() +' )'
    elif nest == 3:
        pass
    print(exp)
    #return exp

generate_factor()

def generate_term():
    exp = ''
    exp = generate_factor()
    nest1 = random.randint(0, 1)
    
    if nest1:
        nest2 = random.randint(1, 2)
        while nest2 > 0:
            nest3 = random.randint(0, 1)
            if nest3:
                exp += ' * '
                exp += generate_factor()
            else:
                exp += ' / '
                exp += generate_factor()
            nest2 -= 1
    #print(exp)
    return exp

# generate_term()

def generate_expression():
    exp = ''
    exp = generate_term()
    nest1 = random.randint(0, 1)
    
    if nest1:
        nest2 = random.randint(1, 2)
        while nest2 > 0:
            nest3 = random.randint(0, 1)
            if nest3:
                exp += ' + '
                exp += generate_term()
            else:
                exp += ' - '
                exp += generate_term()
            nest2 -= 1
    #print(exp)
    return exp

#generate_expression()

def generate_relation():
    exp1 = generate_expression()
    exp2 = generate_expression()
    result = ''
    result = exp1 + ' ' + str(random.choice(op)) + ' ' + exp2
    #print(result)
    return result # E.g. 1 < 19?

# generate_relation()

def generate_assignment():
    #print('let ' + generate_designator() + ' <- ' + generate_expression())
    return ('let ' + generate_designator() + ' <- ' + generate_expression())
    # let a <- a?

# generate_assignment()

def generate_statement():
    return generate_assignment()

# generate_statement()
def generate_statSequence():
    exp = ''
    exp = generate_statement()
    
    nest1 = random.randint(0,1)
    if nest1:
        nest2 = random.randint(1,2)
        while nest2 > 0:
            exp += '; ' + generate_statement()
            nest2 -= 1
    
    nest3 = random.randint(0,1)
    if nest3:
        exp += ';'
    #print(exp)
    return exp

#generate_statSequence()

def generate_funcCall():
    pass

def generate_if_stmt():
    exp = ''
    nest1 = random.randint(0,1)
    if nest1:
        exp = ('if ' + generate_relation() + '\nthen ' + generate_statSequence() + '\nfi ')
    else:
        exp = ('if ' + generate_relation() + '\nthen ' + generate_statSequence() + '\nelse ' + generate_statSequence() + '\nfi ')
    print(exp)
    #return exp
# multiple let with same variable 
#generate_if_stmt()

def generate_while_stmt():
    pass
def generate_return_stmt():
    pass