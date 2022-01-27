from .globals import config as CONFIG

for _each_key, _each_value in CONFIG.items():
    exec(f"{_each_key} = _each_value", locals())