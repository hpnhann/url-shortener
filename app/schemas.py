from pydantic import BaseModel
from typing import Optional

class ShortenRequest(BaseModel):
    url: str
    custom_code: Optional[str] = None  # tuỳ chọn: tự đặt short code

class URLResponse(BaseModel):
    short_code: str
    short_url: str
    original_url: str
    created_at: str
