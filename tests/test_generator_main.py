import random
import string

# To to list:
# done - variable list: something we have to re-use (but it is okay to not use)
# optional - exp list: generate random exp and add it to list, and then later on if we need exp again, we could either reuse from the list or random generate agaian
# counter: for if-statement, while-statement, like 3
# done - counter: for expression; we could choose the counter value randomly as well
# the let could be more than one, also need let after the if-statement
# stop for now - generate txt file as output
# consider netsted if-else
# done - add ; alway after fi
# done - while
# done - while nested while
# done - while nested if-then-else
# done - if-then-else nested while

digit = random.randint(0, 9)
op = ['==', '!=', '<', '<=', '>=', '>']
repetition = 2 # number of repetition for {}
counter_expr = 2 # counter variable for expression
counter_if = 1 # counter variable for nested if-else statement
level_if = 1 # control the number of indentation for nested if-else
counter_while = 1 # counter variable for nested while statement
level_while = 1 # control the number of indentation for nested while
amount = 3 # number of variables we initialize first
variable_init = [] # store the initialized variables
only_number = True # first assignment, we want only number as factor
assigned_variable_init = [] # store already assigned variables
then_else = False # else part

def generate_ident():
        exp = ''
        exp += random.choice(string.ascii_lowercase)
        # decide repeat or not
        nest1 = random.randint(0, 1)
        
        if nest1:
            # decide number of repetition
            nest2 = random.randint(1, repetition)
            while nest2 > 0:
                # decide repeat with digit or letter
                nest3 = random.randint(0,1)    
                if nest3:
                    exp += str(random.randint(0, 9))
                else:
                    exp += random.choice(string.ascii_lowercase) 
                nest2 -= 1   
        
        #print(exp)
        return exp

while (amount > 0):
    generated_ident = generate_ident()
    if generated_ident in variable_init:
        pass
        amount -= 1
    else:    
        variable_init.append(generated_ident)
        amount -= 1
output = "main var "
for i in range(len(variable_init)):
    if i == len(variable_init) - 1:
        output += variable_init[i]
        output += ';{'
    else:
        output += variable_init[i]
        output += ','
print(output)

def generate_number():
        exp = ''
        exp += str(digit)

        # if the first digit is not 0, we do the repetition
        if digit != 0:
            nest1 = random.randint(0, 1)
            
            if nest1:
                nest2 = random.randint(1,repetition)
                while nest2 > 0:
                    exp += str(random.randint(0, 9))
                    nest2 -= 1
        
        #print(exp)

        return exp

#generate_number()

# ignore expression for now
def generate_designator():
    
    exp = ''
    nest = random.randint(0, len(variable_init)-1)   
    exp = variable_init[nest]
        
    #print(exp)
    return exp

#generate_designator()
def generate_designator_expr():
    global assigned_variable_init

    exp = ''
    
    nest = random.randint(0, len(assigned_variable_init)-1)
    exp = assigned_variable_init[nest]
        
    #print(exp)
    return exp

# ignore funcCall for now
def generate_factor():
        global counter_expr
        global only_number
        exp = ''
        
        if(only_number):
            exp = generate_number()
        else:
            if counter_expr > 0:
                nest = random.randint(0, 2)
                #print("if nest is: " + str(nest))
            else:
                nest = random.randint(0, 1)
                #print("else nest is: " + str(nest))
            
            if nest == 0:
                exp = generate_designator_expr()
                #exp = generate_designator()
            elif nest == 1:
                exp = generate_number()
            elif nest == 2:
                counter_expr -= 1
                exp = '(' + str(generate_expression()) +')'
                #print("value: "+ str(counter_expr))
            elif nest == 3:
                pass
        #print(exp)
        return exp

#generate_factor()

# Do we need to conside X/0 case?
def generate_term():
        exp = ''
        exp = generate_factor()
        nest1 = random.randint(0, 1)
        
        if nest1:
            nest2 = random.randint(1, repetition)
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

#generate_term()

def generate_expression():
        exp = ''
        exp = generate_term()
        nest1 = random.randint(0, 1)
        
        if nest1:
            nest2 = random.randint(1, repetition)
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

#generate_relation()

def generate_assignment():
        global only_number
        global assigned_variable_init
        global then_else
        global variable_init

        if only_number:
            first_assignment = generate_designator()
            #print('let ' + first_assignment + ' <- ' + generate_expression() + ';')
            only_number = False
            assigned_variable_init.append(first_assignment)
            return 'let ' + first_assignment + ' <- ' + generate_expression()
        elif then_else:
            later_assignment = generate_designator()
            #print('let ' + later_assignment + ' <- ' + generate_expression() + ';')    
            #variable_init.append(later_assignment)
            return 'let ' + later_assignment + ' <- ' + generate_expression()
        else:
            
            later_assignment = generate_designator()
            #print('let ' + later_assignment + ' <- ' + generate_expression() + ';')    
            assigned_variable_init.append(later_assignment)
            return 'let ' + later_assignment + ' <- ' + generate_expression()
        
#generate_assignment()

# only assignment for now
def generate_statement():
    #print(generate_assignment())
    return generate_assignment()

#generate_statement()

