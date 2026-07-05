"""
Bilibili RAG 知识库系统

认证路由 - 处理 B站登录
"""
from fastapi import APIRouter, HTTPException, Depends
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db, get_db_context
from app.models import QRCodeResponse, LoginStatusResponse, UserSession as UserSessionModel
from app.services.bilibili import BilibiliService
import uuid

router = APIRouter(prefix="/auth", tags=["认证"])

# 临时存储登录会话（生产环境应使用 Redis）
login_sessions = {}


@router.get("/qrcode", response_model=QRCodeResponse)
async def generate_qrcode():
    """
    生成登录二维码

    返回二维码 key 和 base64 编码的二维码图片
    """
    try:
        bili = BilibiliService()
        result = await bili.generate_qrcode()
        await bili.close()

        # 存储会话
        login_sessions[result["qrcode_key"]] = {
            "status": "waiting"
        }

        return QRCodeResponse(
            qrcode_key=result["qrcode_key"],
            qrcode_url=result["qrcode_url"],
            qrcode_image_base64=result["qrcode_image_base64"]
        )

    except Exception as e:
        logger.error(f"生成二维码失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成二维码失败: {str(e)}")


@router.get("/qrcode/poll/{qrcode_key}", response_model=LoginStatusResponse)
async def poll_qrcode_status(qrcode_key: str, db: AsyncSession = Depends(get_db)):
    """
    轮询二维码登录状态
    """
    from sqlalchemy import select
    from app.models import UserSession as UserSessionModel

    try:
        bili = BilibiliService()
        result = await bili.poll_qrcode_status(qrcode_key)
        await bili.close()

        response = LoginStatusResponse(
            status=result["status"],
            message=result["message"]
        )

        # 登录成功
        if result["status"] == "confirmed":
            cookies = result.get("cookies", {})

            # 创建会话
            session_id = str(uuid.uuid4())

            # 获取用户信息
            bili_auth = BilibiliService(
                sessdata=cookies.get("SESSDATA"),
                bili_jct=cookies.get("bili_jct"),
                dedeuserid=cookies.get("DedeUserID")
            )

            user_info_dict = {}
            try:
                user_info = await bili_auth.get_user_info()
                await bili_auth.close()

                mid = int(user_info.get("mid") or cookies.get("DedeUserID"))

                user_info_dict = {
                    "mid": mid,
                    "uname": user_info.get("uname"),
                    "face": user_info.get("face"),
                    "level": user_info.get("level_info", {}).get("current_level")
                }

                # 持久化到数据库
                db_session = UserSessionModel(
                    session_id=session_id,
                    bili_mid=mid,
                    bili_uname=user_info.get("uname"),
                    bili_face=user_info.get("face"),
                    sessdata=cookies.get("SESSDATA"),
                    bili_jct=cookies.get("bili_jct"),
                    dedeuserid=str(cookies.get("DedeUserID")),
                    is_valid=True
                )
                db.add(db_session)
                await db.commit()

                response.user_info = user_info_dict

            except Exception as e:
                logger.warning(f"获取用户信息失败: {e}")
                response.user_info = {
                    "mid": cookies.get("DedeUserID"),
                    "uname": "未知用户"
                }

            # 内存缓存（为了兼容旧代码）
            login_sessions[session_id] = {
                "cookies": cookies,
                "user_info": user_info_dict,
                "refresh_token": result.get("refresh_token")
            }

            response.session_id = session_id

            # 清理旧的 qrcode_key
            login_sessions.pop(qrcode_key, None)

        return response

    except Exception as e:
        logger.error(f"轮询二维码状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"轮询失败: {str(e)}")


@router.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """
    获取会话信息
    """
    session = login_sessions.get(session_id)
    if not session:
        async with get_db_context() as db:
            result = await db.execute(
                select(UserSessionModel).where(UserSessionModel.session_id == session_id)
            )
            db_session = result.scalar_one_or_none()
        if not db_session or not db_session.is_valid:
            raise HTTPException(status_code=404, detail="会话不存在或已过期")
        session = {
            "cookies": {
                "SESSDATA": db_session.sessdata,
                "bili_jct": db_session.bili_jct,
                "DedeUserID": db_session.dedeuserid,
            },
            "user_info": {
                "mid": db_session.bili_mid,
                "uname": db_session.bili_uname,
                "face": db_session.bili_face,
            },
        }
        login_sessions[session_id] = session

    return {"valid": True, "user_info": session.get("user_info")}


@router.delete("/session/{session_id}")
async def logout(session_id: str):
    """
    退出登录
    """
    if session_id in login_sessions:
        del login_sessions[session_id]

    return {"message": "已退出登录"}


async def get_session(session_id: str) -> dict:
    """
    获取会话信息（内部使用）
    """
    session = login_sessions.get(session_id)
    if session:
        return session

    async with get_db_context() as db:
        result = await db.execute(
            select(UserSessionModel).where(UserSessionModel.session_id == session_id)
        )
        db_session = result.scalar_one_or_none()
        if not db_session or not db_session.is_valid:
            return None
        session = {
            "cookies": {
                "SESSDATA": db_session.sessdata,
                "bili_jct": db_session.bili_jct,
                "DedeUserID": db_session.dedeuserid,
            },
            "user_info": {
                "mid": db_session.bili_mid,
                "uname": db_session.bili_uname,
                "face": db_session.bili_face,
            },
        }

    if session:
        login_sessions[session_id] = session
    return session
