def remove_extras(lst):
    a = ()
    c = ()
    n = len(lst)
    for i in range(n):
        for j in range(i,n):
            if lst[i] == lst[j] and i != j:
                a += (j,) #j is the jth index of the list
            else:
                continue
    d = tuple(set(a)) #[repeated_index1, repeated_index2]
    for i in d:
        c += (lst[i],)
    b = lst[::-1]
    for j in range(len(c)):
        b.remove(c[j])
    e = b[::-1]
    return e
