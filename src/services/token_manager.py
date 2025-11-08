"""Token management module"""
import jwt
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from curl_cffi.requests import AsyncSession
from ..core.database import Database
from ..core.models import Token, TokenStats
from ..core.config import config
from .proxy_manager import ProxyManager

class TokenManager:
    """Token lifecycle manager"""

    def __init__(self, db: Database):
        self.db = db
        self._lock = asyncio.Lock()
        self.proxy_manager = ProxyManager(db)
    
    async def decode_jwt(self, token: str) -> dict:
        """Decode JWT token without verification"""
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            return decoded
        except Exception as e:
            raise ValueError(f"Invalid JWT token: {str(e)}")
    
    async def get_user_info(self, access_token: str) -> dict:
        """Get user info from Sora API"""
        proxy_url = await self.proxy_manager.get_proxy_url()

        async with AsyncSession() as session:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "Origin": "https://sora.chatgpt.com",
                "Referer": "https://sora.chatgpt.com/"
            }

            kwargs = {
                "headers": headers,
                "timeout": 30,
                "impersonate": "chrome"  # 自动生成 User-Agent 和浏览器指纹
            }

            if proxy_url:
                kwargs["proxy"] = proxy_url

            response = await session.get(
                f"{config.sora_base_url}/me",
                **kwargs
            )

            if response.status_code != 200:
                raise ValueError(f"Failed to get user info: {response.status_code}")

            return response.json()

    async def get_subscription_info(self, token: str) -> Dict[str, Any]:
        """Get subscription information from Sora API

        Returns:
            {
                "plan_type": "chatgpt_team",
                "plan_title": "ChatGPT Business",
                "subscription_end": "2025-11-13T16:58:21Z"
            }
        """
        print(f"🔍 开始获取订阅信息...")
        proxy_url = await self.proxy_manager.get_proxy_url()

        headers = {
            "Authorization": f"Bearer {token}"
        }

        async with AsyncSession() as session:
            url = "https://sora.chatgpt.com/backend/billing/subscriptions"
            print(f"📡 请求 URL: {url}")
            print(f"🔑 使用 Token: {token[:30]}...")

            kwargs = {
                "headers": headers,
                "timeout": 30,
                "impersonate": "chrome"  # 自动生成 User-Agent 和浏览器指纹
            }

            if proxy_url:
                kwargs["proxy"] = proxy_url
                print(f"🌐 使用代理: {proxy_url}")

            response = await session.get(url, **kwargs)
            print(f"📥 响应状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"📦 响应数据: {data}")

                # 提取第一个订阅信息
                if data.get("data") and len(data["data"]) > 0:
                    subscription = data["data"][0]
                    plan = subscription.get("plan", {})

                    result = {
                        "plan_type": plan.get("id", ""),
                        "plan_title": plan.get("title", ""),
                        "subscription_end": subscription.get("end_ts", "")
                    }
                    print(f"✅ 订阅信息提取成功: {result}")
                    return result

                print(f"⚠️  响应数据中没有订阅信息")
                return {
                    "plan_type": "",
                    "plan_title": "",
                    "subscription_end": ""
                }
            else:
                error_msg = f"Failed to get subscription info: {response.status_code}"
                print(f"❌ {error_msg}")
                print(f"📄 响应内容: {response.text[:500]}")
                raise Exception(error_msg)

    async def get_sora2_invite_code(self, access_token: str) -> dict:
        """Get Sora2 invite code"""
        proxy_url = await self.proxy_manager.get_proxy_url()

        print(f"🔍 开始获取Sora2邀请码...")

        async with AsyncSession() as session:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }

            kwargs = {
                "headers": headers,
                "timeout": 30,
                "impersonate": "chrome"  # 自动生成 User-Agent 和浏览器指纹
            }

            if proxy_url:
                kwargs["proxy"] = proxy_url
                print(f"🌐 使用代理: {proxy_url}")

            response = await session.get(
                "https://sora.chatgpt.com/backend/project_y/invite/mine",
                **kwargs
            )

            print(f"📥 响应状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Sora2邀请码获取成功: {data}")
                return {
                    "supported": True,
                    "invite_code": data.get("invite_code"),
                    "redeemed_count": data.get("redeemed_count", 0),
                    "total_count": data.get("total_count", 0)
                }
            else:
                # Check if it's 401 unauthorized
                try:
                    error_data = response.json()
                    if error_data.get("error", {}).get("message", "").startswith("401"):
                        print(f"⚠️  Token不支持Sora2")
                        return {
                            "supported": False,
                            "invite_code": None
                        }
                except:
                    pass

                print(f"❌ 获取Sora2邀请码失败: {response.status_code}")
                print(f"📄 响应内容: {response.text[:500]}")
                return {
                    "supported": False,
                    "invite_code": None
                }

    async def activate_sora2_invite(self, access_token: str, invite_code: str) -> dict:
        """Activate Sora2 with invite code"""
        import uuid
        proxy_url = await self.proxy_manager.get_proxy_url()

        print(f"🔍 开始激活Sora2邀请码: {invite_code}")
        print(f"🔑 Access Token 前缀: {access_token[:50]}...")

        async with AsyncSession() as session:
            # 生成设备ID
            device_id = str(uuid.uuid4())

            # 只设置必要的头，让 impersonate 处理其他
            headers = {
                "authorization": f"Bearer {access_token}",
                "cookie": f"oai-did={device_id}"
            }

            print(f"🆔 设备ID: {device_id}")
            print(f"📦 请求体: {{'invite_code': '{invite_code}'}}")

            kwargs = {
                "headers": headers,
                "json": {"invite_code": invite_code},
                "timeout": 30,
                "impersonate": "chrome120"  # 使用 chrome120 让库自动处理 UA 等头
            }

            if proxy_url:
                kwargs["proxy"] = proxy_url
                print(f"🌐 使用代理: {proxy_url}")

            response = await session.post(
                "https://sora.chatgpt.com/backend/project_y/invite/accept",
                **kwargs
            )

            print(f"📥 响应状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Sora2激活成功: {data}")
                return {
                    "success": data.get("success", False),
                    "already_accepted": data.get("already_accepted", False)
                }
            else:
                print(f"❌ Sora2激活失败: {response.status_code}")
                print(f"📄 响应内容: {response.text[:500]}")
                raise Exception(f"Failed to activate Sora2: {response.status_code}")

    async def st_to_at(self, session_token: str) -> dict:
        """Convert Session Token to Access Token"""
        proxy_url = await self.proxy_manager.get_proxy_url()

        async with AsyncSession() as session:
            headers = {
                "Cookie": f"__Secure-next-auth.session-token={session_token}",
                "Accept": "application/json",
                "Origin": "https://sora.chatgpt.com",
                "Referer": "https://sora.chatgpt.com/"
            }

            kwargs = {
                "headers": headers,
                "timeout": 30,
                "impersonate": "chrome"  # 自动生成 User-Agent 和浏览器指纹
            }

            if proxy_url:
                kwargs["proxy"] = proxy_url

            response = await session.get(
                "https://sora.chatgpt.com/api/auth/session",
                **kwargs
            )

            if response.status_code != 200:
                raise ValueError(f"Failed to convert ST to AT: {response.status_code}")

            data = response.json()
            return {
                "access_token": data.get("accessToken"),
                "email": data.get("user", {}).get("email"),
                "expires": data.get("expires")
            }
    
    async def rt_to_at(self, refresh_token: str) -> dict:
        """Convert Refresh Token to Access Token"""
        proxy_url = await self.proxy_manager.get_proxy_url()

        async with AsyncSession() as session:
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }

            kwargs = {
                "headers": headers,
                "json": {
                    "client_id": "app_LlGpXReQgckcGGUo2JrYvtJK",
                    "grant_type": "refresh_token",
                    "redirect_uri": "com.openai.chat://auth0.openai.com/ios/com.openai.chat/callback",
                    "refresh_token": refresh_token
                },
                "timeout": 30,
                "impersonate": "chrome"  # 自动生成 User-Agent 和浏览器指纹
            }

            if proxy_url:
                kwargs["proxy"] = proxy_url

            response = await session.post(
                "https://auth.openai.com/oauth/token",
                **kwargs
            )

            if response.status_code != 200:
                raise ValueError(f"Failed to convert RT to AT: {response.status_code} - {response.text}")

            data = response.json()
            return {
                "access_token": data.get("access_token"),
                "refresh_token": data.get("refresh_token"),
                "expires_in": data.get("expires_in")
            }
    
    async def add_token(self, token_value: str,
                       st: Optional[str] = None,
                       rt: Optional[str] = None,
                       remark: Optional[str] = None,
                       update_if_exists: bool = False) -> Token:
        """Add a new Access Token to database

        Args:
            token_value: Access Token
            st: Session Token (optional)
            rt: Refresh Token (optional)
            remark: Remark (optional)
            update_if_exists: If True, update existing token instead of raising error

        Returns:
            Token object

        Raises:
            ValueError: If token already exists and update_if_exists is False
        """
        # Check if token already exists
        existing_token = await self.db.get_token_by_value(token_value)
        if existing_token:
            if not update_if_exists:
                raise ValueError(f"Token 已存在（邮箱: {existing_token.email}）。如需更新，请先删除旧 Token 或使用更新功能。")
            # Update existing token
            return await self.update_existing_token(existing_token.id, token_value, st, rt, remark)

        # Decode JWT to get expiry time and email
        decoded = await self.decode_jwt(token_value)

        # Extract expiry time from JWT
        expiry_time = datetime.fromtimestamp(decoded.get("exp", 0)) if "exp" in decoded else None

        # Extract email from JWT (OpenAI JWT format)
        jwt_email = None
        if "https://api.openai.com/profile" in decoded:
            jwt_email = decoded["https://api.openai.com/profile"].get("email")

        # Get user info from Sora API
        try:
            user_info = await self.get_user_info(token_value)
            email = user_info.get("email", jwt_email or "")
            name = user_info.get("name") or ""
        except Exception as e:
            # If API call fails, use JWT data
            email = jwt_email or ""
            name = email.split("@")[0] if email else ""

        # Get subscription info from Sora API
        plan_type = None
        plan_title = None
        subscription_end = None
        try:
            sub_info = await self.get_subscription_info(token_value)
            plan_type = sub_info.get("plan_type")
            plan_title = sub_info.get("plan_title")
            # Parse subscription end time
            if sub_info.get("subscription_end"):
                from dateutil import parser
                subscription_end = parser.parse(sub_info["subscription_end"])
        except Exception as e:
            # If API call fails, subscription info will be None
            print(f"Failed to get subscription info: {e}")

        # Get Sora2 invite code
        sora2_supported = None
        sora2_invite_code = None
        sora2_redeemed_count = 0
        sora2_total_count = 0
        try:
            sora2_info = await self.get_sora2_invite_code(token_value)
            sora2_supported = sora2_info.get("supported", False)
            sora2_invite_code = sora2_info.get("invite_code")
            sora2_redeemed_count = sora2_info.get("redeemed_count", 0)
            sora2_total_count = sora2_info.get("total_count", 0)
        except Exception as e:
            # If API call fails, Sora2 info will be None
            print(f"Failed to get Sora2 info: {e}")

        # Create token object
        token = Token(
            token=token_value,
            email=email,
            name=name,
            st=st,
            rt=rt,
            remark=remark,
            expiry_time=expiry_time,
            is_active=True,
            plan_type=plan_type,
            plan_title=plan_title,
            subscription_end=subscription_end,
            sora2_supported=sora2_supported,
            sora2_invite_code=sora2_invite_code,
            sora2_redeemed_count=sora2_redeemed_count,
            sora2_total_count=sora2_total_count
        )

        # Save to database
        token_id = await self.db.add_token(token)
        token.id = token_id

        return token

    async def update_existing_token(self, token_id: int, token_value: str,
                                    st: Optional[str] = None,
                                    rt: Optional[str] = None,
                                    remark: Optional[str] = None) -> Token:
        """Update an existing token with new information"""
        # Decode JWT to get expiry time
        decoded = await self.decode_jwt(token_value)
        expiry_time = datetime.fromtimestamp(decoded.get("exp", 0)) if "exp" in decoded else None

        # Get user info from Sora API
        jwt_email = None
        if "https://api.openai.com/profile" in decoded:
            jwt_email = decoded["https://api.openai.com/profile"].get("email")

        try:
            user_info = await self.get_user_info(token_value)
            email = user_info.get("email", jwt_email or "")
            name = user_info.get("name", "")
        except Exception as e:
            email = jwt_email or ""
            name = email.split("@")[0] if email else ""

        # Get subscription info from Sora API
        plan_type = None
        plan_title = None
        subscription_end = None
        try:
            sub_info = await self.get_subscription_info(token_value)
            plan_type = sub_info.get("plan_type")
            plan_title = sub_info.get("plan_title")
            if sub_info.get("subscription_end"):
                from dateutil import parser
                subscription_end = parser.parse(sub_info["subscription_end"])
        except Exception as e:
            print(f"Failed to get subscription info: {e}")

        # Update token in database
        await self.db.update_token(
            token_id=token_id,
            token=token_value,
            st=st,
            rt=rt,
            remark=remark,
            expiry_time=expiry_time,
            plan_type=plan_type,
            plan_title=plan_title,
            subscription_end=subscription_end
        )

        # Get updated token
        updated_token = await self.db.get_token(token_id)
        return updated_token

    async def delete_token(self, token_id: int):
        """Delete a token"""
        await self.db.delete_token(token_id)

    async def update_token(self, token_id: int,
                          token: Optional[str] = None,
                          st: Optional[str] = None,
                          rt: Optional[str] = None,
                          remark: Optional[str] = None):
        """Update token (AT, ST, RT, remark)"""
        # If token (AT) is updated, decode JWT to get new expiry time
        expiry_time = None
        if token:
            try:
                decoded = await self.decode_jwt(token)
                expiry_time = datetime.fromtimestamp(decoded.get("exp", 0)) if "exp" in decoded else None
            except Exception:
                pass  # If JWT decode fails, keep expiry_time as None

        await self.db.update_token(token_id, token=token, st=st, rt=rt, remark=remark, expiry_time=expiry_time)

    async def get_active_tokens(self) -> List[Token]:
        """Get all active tokens (not cooled down)"""
        return await self.db.get_active_tokens()
    
    async def get_all_tokens(self) -> List[Token]:
        """Get all tokens"""
        return await self.db.get_all_tokens()
    
    async def update_token_status(self, token_id: int, is_active: bool):
        """Update token active status"""
        await self.db.update_token_status(token_id, is_active)

    async def enable_token(self, token_id: int):
        """Enable a token and reset error count"""
        await self.db.update_token_status(token_id, True)
        # Reset error count when enabling (in token_stats table)
        await self.db.reset_error_count(token_id)

    async def disable_token(self, token_id: int):
        """Disable a token"""
        await self.db.update_token_status(token_id, False)

    async def test_token(self, token_id: int) -> dict:
        """Test if a token is valid by calling Sora API and refresh Sora2 info"""
        # Get token from database
        token_data = await self.db.get_token(token_id)
        if not token_data:
            return {"valid": False, "message": "Token not found"}

        try:
            # Try to get user info from Sora API
            user_info = await self.get_user_info(token_data.token)

            # Refresh Sora2 invite code and counts
            sora2_info = await self.get_sora2_invite_code(token_data.token)
            sora2_supported = sora2_info.get("supported", False)
            sora2_invite_code = sora2_info.get("invite_code")
            sora2_redeemed_count = sora2_info.get("redeemed_count", 0)
            sora2_total_count = sora2_info.get("total_count", 0)

            # Update token Sora2 info in database
            await self.db.update_token_sora2(
                token_id,
                supported=sora2_supported,
                invite_code=sora2_invite_code,
                redeemed_count=sora2_redeemed_count,
                total_count=sora2_total_count
            )

            return {
                "valid": True,
                "message": "Token is valid",
                "email": user_info.get("email"),
                "username": user_info.get("username"),
                "sora2_supported": sora2_supported,
                "sora2_invite_code": sora2_invite_code,
                "sora2_redeemed_count": sora2_redeemed_count,
                "sora2_total_count": sora2_total_count
            }
        except Exception as e:
            return {
                "valid": False,
                "message": f"Token is invalid: {str(e)}"
            }

    async def record_usage(self, token_id: int, is_video: bool = False):
        """Record token usage"""
        await self.db.update_token_usage(token_id)
        
        if is_video:
            await self.db.increment_video_count(token_id)
        else:
            await self.db.increment_image_count(token_id)
    
    async def record_error(self, token_id: int):
        """Record token error"""
        await self.db.increment_error_count(token_id)
        
        # Check if should ban
        stats = await self.db.get_token_stats(token_id)
        admin_config = await self.db.get_admin_config()
        
        if stats and stats.error_count >= admin_config.error_ban_threshold:
            await self.db.update_token_status(token_id, False)
    
    async def record_success(self, token_id: int):
        """Record successful request (reset error count)"""
        await self.db.reset_error_count(token_id)
    
    async def check_and_apply_cooldown(self, token_id: int):
        """Check if token should be cooled down"""
        stats = await self.db.get_token_stats(token_id)
        admin_config = await self.db.get_admin_config()
        
        if stats and stats.video_count >= admin_config.video_cooldown_threshold:
            # Apply 12 hour cooldown
            cooled_until = datetime.now() + timedelta(hours=12)
            await self.db.update_token_cooldown(token_id, cooled_until)
