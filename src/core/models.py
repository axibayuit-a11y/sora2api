"""Data models"""
from datetime import datetime
from typing import Optional, List, Union
from pydantic import BaseModel

class Token(BaseModel):
    """Token model"""
    id: Optional[int] = None
    token: str
    email: str
    name: Optional[str] = ""
    st: Optional[str] = None
    rt: Optional[str] = None
    remark: Optional[str] = None
    expiry_time: Optional[datetime] = None
    is_active: bool = True
    cooled_until: Optional[datetime] = None
    created_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    use_count: int = 0
    # 订阅信息
    plan_type: Optional[str] = None  # 账户类型，如 chatgpt_team
    plan_title: Optional[str] = None  # 套餐名称，如 ChatGPT Business
    subscription_end: Optional[datetime] = None  # 套餐到期时间
    # Sora2 支持信息
    sora2_supported: Optional[bool] = None  # 是否支持Sora2
    sora2_invite_code: Optional[str] = None  # Sora2邀请码
    sora2_redeemed_count: int = 0  # Sora2已用次数
    sora2_total_count: int = 0  # Sora2总次数

class TokenStats(BaseModel):
    """Token statistics"""
    id: Optional[int] = None
    token_id: int
    image_count: int = 0
    video_count: int = 0
    error_count: int = 0
    last_error_at: Optional[datetime] = None

class Task(BaseModel):
    """Task model"""
    id: Optional[int] = None
    task_id: str
    token_id: int
    model: str
    prompt: str
    status: str = "processing"  # processing/completed/failed
    progress: float = 0.0
    result_urls: Optional[str] = None  # JSON array
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class RequestLog(BaseModel):
    """Request log model"""
    id: Optional[int] = None
    token_id: Optional[int] = None
    operation: str
    request_body: Optional[str] = None
    response_body: Optional[str] = None
    status_code: int
    duration: float
    created_at: Optional[datetime] = None

class AdminConfig(BaseModel):
    """Admin configuration"""
    id: int = 1
    video_cooldown_threshold: int = 30
    error_ban_threshold: int = 3
    updated_at: Optional[datetime] = None

class ProxyConfig(BaseModel):
    """Proxy configuration"""
    id: int = 1
    proxy_enabled: bool = False
    proxy_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class WatermarkFreeConfig(BaseModel):
    """Watermark-free mode configuration"""
    id: int = 1
    watermark_free_enabled: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class VideoLengthConfig(BaseModel):
    """Video length configuration"""
    id: int = 1
    default_length: str = "10s"  # Default video length: "10s" or "15s"
    lengths_json: str = '{"10s": 300, "15s": 450}'  # JSON mapping of length to n_frames
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# API Request/Response models
class ChatMessage(BaseModel):
    role: str
    content: Union[str, List[dict]]  # Support both string and array format (OpenAI multimodal)

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    image: Optional[str] = None
    stream: bool = True

class ChatCompletionChoice(BaseModel):
    index: int
    message: Optional[dict] = None
    delta: Optional[dict] = None
    finish_reason: Optional[str] = None

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
