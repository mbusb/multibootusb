#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Name:     param_rewrite.py
# Purpose:  Provide functions to assist boot param rewriting with.
# Authors:  shinji-s
# Licence:  This file is a part of multibootusb package. You can redistribute
# it or modify under the terms of GNU General Public License, v.2 or above

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
    if any(x.startswith(key) for x in params):
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
    return [x for x in params if all(not x.startswith(k) for k in keys)]

def remove_keys(*keys):
    assert all(k.endswith('=') for k in keys)
    return partial(op_remove_keys, keys)

# Predicates

def always(starter_token, params):
    return True

def contains_token(token):
    return lambda starter, params: token in params

def contains_all_tokens(*tokens):
    return lambda starter, params: all(t in params for t in tokens)

def contains_any_token(*tokens):
    return lambda starter, params: any(t in params for t in tokens)

def contains_key(key):
    assert type(key)==str
    assert key[-1:] == '='
    return lambda starter, params: any(x.startswith(key) for x in params)

def contains_all_keys(*keys):
    assert all(k.endswith('=') for k in keys)
    return lambda starter, params: all(any(p.startswith(k) for p in params)
                              for k in keys)

def contains_any_key(*keys):
    return lambda starter, params: any(any(p.startswith(k) for p in params)
                              for k in keys)

def starter_is_either(*possible_starters):
    return lambda starter, params: starter in possible_starters

def _not(another_predicate):
    return lambda starter, params: not another_predicate(starter, params)


def test_rewrite_machinary():

    def transform(op_or_oplist, predicate, input_line):
        params = input_line.split(' ')
        if not predicate('test_starter', params):
            return input_line
        # See if op_or_oplist is iterable
        try:
            iter(op_or_oplist)
        except TypeError:
            # Otherwise let's assume we have a singleton op here
            op_or_oplist = [op_or_oplist]
        for op in op_or_oplist:
            params = op(params)
        return ' '.join(params)


    boot_line = "kernel /boot/vmlinuz bar=baz foo bar key2=value2"

    print ('Test token addition')
    assert transform(add_tokens('foo','more'), always, boot_line)==\
           "kernel /boot/vmlinuz bar=baz foo bar key2=value2 more"

    print ('Test token replacement')
    assert transform(replace_token('foo', 'hum'), always, boot_line)==\
           "kernel /boot/vmlinuz bar=baz hum bar key2=value2"

    print ('Test token removal')
    assert transform(remove_tokens('foo', 'bar'), always, boot_line)==\
           "kernel /boot/vmlinuz bar=baz key2=value2"

    print ('Test kv add_or_replace (results in append)')
    assert transform(add_or_replace_kv('live-path=', '/lib/live'), always, 
                     boot_line)==\
                     "kernel /boot/vmlinuz bar=baz foo bar key2=value2 " \
                     "live-path=/lib/live"

    print ('Test kv add_or_replace (results in replace)')
    assert transform(add_or_replace_kv('bar=', '/lib/live'),
                     always, boot_line)==\
           "kernel /boot/vmlinuz bar=/lib/live foo bar key2=value2"

    print ('Test kv replace (results in no change)')
    assert transform(replace_kv('live-path=', '/lib/live'), always,
                     boot_line)==\
                     "kernel /boot/vmlinuz bar=baz foo bar key2=value2"

    print ('Test kv replace (results in replace)')
    assert transform(replace_kv('bar=', '/lib/live'), always, boot_line)==\
           "kernel /boot/vmlinuz bar=/lib/live foo bar key2=value2"

    print ('Test kv replace with computed value (bang! at head).')
    assert transform(replace_kv('bar=', lambda k, old_v, params: '!' + old_v),
                     always, boot_line)==\
                     "kernel /boot/vmlinuz bar=!baz foo bar key2=value2"

    print ('Test key removal')
    assert transform(remove_keys('bar=','key2='), always, boot_line)==\
           "kernel /boot/vmlinuz foo bar"

    print ('Test strip everything (multi-op)')
    assert transform([remove_tokens('foo', 'bar', 'kernel', '/boot/vmlinuz'),
                      remove_keys('bar=', 'key2=')],
                     always, boot_line)==''

    print ('Test condition always')
    assert  transform(replace_token('bar', 'tail'), always,
                      boot_line)=="kernel /boot/vmlinuz bar=baz foo tail "\
                      "key2=value2"

    print ('Test condition contains_token (positive)')
    assert transform(replace_token('bar', 'tail'), contains_token('kernel'),
                     boot_line)=="kernel /boot/vmlinuz bar=baz foo tail"\
                     " key2=value2"

    print ('Test condition contains_token (negative)')
    assert transform(replace_token('bar', 'tail'), contains_token('initrd'),
                     boot_line)==boot_line

    print ('Test condition contains_all_tokens (positive)')
    assert transform(replace_token('bar', 'tail'),
                     contains_all_tokens('kernel', 'foo'),
                     boot_line)=="kernel /boot/vmlinuz bar=baz foo tail" \
                     " key2=value2"

    print ('Test condition contains_all_tokens (negative)')
    assert transform(replace_token('bar', 'tail'),
                     contains_all_tokens('kernel', 'nowhere'),
                     boot_line)==boot_line

    print ('Test condition contains_any_token (positive)')
    assert  transform(replace_token('bar', 'tail'),
                      contains_any_token('kernel', 'nowhere'),
                      boot_line)=="kernel /boot/vmlinuz bar=baz foo tail" \
                      " key2=value2"

    print ('Test condition contains_any_token (negative)')
    assert  transform(replace_token('bar', 'tail'),
                      contains_any_token('not_anywhere', 'nowhere'),
                      boot_line)==boot_line

    print ('Test condition contains_any_key (positive)')
    assert  transform(replace_token('bar', 'tail'),
                      contains_any_key('key2', 'nowhere'),
                      boot_line)=="kernel /boot/vmlinuz bar=baz foo tail" \
                      " key2=value2"

    print ('Test condition contains_any_key (negative)')
    assert transform(replace_token('bar', 'tail'),
                     contains_any_key('anywhere', 'else'),
                     boot_line)==boot_line


    print ('Test not() predicate on contains_any_token (positive)')
    assert transform(replace_token('bar', 'tail'),
                     _not(contains_any_token('nowhere', 'else')),
                     boot_line)=="kernel /boot/vmlinuz bar=baz foo tail" \
                     " key2=value2"

    print ('Test not() predicate on contains_any_token (negative)')
    assert transform(replace_token('bar', 'tail'),
                     _not(contains_any_token('nowhere', 'kernel')),
                     boot_line)==boot_line

    print ('Test not() predicate on contains_all_keys (positive)')
    assert transform(replace_token('bar', 'tail'),
                     _not(contains_all_keys('bar=', 'nonexistent_key=')),
                     boot_line)=="kernel /boot/vmlinuz bar=baz foo tail" \
                     " key2=value2"

    print ('Test not() predicate on contains_all_keys (negative)')
    assert transform(replace_token('bar', 'tail'),
                     _not(contains_all_keys('bar=', 'key2=')),
                     boot_line)=="kernel /boot/vmlinuz bar=baz foo bar" \
                     " key2=value2"
