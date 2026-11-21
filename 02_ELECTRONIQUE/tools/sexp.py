"""Minimal KiCad S-expression reader/writer."""
BS = chr(92)   # backslash
QT = chr(34)   # double quote


def tokenize(s):
    out = []
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c in '()':
            out.append(c)
            i += 1
        elif c == QT:
            j = i + 1
            buf = []
            while j < n:
                if s[j] == BS:
                    buf.append(s[j + 1])
                    j += 2
                elif s[j] == QT:
                    break
                else:
                    buf.append(s[j])
                    j += 1
            out.append(('STR', ''.join(buf)))
            i = j + 1
        elif c.isspace():
            i += 1
        else:
            j = i
            while j < n and not s[j].isspace() and s[j] not in '()' + QT:
                j += 1
            out.append(('SYM', s[i:j]))
            i = j
    return out


def parse(tokens):
    def helper(idx):
        assert tokens[idx] == '('
        node = []
        idx += 1
        while tokens[idx] != ')':
            if tokens[idx] == '(':
                sub, idx = helper(idx)
                node.append(sub)
            else:
                node.append(tokens[idx])
                idx += 1
        return node, idx + 1
    node, _ = helper(0)
    return node


def load(path):
    with open(path, encoding='utf-8') as f:
        return parse(tokenize(f.read()))


def head(node):
    """Return the head atom name of a list node, or None."""
    if isinstance(node, list) and node and isinstance(node[0], tuple):
        return node[0][1]
    return None


def sym_name(node):
    """Name of a (symbol "NAME" ...) node."""
    if len(node) > 1 and isinstance(node[1], tuple):
        return node[1][1]
    return None


def find_symbols(root):
    res = {}
    for n in root[1:]:
        if head(n) == 'symbol':
            nm = sym_name(n)
            if nm:
                res[nm] = n
    return res


def esc(s):
    return s.replace(BS, BS + BS).replace(QT, BS + QT)


def dump(node, indent=0):
    """Serialize a parsed node back to S-expression text."""
    pad = '  ' * indent
    if isinstance(node, tuple):
        kind, val = node
        return QT + esc(val) + QT if kind == 'STR' else val
    parts = []
    has_list = any(isinstance(c, list) for c in node)
    for c in node:
        if isinstance(c, list):
            parts.append('\n' + dump(c, indent + 1))
        else:
            parts.append(' ' + dump(c, indent))
    body = ''.join(parts).lstrip()
    if has_list:
        return pad + '(' + body + '\n' + pad + ')'
    return pad + '(' + body + ')'
