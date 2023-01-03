from __future__ import annotations


class CMDContainer(object):
    def __new__(cls, *args, **kwargs) -> CMDContainer:
        self = super().__new__(cls)

        return self