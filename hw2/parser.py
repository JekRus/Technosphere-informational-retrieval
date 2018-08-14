#!/usr/bin/env python
import re

SPLIT_RGX = re.compile(r'\w+|[\(\)&\|!]', re.U)

class QtreeTypeInfo:
    def __init__(self, value, op=False, bracket=False, term=False):
        self.value = value
        self.is_operator = op
        self.is_bracket = bracket
        self.is_term = term

    def __repr__(self):
        return repr(self.value)

    def __eq__(self, other):
        if isinstance(other, QtreeTypeInfo):
            return self.value == other.value
        return self.value == other


class QTreeTerm(QtreeTypeInfo):
    def __init__(self, term):
        QtreeTypeInfo.__init__(self, term, term=True)


class QTreeOperator(QtreeTypeInfo):
    def __init__(self, op):
        QtreeTypeInfo.__init__(self, op, op=True)
        self.priority = get_operator_prio(op)
        self.left = None
        self.right = None


class QTreeBracket(QtreeTypeInfo):
    def __init__(self, bracket):
        QtreeTypeInfo.__init__(self, bracket, bracket=True)


def get_operator_prio(s):
    if s == '|':
        return 0
    if s == '&':
        return 1
    if s == '!':
        return 2

    return None


def is_operator(s):
    return get_operator_prio(s) is not None


def tokenize_query(q):
    tokens = []
    for t in map(lambda w: w.encode('utf-8'), re.findall(SPLIT_RGX, q)):
        if t == '(' or t == ')':
            tokens.append(QTreeBracket(t))
        elif is_operator(t):
            tokens.append(QTreeOperator(t))
        else:
            tokens.append(QTreeTerm(t))

    return tokens


def build_query_tree(tokens):
    if(len(tokens) == 0):
        return None
    if(tokens[0].is_bracket and tokens[-1].is_bracket):
        bracket_counter = 0
        for t in tokens[1:-1]:
            if(t.value == '('):
                bracket_counter += 1
            elif(t.value == ')'):
                bracket_counter -= 1
            if(bracket_counter < 0):
                break
        if(bracket_counter == 0):
            tokens = tokens[1:-1]
    bracket_counter = 0
    prior_idx = -1
    priority = 3
    for idx, t in enumerate(tokens):
        if(t.is_operator and bracket_counter == 0):
            if(t.priority <= priority):
                priority = t.priority
                prior_idx = idx
        elif(t.is_bracket):
            if(t.value == '('):
                bracket_counter += 1
            else:
                bracket_counter -= 1
    if(prior_idx != -1):
        """operator found"""
        token = tokens[prior_idx]
        if(token.value != '!'):
            token.left = build_query_tree(tokens[:prior_idx])
        token.right = build_query_tree(tokens[prior_idx+1:])
    else:
        """result = term"""
        token = tokens[0]
    return token

def parse_query(q):
    tokens = tokenize_query(q)
    return build_query_tree(tokens)
