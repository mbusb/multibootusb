from functools import partial

# Operations

def op_add_tokens(tokens, params):
    return params + [t for t in tokens if t not in params]

def add_tokens(*tokens):
    return partial(op_add_tokens, tokens)

def op_remove_tokens(tokens, params):
    return [x for x in params if x not in tokens]

def remove_tokens(*tokens):
    return partial(op_remove_tokens, tokens)

def op_replace_token(old_token, new_token, params):
    return [new_token if x==old_token else x for x in params]

def replace_token(old_token, new_token):
    return partial(op_replace_token, old_token, new_token)

def op_add_or_replace_kv(key, value, params):
    assert key.endswith('=')
    if any([x.startswith(key) for x in params]):
        return op_replace_kv(key, value, params)
    return params + [(key + (value(key, None, params)
                             if callable(value) else value))]

def add_or_replace_kv(key, value):
    assert key.endswith('=')
    return partial(op_add_or_replace_kv, key, value)

def op_replace_kv(key, value, params):
    ''' Replace {value} of {key} if the key already exists in {params}.
    {value} may be a callable. In that case {value} will be called with
    key, definition to be replaced and {params}.
    '''
    assert key.endswith('=')
    return [key + 
            (value(key, x[len(key):], params) if callable(value) else value)
            if x.startswith(key) 
            else x for x in params]

def replace_kv(key, value):
    assert key.endswith('=')
    return partial(op_replace_kv, key, value)

def op_remove_keys(keys, params):
    return [x for x in params if all([not x.startswith(k) for k in keys])]

def remove_keys(*keys):
    assert all([k.endswith('=') for k in keys])
    return partial(op_remove_keys, keys)

# Predicates

def always(params):
    return True

def contains_token(token):
    return lambda params: token in params

def contains_all_tokens(*tokens):
    return lambda params: all([t in params for t in tokens])

def contains_any_token(*tokens):
    return lambda params: any([t in params for t in tokens])

def contains_key(key):
    assert type(key)==str
    return lambda params: any(x.startswith(key) for x in params)

def contains_all_keys(*keys):
    assert all([k.endswith('=') for k in keys])
    return lambda params: all(any(p.startswith(k) for p in params)
                              for k in keys)

def contains_any_key(*keys):
    return lambda params: any(any(p.startswith(k) for p in params)
                              for k in keys)

def _not(another_predicate):
    return lambda params: not another_predicate(params)
