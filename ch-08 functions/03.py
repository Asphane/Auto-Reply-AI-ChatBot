
print("enter no of rows: ")
n=int(input())

def func(n):
    x=n
    for i in range(1, n+1):
        print("*"*x)
        x-=1

func(n)