def generate_statSequence():
    exp = ''
    exp = '\t' + str(generate_statement())
    
    
    nest1 = random.randint(0,1)
    if nest1:
        nest2 = random.randint(1,repetition)
        while nest2 > 0:
            exp += str('; ') + str(generate_statement())
            nest2 -= 1
    
    #print(exp)
    return exp

statSequence = generate_statSequence()
print(statSequence)

# ignore funcCall for now
def generate_funcCall():
        pass

def generate_if_stmt():
    global then_else
    global level_if
    global counter_if

    result = ''
    
    nest1 = random.randint(0,1)
    # 0: if-then
    if nest1:
        
        print('\t'*level_if + 'if ' + generate_relation())
        print('\t'*level_if + 'then ')
        # 0: nested, 1: no nested
        nest2 = random.randint(0,1)
        if nest2:
            # 0: nested if-else, 1: nested while
            nest3 = random.randint(0,1)
            if nest3:
                while counter_if > 0:
                    counter_if -= 1
                    level_if += 1
                    generate_if_stmt()
                    level_if -= 1
            else:
                while counter_if > 0:
                    counter_if -= 1
                    level_if += 1
                    generate_while_stmt()
                    level_if -= 1
        else:
            pass
        
        if level_if == 2:
            print('\t'*level_if + generate_statSequence())
            print('\t'*level_if + 'fi;')
        elif level_if == 3:
            print('\t'*level_if + generate_statSequence())
            print('\t'*level_if + 'fi;')
        else:
            print('\t' + generate_statSequence())
            print('\t' + 'fi;')
    
    #1: if-then-else
    else:
        print('\t'*level_if + 'if ' + generate_relation())
        then_else = True
        print('\t'*level_if + 'then ')
        
        # 0: nested if-else, 1: nested while, 2: not nested, under then statement
        nest4 = random.randint(0,2)
        if nest4 == 0:
            while counter_if > 0:
                counter_if -= 1
                level_if += 1
                generate_if_stmt()
                level_if -= 1
        elif nest4 == 1:
            while counter_if > 0:
                counter_if -= 1
                level_if += 1
                generate_while_stmt()
                level_if -= 1
        else:
            pass
        if level_if == 2:
            print('\t'*level_if + generate_statSequence())
            print('\t'*level_if + 'else ')
            nest5 = random.randint(0,2)
            if nest5 == 0:
                while counter_if > 0:
                    counter_if -= 1
                    level_if += 1
                    generate_if_stmt()
                    level_if -= 1
            elif nest5 == 1:
                while counter_if > 0:
                    counter_if -= 1
                    level_if += 1
                    generate_while_stmt()
                    level_if -= 1
            else:
                pass
            print('\t'*level_if + generate_statSequence())
            then_else = False
            print('\t'*level_if + 'fi;')
        elif level_if == 3:
            print('\t'*level_if + generate_statSequence())
            print('\t'*level_if + 'else ')
            nest6 = random.randint(0,2)
            if nest6 == 0:
                while counter_if > 0:
                    counter_if -= 1
                    level_if += 1
                    generate_if_stmt()
                    level_if -= 1
            elif nest6 == 1:
                while counter_if > 0:
                    counter_if -= 1
                    level_if += 1
                    generate_while_stmt()
                    level_if -= 1
            else:
                pass
            print('\t'*level_if + generate_statSequence())
            then_else = False
            print('\t'*level_if + 'fi;')
            
        else:
            print('\t' + generate_statSequence())
            print('\t' + 'else ')
            nest7 = random.randint(0,2)
            if nest7 == 0:
                while counter_if > 0:
                    counter_if -= 1
                    level_if += 1
                    generate_if_stmt()
                    level_if -= 1
            elif nest7 == 1:
                while counter_if > 0:
                    counter_if -= 1
                    level_if += 1
                    generate_while_stmt()
                    level_if -= 1
            else:
                pass
            print('\t' + generate_statSequence())
            then_else = False
            print('\t' + 'fi;')
        
    return result

def generate_while_stmt():
    global level_while
    global counter_while

    print('\t'*level_while + 'while ' + generate_relation())
    print('\t'*level_while + 'do')

    # 0: nested while, 1: nested if-else, 2: no nested
    nest1 = random.randint(0,2)
    if nest1 == 0:
        while counter_while > 0:
            counter_while -= 1
            level_while += 1
            generate_while_stmt()
            level_while -= 1
    elif nest1 == 1:
        while counter_while > 0:
            counter_while -= 1
            level_while += 1
            generate_if_stmt()
            level_while -= 1
    else:
        pass
        
    if level_while == 2:
        print('\t'*level_while + generate_statSequence())
        print('\t'*level_while + 'od;')
    elif level_while == 3:
        print('\t'*level_while + generate_statSequence())
        print('\t'*level_while + 'od;')
    else:
        print('\t' + generate_statSequence())
        print('\t' + 'od;')

#generate_while_stmt()
generate_if_stmt()

def generate_return_stmt():
        pass

def last_line():
    print('}.')
    return '}.'

last_line = last_line()

'''
# write output to a file
def create_output():
    f = open("output.txt", "w")
    f.write(output)
    f.write('\n')
    f.write(stat_sequence)
    f.write('\n')
    f.write(last_line)
    f.close()
create_output()
'''