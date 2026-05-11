#!/usr/bin/env python
"""Script de validación de modelos creados"""

from app import create_app, db
from app.models import *

app = create_app('development')
with app.app_context():
    inspector = db.inspect(db.engine)
    tables = sorted([t for t in inspector.get_table_names() 
                     if not t.startswith('alembic') and not t.startswith('pg_')])
    
    print('TABLAS CREADAS EN LA BASE DE DATOS')
    print('=' * 70)
    
    table_info = []
    for table in tables:
        columns = inspector.get_columns(table)
        fks = inspector.get_foreign_keys(table)
        table_info.append({
            'nombre': table,
            'columnas': len(columns),
            'fks': len(fks)
        })
        print(f'\n✓ {table.upper()} ({len(columns)} columnas, {len(fks)} FKs)')
        for col in columns:
            nullable = 'NULL' if col['nullable'] else 'NOT NULL'
            print(f'    {col["name"]:30} {str(col["type"]):20} {nullable}')
        if fks:
            print(f'    RELACIONES FK:')
            for fk in fks:
                print(f'      - {fk["constrained_columns"]} -> {fk["referred_table"]}.{fk["referred_columns"]}')
    
    print('\n' + '=' * 70)
    print(f'\nRESUMEN: {len(tables)} tablas creadas exitosamente\n')
    
    for info in sorted(table_info, key=lambda x: x['nombre']):
        print(f"  • {info['nombre']:30} {info['columnas']:2} cols, {info['fks']:2} FKs")
