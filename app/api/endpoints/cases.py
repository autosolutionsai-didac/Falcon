from typing import List, Optional
from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel

from app.models.database import get_db
from app.models.case import Case
from app.models.user import User
from app.api.auth.router import get_current_user
from app.core.security import encryption


router = APIRouter(prefix="/cases", tags=["Cases"])


class CaseCreate(BaseModel):
    case_name: str
    client_name: str
    opposing_party: Optional[str] = None
    jurisdiction: Optional[str] = None


class CaseUpdate(BaseModel):
    case_name: Optional[str] = None
    client_name: Optional[str] = None
    opposing_party: Optional[str] = None
    jurisdiction: Optional[str] = None
    status: Optional[str] = None


class CaseResponse(BaseModel):
    id: int
    case_number: str
    case_name: str
    client_name: str
    opposing_party: Optional[str]
    jurisdiction: Optional[str]
    status: str
    total_assets: Optional[float]
    total_liabilities: Optional[float]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


@router.post("/", response_model=CaseResponse)
async def create_case(
    case_data: CaseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new case."""
    # Generate unique case number
    case_number = f"FCN-{datetime.now().year}-{uuid.uuid4().hex[:8].upper()}"
    
    case = Case(
        user_id=current_user.id,
        case_number=case_number,
        case_name=case_data.case_name,
        client_name=case_data.client_name,
        opposing_party=case_data.opposing_party,
        jurisdiction=case_data.jurisdiction or current_user.jurisdiction
    )
    
    db.add(case)
    await db.commit()
    await db.refresh(case)
    
    return case


@router.get("/", response_model=List[CaseResponse])
async def list_cases(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all cases for the current user."""
    query = select(Case).where(Case.user_id == current_user.id)
    
    if status:
        query = query.where(Case.status == status)
    
    query = query.offset(skip).limit(limit).order_by(Case.created_at.desc())
    
    result = await db.execute(query)
    cases = result.scalars().all()
    
    return cases


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific case."""
    result = await db.execute(
        select(Case).where(and_(Case.id == case_id, Case.user_id == current_user.id))
    )
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    return case


@router.put("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: int,
    case_update: CaseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a case."""
    result = await db.execute(
        select(Case).where(and_(Case.id == case_id, Case.user_id == current_user.id))
    )
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    # Update fields
    update_data = case_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(case, field, value)
    
    case.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(case)
    
    return case


@router.delete("/{case_id}")
async def delete_case(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a case and all associated data."""
    result = await db.execute(
        select(Case).where(and_(Case.id == case_id, Case.user_id == current_user.id))
    )
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    # Delete case (cascade will handle documents and reports)
    await db.delete(case)
    await db.commit()
    
    return {"message": "Case deleted successfully"}


@router.post("/{case_id}/analyze")
async def analyze_case(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Trigger AI analysis for a case."""
    result = await db.execute(
        select(Case).where(and_(Case.id == case_id, Case.user_id == current_user.id))
    )
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    # Check if case has documents
    if not case.documents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No documents uploaded for this case"
        )
    
    # Import the enhanced forensic service
    from app.services.ai_agent_v3 import forensic_service_v3
    from app.services.email import send_case_completion_email
    from celery import current_app as celery_app
    
    # Get case documents
    documents_data = []
    for doc in case.documents:
        doc_data = {
            'id': str(doc.id),
            'type': doc.file_type,
            'filename': doc.original_filename,
            'status': doc.status,
            'extracted_data': doc.extracted_data or {}
        }
        documents_data.append(doc_data)
    
    # Trigger async analysis
    task = celery_app.send_task(
        'app.tasks.analyze_case_task',
        args=[
            case_id,
            documents_data,
            {
                'user_id': current_user.id,
                'email': current_user.email,
                'full_name': current_user.full_name
            },
            case.jurisdiction or current_user.jurisdiction or 'California'
        ]
    )
    
    return {
        "message": "Comprehensive forensic analysis started",
        "case_id": case_id,
        "task_id": task.id,
        "estimated_time": "10-15 minutes",
        "analysis_phases": [
            "Phase 1: Constitutional Verification",
            "Phase 2: Sequential Analysis",
            "Phase 3: Self-Correction & Validation",
            "Phase 4: Strategic Output Generation"
        ]
    }
