def spacecamel(text):
    # Turn e.g. 'ShelfView' to 'Shelf View'
    return ''.join([' ' + c if c.isupper() else c for c in text]).lstrip()
