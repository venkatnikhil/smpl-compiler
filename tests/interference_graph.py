blocks = []
# assume 5 blocks for now
#blocks.append("BB0")
blocks.append("BB1")
blocks.append("BB2")
blocks.append("BB3")
blocks.append("BB4")

bb = {}
#bb["BB0"] = [0]
bb["BB1"] = [1, 2, 4, 5]
bb["BB2"] = [6, 9]
bb["BB3"] = []
bb["BB4"] = [7, 8, 10, 11, 12]

instructions = {}

instructions[1] = []
instructions[2] = [1, 1]
instructions[3] = []
instructions[4] = [1, 3]
instructions[5] = []
instructions[6] = [2, 2]
instructions[7] = ["Phi", 6, 2]
instructions[8] = ["Phi", 6, 1]
instructions[9] = []
instructions[10] = [8]
instructions[11] = [1]
instructions[12] = [7]

# child-parent relationship
relationship = {}
# left child - right parent
relationship["BB1"] = ["BB0"]
relationship["BB2"] = ["BB1"]
relationship["BB3"] = ["BB1"]
relationship["BB4"] = ["BB2", "BB3"]

# result
result = []
left_result = []
right_result = []

# temp for phi
temp = []
left_temp = []
right_temp = []

interference_graph = {}

blocks.reverse()
for bl in blocks:
    bb[bl].reverse()

for bl in blocks:
    print("current block is", bl)
    print("current block's parent is", relationship[bl])
    for b in bb[bl]:
        temp = []
        for i in instructions[b]:
            
            if b in result:
                before = result
                result.remove(b)
                after = result

                list(set(before).intersection(after))
                interference_graph[b] = [list(set(before).intersection(after))]
                #print("graph is", interference_graph)
            if i == 'Phi':
                for z in instructions[b]:
                    if z in temp:
                        pass
                    else:
                        temp.append(z)
                temp.remove('Phi')
                break
            else:
                if i in result:
                    pass
                else:
                    result.append(i)
        print(bb[bl], "current set", result)
        if len(temp) != 0:
            print("temp is:", temp)
            left_temp = temp[:len(temp)//2]
            right_temp = temp[len(temp)//2:]
            print("left", left_temp)
            print("right", right_temp)