
def generate( numRows: int) -> list[list[int]]:
    n = numRows
    output = []
    if n == 1:

        return [[1]]
    elif n == 2:

        return [[1], [1, 1]]
    else:
        next_list = generate( n - 1)

        next_list.append([1, 1])

        for i in range(1, n -1):

            next_list[n-1].insert(i, next_list[n-2][i-1]+next_list[n-2][i])


        return next_list


print(generate(5))

