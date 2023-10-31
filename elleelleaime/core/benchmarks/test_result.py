class TestResult:
    def __init__(self, result: bool) -> None:
        self.result = result

    def is_passing(self) -> bool:
        return self.result

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"TestResult({self.result})"
