"""
DebugTools: conjunto de decorators úteis para debug em Python.
Uso:
    import debugtools as dbg

    @dbg.debug_call
    def soma(a, b):
        return a + b
"""

import time
import os
import functools
import traceback
from functools import wraps

# -------------------------------------------------------------
# Decorator: Loga chamada da função (args e kwargs)
# -------------------------------------------------------------
def debug_call(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"[DEBUG] Chamando {func.__name__} com args={args}, kwargs={kwargs}")
        return func(*args, **kwargs)
    return wrapper


# -------------------------------------------------------------
# Decorator: Loga retorno da função
# -------------------------------------------------------------
def debug_result(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        print(f"[DEBUG] Retorno de {func.__name__}: {result}")
        return result
    return wrapper


# -------------------------------------------------------------
# Decorator: Loga chamada + retorno
# -------------------------------------------------------------
def debug(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"[DEBUG] Entrando em {func.__name__}")
        print(f"[DEBUG] args={args}, kwargs={kwargs}")
        result = func(*args, **kwargs)
        print(f"[DEBUG] Saindo de {func.__name__} com retorno={result}")
        return result
    return wrapper


# -------------------------------------------------------------
# Decorator paramétrico: debug(level)
# nível 1 → entrada e saída
# nível 2 → inclui args e kwargs
# -------------------------------------------------------------
def debug_level(level=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if level >= 1:
                print(f"[DEBUG-{level}] -> Entrando em {func.__name__}")
            if level >= 2:
                print(f"[DEBUG-{level}] args={args}, kwargs={kwargs}")

            result = func(*args, **kwargs)

            if level >= 1:
                print(f"[DEBUG-{level}] <- Saindo de {func.__name__} com retorno={result}")

            return result
        return wrapper
    return decorator


# -------------------------------------------------------------
# Decorator: medir tempo de execução
# -------------------------------------------------------------
def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        result = func(*args, **kwargs)
        t1 = time.perf_counter()
        print(f"[TIMER] {func.__name__} executou em {t1 - t0:.6f}s")
        return result
    return wrapper


# -------------------------------------------------------------
# Decorator: debug + timer combinado
# -------------------------------------------------------------
def debug_timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"[DEBUG] Iniciando {func.__name__}")
        print(f"[DEBUG] args={args}, kwargs={kwargs}")

        t0 = time.perf_counter()
        result = func(*args, **kwargs)
        t1 = time.perf_counter()

        print(f"[DEBUG] Retorno: {result}")
        print(f"[TIMER] {func.__name__} executou em {t1 - t0:.6f}s")
        return result
    return wrapper


# -------------------------------------------------------------
# Decorator: ativado somente se variável de ambiente DEBUG=1
# -------------------------------------------------------------
DEBUG_MODE = os.getenv("DEBUG", "0") == "1"

def debug_if_enabled(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if DEBUG_MODE:
            print(f"[DEBUG] {func.__name__} -> args={args}, kwargs={kwargs}")
        return func(*args, **kwargs)
    return wrapper


# -------------------------------------------------------------
# Decorator: loga exceções com stack trace
# -------------------------------------------------------------
def log_exceptions(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"[ERROR] Exceção em {func.__name__}: {e}")
            traceback.print_exc()
            raise
    return wrapper


# -------------------------------------------------------------
# Decorator: trace de execução estilo profiler
# -------------------------------------------------------------
def trace(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"--> Entrando: {func.__name__}")
        result = func(*args, **kwargs)
        print(f"<-- Saindo : {func.__name__}")
        return result
    return wrapper


# -------------------------------------------------------------
# Lista de exportação quando usar: from debugtools import ...
# -------------------------------------------------------------
__all__ = [
    "debug_call",
    "debug_result",
    "debug",
    "debug_level",
    "timer",
    "debug_timer",
    "debug_if_enabled",
    "log_exceptions",
    "trace",
]
