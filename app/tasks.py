from celery import Celery
from datetime import datetime
from typing import List, Dict, Any

from app.core.config import settings
from app.models.database import SessionLocal
from app.models.case import Case
from app.models.report import Report
from app.services.ai_agent_v3 import forensic_service_v3
from app.services.email import send_case_completion_email

# Initialize Celery
celery_app = Celery(
    'falcon',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=1800,  # 30 minutes
    task_soft_time_limit=1500,  # 25 minutes
)


@celery_app.task(name='app.tasks.analyze_case_task')
async def analyze_case_task(
    case_id: int,
    documents_data: List[Dict[str, Any]],
    user_context: Dict[str, Any],
    jurisdiction: str
) -> Dict[str, Any]:
    """
    Async task to perform comprehensive forensic analysis on a case.
    
    Args:
        case_id: ID of the case to analyze
        documents_data: List of document data dictionaries
        user_context: User context information
        jurisdiction: Legal jurisdiction for the case
    
    Returns:
        Analysis results dictionary
    """
    try:
        # Run the Falcon v3.0 forensic analysis
        analysis_result = await forensic_service_v3.analyze_case(
            case_id=case_id,
            documents=documents_data,
            user_context=user_context,
            jurisdiction=jurisdiction
        )
        
        # Generate reports
        executive_report = await forensic_service_v3.generate_report(
            analysis_result, 
            report_type="executive"
        )
        
        confidence_report = await forensic_service_v3.generate_report(
            analysis_result,
            report_type="confidence"
        )
        
        detailed_report = await forensic_service_v3.generate_report(
            analysis_result,
            report_type="detailed"
        )
        
        # Save reports to database
        async with SessionLocal() as db:
            # Create executive summary report
            exec_report = Report(
                case_id=case_id,
                report_type="executive_summary",
                content=executive_report,
                metadata={
                    "confidence_dashboard": analysis_result.confidence_dashboard.dict(),
                    "total_assets": analysis_result.total_assets_value,
                    "net_worth": analysis_result.net_worth,
                    "generated_at": datetime.utcnow().isoformat()
                }
            )
            db.add(exec_report)
            
            # Create confidence analysis report
            conf_report = Report(
                case_id=case_id,
                report_type="confidence_analysis",
                content=confidence_report,
                metadata={
                    "overall_confidence": analysis_result.confidence_dashboard.overall_confidence,
                    "evidence_robustness": analysis_result.evidence_robustness,
                    "objectivity_assessment": analysis_result.objectivity_assessment
                }
            )
            db.add(conf_report)
            
            # Create detailed forensic report
            detail_report = Report(
                case_id=case_id,
                report_type="detailed_forensic",
                content=detailed_report,
                metadata={
                    "analysis_phases": ["constitutional_verification", "sequential_analysis", 
                                      "self_correction", "strategic_output"],
                    "concealment_schemes_detected": len(analysis_result.concealment_schemes),
                    "immediate_actions_count": len(analysis_result.immediate_actions)
                }
            )
            db.add(detail_report)
            
            # Update case status
            case = await db.get(Case, case_id)
            if case:
                case.status = "analysis_complete"
                case.total_assets = analysis_result.total_assets_value
                case.total_liabilities = analysis_result.total_liabilities_amount
                case.updated_at = datetime.utcnow()
            
            await db.commit()
        
        # Send completion email
        await send_case_completion_email(
            to_email=user_context['email'],
            user_name=user_context['full_name'],
            case_id=case_id,
            summary=analysis_result.executive_summary,
            confidence_level=analysis_result.confidence_dashboard.overall_confidence
        )
        
        return {
            "status": "completed",
            "case_id": case_id,
            "reports_generated": ["executive", "confidence", "detailed"],
            "confidence_dashboard": analysis_result.confidence_dashboard.dict(),
            "total_assets": analysis_result.total_assets_value,
            "net_worth": analysis_result.net_worth,
            "immediate_actions": len(analysis_result.immediate_actions),
            "strategic_leverage_points": len(analysis_result.strategic_leverage_points)
        }
        
    except Exception as e:
        # Log the error
        print(f"Error analyzing case {case_id}: {str(e)}")
        
        # Update case status to failed
        async with SessionLocal() as db:
            case = await db.get(Case, case_id)
            if case:
                case.status = "analysis_failed"
                case.updated_at = datetime.utcnow()
                await db.commit()
        
        # Send failure notification
        await send_case_completion_email(
            to_email=user_context['email'],
            user_name=user_context['full_name'],
            case_id=case_id,
            summary=f"Analysis failed: {str(e)}",
            confidence_level="N/A",
            is_error=True
        )
        
        raise


@celery_app.task(name='app.tasks.process_document_task')
async def process_document_task(
    document_id: int,
    file_path: str,
    file_type: str
) -> Dict[str, Any]:
    """
    Async task to process and extract data from uploaded documents.
    
    Args:
        document_id: ID of the document to process
        file_path: Path to the uploaded file
        file_type: Type of document (pdf, excel, csv, etc.)
    
    Returns:
        Extraction results dictionary
    """
    try:
        extracted_data = {}
        
        if file_type == 'pdf':
            # Extract text from PDF
            import pypdf
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                text_content = ""
                for page in pdf_reader.pages:
                    text_content += page.extract_text()
                
                extracted_data = {
                    "text_content": text_content,
                    "page_count": len(pdf_reader.pages),
                    "metadata": pdf_reader.metadata
                }
        
        elif file_type in ['csv', 'xlsx', 'xls']:
            # Extract data from spreadsheet
            import pandas as pd
            df = pd.read_csv(file_path) if file_type == 'csv' else pd.read_excel(file_path)
            
            extracted_data = {
                "row_count": len(df),
                "columns": df.columns.tolist(),
                "summary_stats": df.describe().to_dict() if not df.empty else {},
                "data_preview": df.head(10).to_dict() if not df.empty else {}
            }
        
        # Update document status in database
        async with SessionLocal() as db:
            from app.models.document import Document
            document = await db.get(Document, document_id)
            if document:
                document.status = "processed"
                document.extracted_data = extracted_data
                document.processed_at = datetime.utcnow()
                await db.commit()
        
        return {
            "status": "success",
            "document_id": document_id,
            "extracted_data": extracted_data
        }
        
    except Exception as e:
        # Update document status to failed
        async with SessionLocal() as db:
            from app.models.document import Document
            document = await db.get(Document, document_id)
            if document:
                document.status = "processing_failed"
                document.error_message = str(e)
                await db.commit()
        
        raise