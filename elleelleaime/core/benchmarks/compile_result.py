from typing import Optional


class CompileResult:
    def __init__(self, result: Optional[bool]) -> None:
        self.result = result

    def is_passing(self) -> Optional[bool]:
        return self.result

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"CompileResult({self.result})"
