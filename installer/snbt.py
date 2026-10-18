"""SPDX-License-Identifier: GPL-3.0-or-later.
Conservative parser for FTB Quests SNBT. Scalars retain their exact spelling/type.
"""
import hashlib
import json
import re

TOKEN = re.compile(r'''\s+|//[^\n]*|\#[^\n]*|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[{}\[\]:,;]|[^\s{}\[\]:,;"']+''')


def parse(text):
    tokens = []
    end = 0
    for match in TOKEN.finditer(text.lstrip('\ufeff')):
        if match.start() != end:
            raise ValueError('Unsupported SNBT syntax')
        end = match.end()
        token = match.group()
        if not token.isspace() and not token.startswith(('//', '#')):
            tokens.append(token)
    if end != len(text.lstrip('\ufeff')):
        raise ValueError('Unterminated SNBT string')
    i = 0

    def value():
        nonlocal i
        token = tokens[i]
        i += 1
        if token == '{':
            result = {}
            while tokens[i] != '}':
                if tokens[i] == ',':
                    i += 1
                    continue
                key = tokens[i]
                if key.startswith('"'):
                    key = json.loads(key)
                i += 1
                if tokens[i] != ':' or key in result:
                    raise ValueError('Invalid or duplicate SNBT key')
                i += 1
                result[key] = value()
            i += 1
            return result
        if token == '[':
            result = []
            while tokens[i] != ']':
                if tokens[i] == ',':
                    i += 1
                else:
                    result.append(value())
            i += 1
            return result
        if token in ('}', ']', ':', ','):
            raise ValueError('Unexpected SNBT delimiter')
        return token

    result = value()
    if i != len(tokens) or not isinstance(result, dict):
        raise ValueError('Expected one complete SNBT compound')
    return result


def structural_hash(text):
    data = parse(text)
    # Chapter presentation order may change after the game saves its quest file.
    data.pop('order_index', None)
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode('utf8')).hexdigest()


def language_bytes(data):
    def render(value):
        if isinstance(value, str) and value.startswith(('"', "'")):
            return value
        if isinstance(value, list):
            return '[' + ', '.join(render(item) for item in value) + ']'
        raise ValueError('Unexpected non-text language value')
    return ('{\n' + ''.join('\t' + json.dumps(key) + ': ' + render(data[key]) + '\n'
                           for key in sorted(data)) + '}\n').encode('utf8')
