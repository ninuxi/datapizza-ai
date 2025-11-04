"""Datapizza namespace package.

Abilita la coesistenza di più sotto-pacchetti (core, clients, embedders, ecc.)
usando pkgutil.extend_path così che `datapizza.*` venga risolto anche quando
le cartelle sono in percorsi diversi (es. monorepo con installazioni editable).
"""

from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)
