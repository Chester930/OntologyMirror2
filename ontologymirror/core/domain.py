from typing import List, Optional
from pydantic import BaseModel

class RawColumn(BaseModel):
    name: str
    original_type: str
    nullable: bool = True
    pk: bool = False

class RawTable(BaseModel):
    name: str
    columns: List[RawColumn]
    source_file: Optional[str] = None
    raw_content: Optional[str] = None
