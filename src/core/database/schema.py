from sqlalchemy import JSON, Column, Integer, String, DateTime, Text, Numeric
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Result(Base):
    __tablename__ = 'results'

    id: int = Column(Integer(), primary_key=True)  # type: ignore
    model: str = Column(String(100), nullable=False)  # type: ignore
    benchmark: str = Column(String(100), nullable=False)  # type: ignore
    project: str = Column(String(100), nullable=False)  # type: ignore
    bug_id: int = Column(Integer(), nullable=False)  # type: ignore
    # single line, function, single hunk
    request_type: str = Column(String(100))  # type: ignore
    sample_number: int = Column(Integer())  # type: ignore
    prompt_text: str = Column(Text)  # type: ignore
    prompt_size: int = Column(Integer())  # type: ignore
    bug_start_pos: int = Column(Integer())  # type: ignore
    bug_end_pos: int = Column(Integer())  # type: ignore
    temperature: float = Column(Numeric())  # type: ignore
    buggy_file_path: str = Column(String(200))  # type: ignore
    patch: str = Column(Text)  # type: ignore
    buggy_code_chunk: str = Column(Text)  # type: ignore
    buggy_code_token: int = Column(Integer())  # type: ignore
    fixed_code_chunk: str = Column(Text)  # type: ignore
    fixed_code_token: int = Column(Integer())  # type: ignore
    respond_origin_code_chunk: str = Column(Text)  # type: ignore
    respond_clean_code_chunk: str = Column(Text)  # type: ignore
    respond_code_token: int = Column(Integer())  # type: ignore
    respond_compiled_output: str = Column(Text)  # type: ignore
    respond_test_output: str = Column(Text)  # type: ignore
    buggy_test_output: str = Column(Text)  # type: ignore
    fixed_test_output: str = Column(Text)  # type: ignore
    created_on: datetime = Column(
        DateTime(), default=datetime.now)  # type: ignore
    # for example, turn on/off comments or document
    prompt_params: dict = Column(JSON)  # type: ignore
    # for example, codex params
    request_params: dict = Column(JSON)  # type: ignore
    # CODE_TOO_LONG, ERROR, SYNTAX_INCORRECT, SYNTAX_CORRECT, SEMANTIC_CORRECT
    result_type: str = Column(String(100))  # type: ignore
    # record error message if result_type is ERROR
    error_message: str = Column(Text)  # type: ignore

    def __init__(self) -> None:
        pass


# def run():
#     Base.metadata.create_all(get_engine())
