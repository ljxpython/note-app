"""
笔记服务主模块
"""
from fastapi import FastAPI, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uvicorn
import asyncio
import logging

# 暂时注释掉复杂的导入，使用简化版本
# from .database import get_db, init_db
# from .models import Note, NoteCreate, NoteUpdate, NoteResponse, NoteListResponse
# from .search_service import SearchService
# from .file_service import FileService
from ...shared.config.settings import get_settings
from ...shared.models.base import APIResponse, PaginationParams, PaginationResponse
from ...shared.utils.auth import get_current_user_from_token

settings = get_settings()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="NoteAI Note Service",
    description="笔记管理和搜索服务",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.security.cors_origins,
    allow_credentials=settings.security.cors_allow_credentials,
    allow_methods=settings.security.cors_allow_methods,
    allow_headers=settings.security.cors_allow_headers,
)

# 全局服务实例
search_service: SearchService = None
file_service: FileService = None


@app.on_event("startup")
async def startup_event():
    """启动事件"""
    global search_service, file_service
    
    try:
        # 初始化数据库
        await init_db()
        
        # 初始化搜索服务
        search_service = SearchService()
        await search_service.initialize()
        
        # 初始化文件服务
        file_service = FileService()
        await file_service.initialize()
        
        logger.info("Note Service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start Note Service: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    try:
        if search_service:
            await search_service.close()
        if file_service:
            await file_service.close()
        logger.info("Note Service shutdown successfully")
    except Exception as e:
        logger.error(f"Error during Note Service shutdown: {e}")


@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 检查数据库连接
        db_status = await check_database_health()
        
        # 检查搜索服务
        search_status = await search_service.health_check() if search_service else False
        
        return {
            "status": "healthy" if db_status and search_status else "unhealthy",
            "service": "note_service",
            "database": db_status,
            "search": search_status,
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "note_service",
            "error": str(e),
            "timestamp": asyncio.get_event_loop().time()
        }


@app.post("/api/v1/notes", response_model=APIResponse)
async def create_note(
    note_data: NoteCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user_from_token),
    db = Depends(get_db)
):
    """创建笔记"""
    try:
        user_id = current_user["user_id"]
        
        # 创建笔记文档
        note_doc = {
            "user_id": user_id,
            "title": note_data.title,
            "content": note_data.content,
            "category_id": note_data.category_id,
            "tags": note_data.tags,
            "is_public": note_data.is_public,
            "status": "draft",
            "created_at": asyncio.get_event_loop().time(),
            "updated_at": asyncio.get_event_loop().time()
        }
        
        # 处理内容
        note_doc["content_html"] = await render_markdown(note_data.content)
        note_doc["excerpt"] = generate_excerpt(note_data.content)
        note_doc["word_count"] = len(note_data.content)
        note_doc["character_count"] = len(note_data.content)
        note_doc["reading_time"] = calculate_reading_time(note_data.content)
        
        # 插入到数据库
        result = await db.notes.insert_one(note_doc)
        note_doc["_id"] = result.inserted_id
        
        # 后台任务：添加到搜索索引
        background_tasks.add_task(
            index_note_for_search,
            str(result.inserted_id),
            note_doc
        )
        
        # 后台任务：AI自动分类
        if not note_data.category_id and note_data.content:
            background_tasks.add_task(
                auto_classify_note,
                str(result.inserted_id),
                note_data.content,
                user_id
            )
        
        # 转换为响应格式
        note_response = NoteResponse(
            id=str(result.inserted_id),
            **{k: v for k, v in note_doc.items() if k != "_id"}
        )
        
        return APIResponse(
            success=True,
            data=note_response,
            message="笔记创建成功"
        )
        
    except Exception as e:
        logger.error(f"Failed to create note for user {current_user.get('user_id')}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建笔记失败: {str(e)}"
        )


