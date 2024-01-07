#!/usr/bin/env python

exstr = "fddssffjjkjhsdsfshfhjkjldlfjfkkshsldlfskjhsdjkfhskhjalgkjahlsghalkhgkl1234ahklghalkssdhfgouqeyroiguyqigouyeioyriougyiourygouiyqoruiygquioeryuiotyuiqoyertdjklfgxzvjmbkldfhgioeurbng"
# Array method
def first_unique(stri, v_range):
    pos = 0
    last_pos = len(stri)
    def chars_is_unique(chars, v_range):
        for i in range(0,v_range-1):
            for j in range(i+1,v_range):
                if(chars[i] == chars[j]):
                    return False
        return True
    # Optimize by making chars fixed size early
    chars = []
    for i in range(0,v_range):
        chars.append(stri[i])
    
    for i in range(0,last_pos):
        if(i < last_pos-v_range):
            for j in range(0,v_range):
                chars[j] = stri[i+j]
            if(chars_is_unique(chars, v_range) == True):
                return i
    return None
## Iterator method

largest_non_repeat = 3
l_rep = first_unique(exstr, largest_non_repeat)
while(l_rep != None):
    largest_non_repeat = largest_non_repeat + 1
    l_rep = first_unique(exstr, largest_non_repeat)

print("Largest non repeat: " + str(largest_non_repeat))
print(str(first_unique(exstr, 5)))

