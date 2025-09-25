def find_in_dict(data, key, default=None):
    """
    Procura a primeira ocorrência de `key` em qualquer nível do dicionário.
    Retorna o valor encontrado ou `default` se não existir.
    """
    if not isinstance(data, dict):
        return default

    stack = [data]
    while stack:
        current = stack.pop()
        if key in current:
            return current[key]
        for value in current.values():
            if isinstance(value, dict):
                stack.append(value)
            elif isinstance(value, list):
                stack.extend([v for v in value if isinstance(v, dict)])
    return default
