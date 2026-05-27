print("enter 1st no: ")
a = int(input())

print("enter 2nd no: ")
b = int(input())

print("enter 3rd no: ")
c = int(input())

def greatest3(a, b, c):
    if(a>b and a>c):
        return a
    elif(b>a and b>c):
        return b
    else:
        return c

print("the greatest number is: ", greatest3(a, b, c))