# Permette di eseguire solo i test unitari senza scaricare PostgreSQL/psycopg.
# Non viene importato dall'applicazione.
import importlib.util
import sys
import types

if importlib.util.find_spec('psycopg') is None:
    psycopg = types.ModuleType('psycopg')
    psycopg.Error = type('Error', (Exception,), {})
    psycopg.connect = lambda *a, **kw: None
    psycopg.sql = types.SimpleNamespace(SQL=lambda s: s, Identifier=lambda x: x, Placeholder=lambda: '%s')
    rows = types.ModuleType('psycopg.rows')
    rows.dict_row = object()
    sys.modules['psycopg'] = psycopg
    sys.modules['psycopg.rows'] = rows