@app.get("/api/v1/notes", response_model=APIResponse)
async def get_notes(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    category_id: Optional[str] = Query(None, description="分类ID"),
    tags: Optional[List[str]] = Query(None, description="标签过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[str] = Query(None, description="状态过滤"),
    sort_by: str = Query("updated_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    current_user: dict = Depends(get_current_user_from_token),
    db = Depends(get_db)
):
    """获取笔记列表"""
    try:
        user_id = current_user["user_id"]
        
        # 构建查询条件
        query = {"user_id": user_id, "status": {"$ne": "deleted"}}
        
        if category_id:
            query["category_id"] = category_id
        
        if tags:
            query["tags"] = {"$in": tags}
        
        if status:
            query["status"] = status
        
        if search:
            # 如果有搜索关键词，使用搜索服务
            search_results = await search_service.search_notes(
                query=search,
                user_id=user_id,
                page=page,
                limit=limit,
                filters={
                    "category_id": category_id,
                    "tags": tags,
                    "status": status
                }
            )
            
            return APIResponse(
                success=True,
                data=search_results,
                message="搜索完成"
            )
        
        # 计算分页
        skip = (page - 1) * limit
        
        # 构建排序
        sort_direction = -1 if sort_order == "desc" else 1
        sort_spec = [(sort_by, sort_direction)]
        
        # 执行查询
        cursor = db.notes.find(query).sort(sort_spec).skip(skip).limit(limit)
        notes = await cursor.to_list(length=limit)
        
        # 获取总数
        total = await db.notes.count_documents(query)
        
        # 转换为响应格式
        note_responses = []
        for note in notes:
            note_response = NoteResponse(
                id=str(note["_id"]),
                **{k: v for k, v in note.items() if k != "_id"}
            )
            note_responses.append(note_response)
        
        # 构建分页信息
        pagination = PaginationResponse.create(page, limit, total)
        
        return APIResponse(
            success=True,
            data={
                "notes": note_responses,
                "pagination": pagination
            },
            message="获取笔记列表成功"
        )
        
    except Exception as e:
        logger.error(f"Failed to get notes for user {current_user.get('user_id')}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取笔记列表失败: {str(e)}"
        )


@app.get("/api/v1/notes/{note_id}", response_model=APIResponse)
async def get_note(
    note_id: str,
    current_user: dict = Depends(get_current_user_from_token),
    db = Depends(get_db)
):
    """获取单个笔记"""
    try:
        from bson import ObjectId
        
        # 查找笔记
        note = await db.notes.find_one({
            "_id": ObjectId(note_id),
            "user_id": current_user["user_id"]
        })
        
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="笔记不存在"
            )
        
        # 转换为响应格式
        note_response = NoteResponse(
            id=str(note["_id"]),
            **{k: v for k, v in note.items() if k != "_id"}
        )
        
        return APIResponse(
            success=True,
            data=note_response,
            message="获取笔记成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get note {note_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取笔记失败: {str(e)}"
        )


@app.put("/api/v1/notes/{note_id}", response_model=APIResponse)
async def update_note(
    note_id: str,
    note_data: NoteUpdate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user_from_token),
    db = Depends(get_db)
):
    """更新笔记"""
    try:
        from bson import ObjectId
        
        # 构建更新数据
        update_data = {"updated_at": asyncio.get_event_loop().time()}
        
        # 只更新提供的字段
        for field, value in note_data.dict(exclude_unset=True).items():
            if field == "content":
                update_data["content"] = value
                update_data["content_html"] = await render_markdown(value)
                update_data["excerpt"] = generate_excerpt(value)
                update_data["word_count"] = len(value)
                update_data["character_count"] = len(value)
                update_data["reading_time"] = calculate_reading_time(value)
            else:
                update_data[field] = value
        
        # 更新笔记
        result = await db.notes.update_one(
            {"_id": ObjectId(note_id), "user_id": current_user["user_id"]},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="笔记不存在"
            )
        
        # 获取更新后的笔记
        updated_note = await db.notes.find_one({"_id": ObjectId(note_id)})
        
        # 后台任务：更新搜索索引
        background_tasks.add_task(
            update_search_index,
            note_id,
            updated_note
        )
        
        # 转换为响应格式
        note_response = NoteResponse(
            id=str(updated_note["_id"]),
            **{k: v for k, v in updated_note.items() if k != "_id"}
        )
        
        return APIResponse(
            success=True,
            data=note_response,
            message="笔记更新成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update note {note_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新笔记失败: {str(e)}"
        )


@app.delete("/api/v1/notes/{note_id}", response_model=APIResponse)
async def delete_note(
    note_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user_from_token),
    db = Depends(get_db)
):
    """删除笔记（软删除）"""
    try:
        from bson import ObjectId
        
        # 软删除笔记
        result = await db.notes.update_one(
            {"_id": ObjectId(note_id), "user_id": current_user["user_id"]},
            {"$set": {"status": "deleted", "updated_at": asyncio.get_event_loop().time()}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="笔记不存在"
            )
        
        # 后台任务：从搜索索引中删除
        background_tasks.add_task(
            remove_from_search_index,
            note_id
        )
        
        return APIResponse(
            success=True,
            message="笔记删除成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete note {note_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除笔记失败: {str(e)}"
        )


# 工具函数
async def render_markdown(content: str) -> str:
    """渲染Markdown为HTML"""
    try:
        import markdown
        return markdown.markdown(content, extensions=['codehilite', 'tables', 'toc'])
    except Exception as e:
        logger.error(f"Failed to render markdown: {e}")
        return content


def generate_excerpt(content: str, max_length: int = 200) -> str:
    """生成摘要"""
    import re
    # 移除Markdown标记
    clean_content = re.sub(r'[#*`\[\]()]', '', content)
    clean_content = re.sub(r'\n+', ' ', clean_content).strip()
    return clean_content[:max_length] + "..." if len(clean_content) > max_length else clean_content


def calculate_reading_time(content: str) -> int:
    """计算阅读时间（分钟）"""
    # 中文按字符计算，英文按单词计算
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
    english_words = len(re.findall(r'[a-zA-Z]+', content))
    
    # 中文每分钟300字，英文每分钟200词
    reading_time = (chinese_chars / 300) + (english_words / 200)
    return max(1, int(reading_time))


async def check_database_health() -> bool:
    """检查数据库健康状态"""
    try:
        db = await get_db().__anext__()
        await db.notes.find_one({}, {"_id": 1})
        return True
    except Exception:
        return False


# 后台任务函数
async def index_note_for_search(note_id: str, note_data: dict):
    """添加笔记到搜索索引"""
    try:
        if search_service:
            await search_service.index_note(note_id, note_data)
    except Exception as e:
        logger.error(f"Failed to index note {note_id}: {e}")


async def update_search_index(note_id: str, note_data: dict):
    """更新搜索索引"""
    try:
        if search_service:
            await search_service.update_note(note_id, note_data)
    except Exception as e:
        logger.error(f"Failed to update search index for note {note_id}: {e}")


async def remove_from_search_index(note_id: str):
    """从搜索索引中删除"""
    try:
        if search_service:
            await search_service.delete_note(note_id)
    except Exception as e:
        logger.error(f"Failed to remove note {note_id} from search index: {e}")


async def auto_classify_note(note_id: str, content: str, user_id: str):
    """AI自动分类笔记"""
    try:
        # 调用AI服务进行分类
        # 这里简化处理，实际应该调用AI服务API
        logger.info(f"Auto-classifying note {note_id} for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to auto-classify note {note_id}: {e}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.service.note_service_port,
        reload=settings.debug
    )
