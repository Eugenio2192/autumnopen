list1 = ["a", "b", "c"]
list2 = [1, 2]


def list_combination(list1, list2):
    comb = []
    for i in list1:
        for j in list2:
            comb.append((i,j))

    return comb

