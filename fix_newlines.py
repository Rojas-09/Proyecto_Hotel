#!/usr/bin/env python
"""Script para agregar saltos de línea al final de archivos"""

import os

files = [
    'app/models/__init__.py',
    'app/models/habitacion.py',
    'app/models/reserva.py',
    'app/models/usuario.py'
]

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if not content.endswith('\n'):
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content + '\n')
        print(f"Fixed: {filepath}")
    else:
        print(f"Already OK: {filepath}")
