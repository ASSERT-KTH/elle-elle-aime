def remove_extras(lst):
    product = []
    for i in lst:
        if i not in product:
            product.append(i)
        else:
            continue
    return product
