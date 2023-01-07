from __future__ import annotations

import core.commands as commands


class CMDContainerMeta(type):
    def __new__(cls, *args, **kwargs) -> CMDContainerMeta:
        class_, bases, attrs = args
        attrs['__cont_name__'] = kwargs.get('name', class_)
        
        __cont_commands__ = list()
        for name, method in attrs.items():
            if not isinstance(method, commands.Command):
                continue
            method.hidden = kwargs.get('hidden', False)
            method.scope = kwargs.get('scope', commands.NORMAL)

            for attr, value in method.__original_kwargs__.items():
                setattr(method, attr, value)
            __cont_commands__.append(name)

        attrs['__cont_commands__'] = __cont_commands__
        self = super().__new__(cls, class_, bases, attrs)
        return self

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)


class CMDContainer(metaclass=CMDContainerMeta):
    """Container for commands
    
    All command classes must inherit from this class
    """

    pass
