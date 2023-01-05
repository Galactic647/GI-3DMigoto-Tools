from __future__ import annotations


class CMDContainerMeta(type):
    def __new__(cls, *args, **kwargs) -> CMDContainerMeta:
        self = super().__new__(cls, *args)

        return self

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)


class CMDContainer(metaclass=CMDContainerMeta):
    def __new__(cls, *args, **kwargs) -> CMDContainer:
        self = super().__new__(cls)

        return self
