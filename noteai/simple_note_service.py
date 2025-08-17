#!/usr/bin/env python3
"""
简化的笔记服务
"""
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uvicorn
import json
import re
import uuid

app = FastAPI(title="NoteAI Note Service", version="1.0.0")

# 简单的内存存储
notes_db: Dict[str, Dict] = {}
security = HTTPBearer()

# 数据模型
class NoteCreate(BaseModel):
    title: str
    content: str = ""
    category_id: Optional[str] = None
    tags: List[str] = []
    is_public: bool = False

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category_id: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None
    is_public: Optional[bool] = None

class NoteResponse(BaseModel):
    id: str
    user_id: str
    title: str
    content: str
    content_html: str = ""
    excerpt: str = ""
    word_count: int = 0
    reading_time: int = 0
    category_id: Optional[str] = None
    tags: List[str] = []
    status: str = "draft"
    is_public: bool = False
    is_favorite: bool = False
    created_at: str
    updated_at: str

# 工具函数
def render_markdown(content: str) -> str:
    """简单的Markdown渲染"""
    # 简化版本，实际应该使用markdown库
    html = content
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)
    html = html.replace('\n', '<br>')
    return html

def generate_excerpt(content: str, max_length: int = 200) -> str:
    """生成摘要"""
    clean_content = re.sub(r'[#*`\[\]()]', '', content)
    clean_content = re.sub(r'\n+', ' ', clean_content).strip()
    return clean_content[:max_length] + "..." if len(clean_content) > max_length else clean_content

def calculate_reading_time(content: str) -> int:
    """计算阅读时间（分钟）"""
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
    english_words = len(re.findall(r'[a-zA-Z]+', content))
    reading_time = (chinese_chars / 300) + (english_words / 200)
    return max(1, int(reading_time))

def get_current_user(token = Depends(security)) -> Dict[str, str]:
    """简化的用户验证"""
    # 在实际应用中，这里应该验证JWT Token
    # 现在返回模拟用户
    return {"user_id": "test-user-123", "email": "test@example.com"}

# API端点
@app.get("/health")
def health_check():
    return {
        "status": "healthy", 
        "service": "note_service",
        "version": "1.0.0",
        "notes_count": len(notes_db)
    }

