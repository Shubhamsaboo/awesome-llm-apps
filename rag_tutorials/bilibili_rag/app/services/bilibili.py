"""
Bilibili RAG 知识库系统

B站 API 服务模块
"""
import httpx
import qrcode
import io
import base64
from typing import Optional, Dict, Any, List
from loguru import logger
from app.services.wbi import wbi_signer


class BilibiliService:
    """B站 API 服务封装"""

    BASE_URL = "https://api.bilibili.com"
    PASSPORT_URL = "https://passport.bilibili.com"

    # 通用请求头
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.bilibili.com/",
        "Origin": "https://www.bilibili.com"
    }

    def __init__(self, sessdata: str = None, bili_jct: str = None, dedeuserid: str = None):
        """
        初始化 B站服务

        Args:
            sessdata: B站登录后的 SESSDATA cookie
            bili_jct: B站登录后的 bili_jct cookie (csrf token)
            dedeuserid: B站用户 ID
        """
        self.sessdata = sessdata
        self.bili_jct = bili_jct
        self.dedeuserid = dedeuserid
        self.client = httpx.AsyncClient(timeout=30.0, headers=self.HEADERS)

    def _get_cookies(self) -> Dict[str, str]:
        """获取 Cookie"""
        cookies = {}
        if self.sessdata:
            cookies["SESSDATA"] = self.sessdata
        if self.bili_jct:
            cookies["bili_jct"] = self.bili_jct
        if self.dedeuserid:
            cookies["DedeUserID"] = self.dedeuserid
        return cookies

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

    # ==================== 登录相关 ====================

    async def generate_qrcode(self) -> Dict[str, Any]:
        """
        生成登录二维码

        Returns:
            {
                "qrcode_key": "二维码 key",
                "qrcode_url": "二维码内容 URL",
                "qrcode_image_base64": "二维码图片 base64"
            }
        """
        url = f"{self.PASSPORT_URL}/x/passport-login/web/qrcode/generate"
        response = await self.client.get(url)
        data = response.json()

        if data["code"] != 0:
            raise Exception(f"生成二维码失败: {data['message']}")

        qrcode_key = data["data"]["qrcode_key"]
        qrcode_url = data["data"]["url"]

        # 生成二维码图片
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(qrcode_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # 转为 base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        return {
            "qrcode_key": qrcode_key,
            "qrcode_url": qrcode_url,
            "qrcode_image_base64": f"data:image/png;base64,{img_base64}"
        }

    async def poll_qrcode_status(self, qrcode_key: str) -> Dict[str, Any]:
        """
        轮询二维码登录状态

        Args:
            qrcode_key: 二维码 key

        Returns:
            {
                "status": "waiting" | "scanned" | "confirmed" | "expired",
                "message": "状态描述",
                "cookies": {...} (仅在 confirmed 时有值)
            }
        """
        url = f"{self.PASSPORT_URL}/x/passport-login/web/qrcode/poll"
        response = await self.client.get(url, params={"qrcode_key": qrcode_key})
        data = response.json()

        if data["code"] != 0:
            raise Exception(f"轮询二维码状态失败: {data['message']}")

        inner_code = data["data"]["code"]
        message = data["data"]["message"]

        status_map = {
            86101: ("waiting", "等待扫码"),
            86090: ("scanned", "已扫码，等待确认"),
            86038: ("expired", "二维码已过期"),
            0: ("confirmed", "登录成功")
        }

        status, msg = status_map.get(inner_code, ("unknown", message))

        result = {
            "status": status,
            "message": msg
        }

        # 登录成功时，从响应头中提取 cookies
        if status == "confirmed":
            cookies = {}
            for cookie in response.cookies.jar:
                cookies[cookie.name] = cookie.value

            # 也可能在 URL 中
            url_str = data["data"].get("url", "")
            if "SESSDATA=" in url_str:
                # 从 URL 解析 cookies
                import urllib.parse
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url_str).query)
                for key in ["SESSDATA", "bili_jct", "DedeUserID"]:
                    if key in parsed:
                        cookies[key] = parsed[key][0]

            result["cookies"] = cookies
            result["refresh_token"] = data["data"].get("refresh_token", "")

        return result

    async def get_user_info(self) -> Dict[str, Any]:
        """
        获取当前登录用户信息

        Returns:
            用户信息字典
        """
        url = f"{self.BASE_URL}/x/web-interface/nav"
        response = await self.client.get(url, cookies=self._get_cookies())
        data = response.json()

        if data["code"] != 0:
            raise Exception(f"获取用户信息失败: {data['message']}")

        return data["data"]

    # ==================== 收藏夹相关 ====================

    async def get_user_favorites(self, mid: int = None) -> List[Dict[str, Any]]:
        """
        获取用户的所有收藏夹

        Args:
            mid: 用户 ID，不传则使用当前登录用户

        Returns:
            收藏夹列表
        """
        if mid is None:
            mid = self.dedeuserid

        if not mid:
            raise Exception("未指定用户 ID")

        url = f"{self.BASE_URL}/x/v3/fav/folder/created/list-all"
        params = {"up_mid": mid}

        response = await self.client.get(url, params=params, cookies=self._get_cookies())
        data = response.json()

        if data["code"] != 0:
            raise Exception(f"获取收藏夹失败: {data['message']}")

        return data["data"]["list"] or []

    async def get_favorite_content(
        self,
        media_id: int,
        pn: int = 1,
        ps: int = 20
    ) -> Dict[str, Any]:
        """
        获取收藏夹内容

        Args:
            media_id: 收藏夹 ID
            pn: 页码
            ps: 每页数量 (最大20)

        Returns:
            {
                "info": 收藏夹信息,
                "medias": 视频列表,
                "has_more": 是否有更多
            }
        """
        url = f"{self.BASE_URL}/x/v3/fav/resource/list"
        params = {
            "media_id": media_id,
            "pn": pn,
            "ps": min(ps, 20),
            "platform": "web"
        }

        response = await self.client.get(url, params=params, cookies=self._get_cookies())
        data = response.json()

        if data["code"] != 0:
            raise Exception(f"获取收藏夹内容失败: {data['message']}")

        return {
            "info": data["data"]["info"],
            "medias": data["data"]["medias"] or [],
            "has_more": data["data"]["has_more"]
        }

    async def get_all_favorite_videos(self, media_id: int) -> List[Dict[str, Any]]:
        """
        获取收藏夹的所有视频

        Args:
            media_id: 收藏夹 ID

        Returns:
            完整视频列表
        """
        all_videos = []
        pn = 1

        while True:
            result = await self.get_favorite_content(media_id, pn=pn, ps=20)
            all_videos.extend(result["medias"])

            if not result["has_more"]:
                break
            pn += 1

            # 避免请求过快
            import asyncio
            await asyncio.sleep(0.3)

        return all_videos

    async def move_favorite_resources(
        self,
        src_media_id: int,
        tar_media_id: int,
        resources: List[str],
    ) -> Dict[str, Any]:
        """
        批量移动收藏夹内容

        Args:
            src_media_id: 源收藏夹 ID
            tar_media_id: 目标收藏夹 ID
            resources: ["avid:type", ...]
        """
        if not self.bili_jct:
            raise Exception("缺少 bili_jct，无法进行收藏夹移动")

        if not resources:
            return {"moved": 0}

        url = f"{self.BASE_URL}/x/v3/fav/resource/move"
        data = {
            "src_media_id": src_media_id,
            "tar_media_id": tar_media_id,
            "resources": ",".join(resources),
            "csrf": self.bili_jct,
        }
        if self.dedeuserid:
            data["mid"] = self.dedeuserid

        response = await self.client.post(url, data=data, cookies=self._get_cookies())
        result = response.json()
        if result.get("code") != 0:
            raise Exception(f"移动收藏夹内容失败: {result.get('message')}")
        return result.get("data") or {}

    async def clean_favorite_resources(self, media_id: int) -> Dict[str, Any]:
        """
        清理收藏夹失效内容
        """
        if not self.bili_jct:
            raise Exception("缺少 bili_jct，无法清理失效内容")

        url = f"{self.BASE_URL}/x/v3/fav/resource/clean"
        data = {"media_id": media_id, "csrf": self.bili_jct}
        response = await self.client.post(url, data=data, cookies=self._get_cookies())
        result = response.json()
        if result.get("code") != 0:
            raise Exception(f"清理失效内容失败: {result.get('message')}")
        return result.get("data") or {}

    # ==================== 视频信息相关 ====================

    async def get_video_info(self, bvid: str) -> Dict[str, Any]:
        """
        获取视频详细信息

        Args:
            bvid: 视频 BV 号

        Returns:
            视频信息字典
        """
        url = f"{self.BASE_URL}/x/web-interface/view"
        params = {"bvid": bvid}

        response = await self.client.get(url, params=params, cookies=self._get_cookies())
        data = response.json()

        if data["code"] != 0:
            raise Exception(f"获取视频信息失败: {data['message']}")

        return data["data"]

    async def get_video_summary(self, bvid: str, cid: int, up_mid: int = None) -> Dict[str, Any]:
        """
        获取视频 AI 摘要

        Args:
            bvid: 视频 BV 号
            cid: 视频 cid
            up_mid: UP主 ID (可选)

        Returns:
            AI 摘要信息
        """
        url = f"{self.BASE_URL}/x/web-interface/view/conclusion/get"

        params = {
            "bvid": bvid,
            "cid": cid,
        }
        if up_mid:
            params["up_mid"] = up_mid

        # 需要 Wbi 签名
        signed_params = await wbi_signer.sign(params, cookies=self._get_cookies())

        response = await self.client.get(
            url,
            params=signed_params,
            cookies=self._get_cookies()
        )
        data = response.json()

        if data["code"] != 0:
            logger.warning(f"获取视频摘要失败 [{bvid}]: {data.get('message', 'unknown error')}")
            return None

        return data["data"]

    async def get_player_info(self, bvid: str, cid: int, aid: int = None) -> Dict[str, Any]:
        """
        获取播放器信息（包含字幕信息）

        Args:
            bvid: 视频 BV 号
            cid: 视频 cid
            aid: 视频 aid (可选)

        Returns:
            播放器信息
        """
        params = {
            "bvid": bvid,
            "cid": cid,
        }
        if aid:
            params["aid"] = aid

        # 优先使用 WBI 版本，提高字幕获取成功率
        try:
            cookies = self._get_cookies()
            cookies_for_sign = cookies if cookies else None
            signed_params = await wbi_signer.sign(params, cookies=cookies_for_sign)
            wbi_url = f"{self.BASE_URL}/x/player/wbi/v2"
            response = await self.client.get(wbi_url, params=signed_params, cookies=cookies)
            data = response.json()
            if data.get("code") == 0:
                return data.get("data")
            logger.warning(f"WBI 播放器信息失败 [{bvid}]: {data.get('message', 'unknown error')}")
        except Exception as e:
            logger.warning(f"WBI 播放器信息异常 [{bvid}]: {e}")

        # 回退到普通接口
        url = f"{self.BASE_URL}/x/player/v2"
        response = await self.client.get(url, params=params, cookies=self._get_cookies())
        data = response.json()

        if data["code"] != 0:
            logger.warning(f"获取播放器信息失败 [{bvid}]: {data.get('message', 'unknown error')}")
            return None

        return data["data"]

    async def get_audio_url(self, bvid: str, cid: int) -> Optional[str]:
        """
        获取音频流 URL（用于 ASR）

        Args:
            bvid: 视频 BV 号
            cid: 视频 cid

        Returns:
            音频 URL（可能为空）
        """
        params = {
            "bvid": bvid,
            "cid": cid,
            "fnval": 16,
            "fnver": 0,
            "fourk": 1,
        }

        cookies = self._get_cookies()
        cookies_for_sign = cookies if cookies else None

        # 优先使用 WBI 接口
        try:
            signed_params = await wbi_signer.sign(params, cookies=cookies_for_sign)
            url = f"{self.BASE_URL}/x/player/wbi/playurl"
            response = await self.client.get(url, params=signed_params, cookies=cookies)
            data = response.json()
        except Exception as e:
            logger.warning(f"获取音频信息失败(WBI) [{bvid}]: {e}")
            data = None

        # 回退到普通接口
        if not data or data.get("code") != 0:
            try:
                url = f"{self.BASE_URL}/x/player/playurl"
                response = await self.client.get(url, params=params, cookies=cookies)
                data = response.json()
            except Exception as e:
                logger.warning(f"获取音频信息失败 [{bvid}]: {e}")
                return None

        if data.get("code") != 0:
            logger.warning(f"获取音频信息失败 [{bvid}]: {data.get('message', 'unknown error')}")
            return None

        payload = data.get("data") or {}
        dash = payload.get("dash") or {}
        audio_list = dash.get("audio") or []
        if audio_list:
            def _bw(item) -> int:
                value = item.get("bandwidth") or item.get("bandWidth") or 0
                try:
                    return int(value)
                except Exception:
                    return 0

            # 优先选择 <= 96kbps 的最高档，兼顾速度与识别效果；否则选最低带宽兜底
            max_bw = 64_000
            candidates = [a for a in audio_list if _bw(a) > 0]
            if candidates:
                preferred = [a for a in candidates if _bw(a) <= max_bw]
                if preferred:
                    best = max(preferred, key=_bw)
                else:
                    best = min(candidates, key=_bw)
            else:
                best = audio_list[0]
            return best.get("baseUrl") or best.get("base_url") or best.get("url")

        durl = payload.get("durl") or []
        if durl:
            return durl[0].get("url")

        return None

    async def download_subtitle(self, subtitle_url: str) -> str:
        """
        下载字幕文件

        Args:
            subtitle_url: 字幕 URL

        Returns:
            字幕文本
        """
        # 处理协议
        if subtitle_url.startswith("//"):
            subtitle_url = "https:" + subtitle_url

        response = await self.client.get(subtitle_url)
        data = response.json()

        # 拼接字幕文本
        texts = []
        for item in data.get("body", []):
            content = item.get("content", "")
            if content:
                texts.append(content)

        return "\n".join(texts)

    async def download_audio_to_file(self, audio_url: str, file_path: str) -> bool:
        """
        下载音频流到本地文件（带 Cookie 与 Referer）

        Args:
            audio_url: 音频 URL
            file_path: 本地保存路径

        Returns:
            是否下载成功
        """
        if not audio_url:
            return False

        headers = dict(self.HEADERS)
        cookies = self._get_cookies()

        try:
            async with self.client.stream(
                "GET", audio_url, headers=headers, cookies=cookies
            ) as resp:
                if resp.status_code not in (200, 206):
                    logger.warning(
                        f"下载音频失败: status_code={resp.status_code} url={audio_url}"
                    )
                    return False
                with open(file_path, "wb") as f:
                    async for chunk in resp.aiter_bytes():
                        if not chunk:
                            continue
                        f.write(chunk)
            return True
        except Exception as e:
            logger.warning(f"下载音频异常: {e}")
            return False
