def sort_age(lst):
    sort = True
    while sort:
        sort = False
        for i in range(len(lst)-1):
            if lst[i][1] < lst[i+1][1]:
                sort = True
                lst[i], lst[i+1] = lst[i+1], lst[i]
    return lst