@app.post("/api/v1/notes", response_model=Dict[str, Any])
def create_note(
    note_data: NoteCreate,
    current_user: Dict[str, str] = Depends(get_current_user)
):
    """创建笔记"""
    try:
        note_id = str(uuid.uuid4())
        user_id = current_user["user_id"]
        
        # 处理内容
        content_html = render_markdown(note_data.content)
        excerpt = generate_excerpt(note_data.content)
        word_count = len(note_data.content)
        reading_time = calculate_reading_time(note_data.content)
        
        # 创建笔记
        note = {
            "id": note_id,
            "user_id": user_id,
            "title": note_data.title,
            "content": note_data.content,
            "content_html": content_html,
            "excerpt": excerpt,
            "word_count": word_count,
            "reading_time": reading_time,
            "category_id": note_data.category_id,
            "tags": note_data.tags,
            "status": "draft",
            "is_public": note_data.is_public,
            "is_favorite": False,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        notes_db[note_id] = note
        
        return {
            "success": True,
            "data": NoteResponse(**note),
            "message": "笔记创建成功"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建笔记失败: {str(e)}")

@app.get("/api/v1/notes", response_model=Dict[str, Any])
def get_notes(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    category_id: Optional[str] = Query(None, description="分类ID"),
    tags: Optional[str] = Query(None, description="标签过滤，逗号分隔"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[str] = Query(None, description="状态过滤"),
    current_user: Dict[str, str] = Depends(get_current_user)
):
    """获取笔记列表"""
    try:
        user_id = current_user["user_id"]
        
        # 过滤用户的笔记
        user_notes = [
            note for note in notes_db.values() 
            if note["user_id"] == user_id and note["status"] != "deleted"
        ]
        
        # 应用过滤条件
        if category_id:
            user_notes = [note for note in user_notes if note["category_id"] == category_id]
        
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
            user_notes = [
                note for note in user_notes 
                if any(tag in note["tags"] for tag in tag_list)
            ]
        
        if status:
            user_notes = [note for note in user_notes if note["status"] == status]
        
        if search:
            user_notes = [
                note for note in user_notes 
                if search.lower() in note["title"].lower() or search.lower() in note["content"].lower()
            ]
        
        # 排序（按更新时间倒序）
        user_notes.sort(key=lambda x: x["updated_at"], reverse=True)
        
        # 分页
        total = len(user_notes)
        start = (page - 1) * limit
        end = start + limit
        paginated_notes = user_notes[start:end]
        
        # 转换为响应格式
        note_responses = [NoteResponse(**note) for note in paginated_notes]
        
        return {
            "success": True,
            "data": {
                "notes": note_responses,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "total_pages": (total + limit - 1) // limit,
                    "has_next": end < total,
                    "has_prev": page > 1
                }
            },
            "message": "获取笔记列表成功"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取笔记列表失败: {str(e)}")

@app.get("/api/v1/notes/{note_id}", response_model=Dict[str, Any])
def get_note(
    note_id: str,
    current_user: Dict[str, str] = Depends(get_current_user)
):
    """获取单个笔记"""
    try:
        note = notes_db.get(note_id)
        
        if not note:
            raise HTTPException(status_code=404, detail="笔记不存在")
        
        if note["user_id"] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="无权访问此笔记")
        
        return {
            "success": True,
            "data": NoteResponse(**note),
            "message": "获取笔记成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取笔记失败: {str(e)}")

@app.put("/api/v1/notes/{note_id}", response_model=Dict[str, Any])
def update_note(
    note_id: str,
    note_data: NoteUpdate,
    current_user: Dict[str, str] = Depends(get_current_user)
):
    """更新笔记"""
    try:
        note = notes_db.get(note_id)
        
        if not note:
            raise HTTPException(status_code=404, detail="笔记不存在")
        
        if note["user_id"] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="无权修改此笔记")
        
        # 更新字段
        update_data = note_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if field == "content":
                note["content"] = value
                note["content_html"] = render_markdown(value)
                note["excerpt"] = generate_excerpt(value)
                note["word_count"] = len(value)
                note["reading_time"] = calculate_reading_time(value)
            else:
                note[field] = value
        
        note["updated_at"] = datetime.utcnow().isoformat()
        
        return {
            "success": True,
            "data": NoteResponse(**note),
            "message": "笔记更新成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新笔记失败: {str(e)}")

@app.delete("/api/v1/notes/{note_id}", response_model=Dict[str, Any])
def delete_note(
    note_id: str,
    current_user: Dict[str, str] = Depends(get_current_user)
):
    """删除笔记（软删除）"""
    try:
        note = notes_db.get(note_id)
        
        if not note:
            raise HTTPException(status_code=404, detail="笔记不存在")
        
        if note["user_id"] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="无权删除此笔记")
        
        # 软删除
        note["status"] = "deleted"
        note["updated_at"] = datetime.utcnow().isoformat()
        
        return {
            "success": True,
            "message": "笔记删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除笔记失败: {str(e)}")

@app.get("/api/v1/notes/search", response_model=Dict[str, Any])
def search_notes(
    q: str = Query(..., description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: Dict[str, str] = Depends(get_current_user)
):
    """搜索笔记"""
    try:
        user_id = current_user["user_id"]
        
        # 简单的全文搜索
        search_results = []
        for note in notes_db.values():
            if (note["user_id"] == user_id and 
                note["status"] != "deleted" and
                (q.lower() in note["title"].lower() or 
                 q.lower() in note["content"].lower() or
                 any(q.lower() in tag.lower() for tag in note["tags"]))):
                
                # 计算相关性评分（简化版）
                score = 0
                if q.lower() in note["title"].lower():
                    score += 10
                if q.lower() in note["content"].lower():
                    score += 5
                if any(q.lower() in tag.lower() for tag in note["tags"]):
                    score += 3
                
                search_results.append({
                    "note": note,
                    "score": score,
                    "highlights": [q]  # 简化的高亮
                })
        
        # 按相关性排序
        search_results.sort(key=lambda x: x["score"], reverse=True)
        
        # 分页
        total = len(search_results)
        start = (page - 1) * limit
        end = start + limit
        paginated_results = search_results[start:end]
        
        # 格式化结果
        formatted_results = []
        for result in paginated_results:
            note = result["note"]
            formatted_results.append({
                "id": note["id"],
                "title": note["title"],
                "excerpt": note["excerpt"],
                "score": result["score"],
                "highlights": result["highlights"],
                "created_at": note["created_at"],
                "tags": note["tags"]
            })
        
        return {
            "success": True,
            "data": {
                "results": formatted_results,
                "total": total,
                "took": 10,  # 模拟搜索耗时
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "total_pages": (total + limit - 1) // limit,
                    "has_next": end < total,
                    "has_prev": page > 1
                }
            },
            "message": "搜索完成"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

if __name__ == "__main__":
    print("🚀 NoteAI 笔记服务启动")
    print("📖 API文档: http://localhost:8003/docs")
    print("🔍 健康检查: http://localhost:8003/health")
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")
