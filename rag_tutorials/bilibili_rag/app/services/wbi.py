"""
Bilibili RAG 知识库系统

Wbi 签名模块 - 用于 B站 API 鉴权
参考: https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/docs/misc/sign/wbi.md
"""
import time
import hashlib
from urllib.parse import urlencode
from functools import reduce
import httpx
from typing import Optional, Dict


# Wbi 签名用的混淆表
MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
    22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52
]


class WbiSigner:
    """Wbi 签名器"""

    def __init__(self):
        self.img_key: Optional[str] = None
        self.sub_key: Optional[str] = None
        self.mixin_key: Optional[str] = None
        self.last_update: float = 0
        self.update_interval: int = 3600  # 1小时更新一次

    def _get_mixin_key(self, orig: str) -> str:
        """生成混淆后的 key"""
        return reduce(lambda s, i: s + orig[i], MIXIN_KEY_ENC_TAB, '')[:32]

    async def _fetch_wbi_keys(self, cookies: Optional[Dict[str, str]] = None) -> None:
        """从 B站获取 wbi keys"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.bilibili.com/x/web-interface/nav",
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://www.bilibili.com/"
                },
                cookies=cookies,
            )
            data = resp.json()

        if data["code"] != 0:
            raise Exception(f"获取 Wbi keys 失败: {data}")

        wbi_img = data["data"]["wbi_img"]

        # 提取 img_key 和 sub_key
        # img_url 格式: https://i0.hdslb.com/bfs/wbi/xxx.png
        self.img_key = wbi_img["img_url"].rsplit("/", 1)[1].split(".")[0]
        self.sub_key = wbi_img["sub_url"].rsplit("/", 1)[1].split(".")[0]

        # 生成混淆 key
        self.mixin_key = self._get_mixin_key(self.img_key + self.sub_key)
        self.last_update = time.time()

    async def ensure_keys(self, cookies: Optional[Dict[str, str]] = None) -> None:
        """确保 keys 有效"""
        # 如果提供了 cookies，强制刷新 key 以确保权限正确
        # 否则使用缓存
        force_refresh = cookies is not None

        if (
            force_refresh or
            self.mixin_key is None or
            time.time() - self.last_update > self.update_interval
        ):
            await self._fetch_wbi_keys(cookies=cookies)

    def _filter_params(self, params: dict) -> dict:
        """过滤非法字符"""
        return {
            k: "".join(c for c in str(v) if c not in "!'()*")
            for k, v in params.items()
        }

    async def sign(self, params: dict, cookies: Optional[Dict[str, str]] = None) -> dict:
        """对参数进行 Wbi 签名

        Args:
            params: 原始请求参数
            cookies: 登录态 cookies（可选）

        Returns:
            签名后的参数（包含 w_rid 和 wts）
        """
        await self.ensure_keys(cookies=cookies)

        # 过滤参数
        params = self._filter_params(params)

        # 添加时间戳
        params["wts"] = int(time.time())

        # 按 key 排序
        params = dict(sorted(params.items()))

        # 拼接并计算 MD5
        query = urlencode(params)
        w_rid = hashlib.md5((query + self.mixin_key).encode()).hexdigest()

        params["w_rid"] = w_rid
        return params


# 全局签名器实例
wbi_signer = WbiSigner()
