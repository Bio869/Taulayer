from typing import Dict, Any, Optional
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

class RequestLogger:
    """Handles logging of requests to Supabase"""
    
    def __init__(self):
        self.log_level = logging.INFO
    
    async def log_request(
        self, 
        request_id: str, 
        user_id: str, 
        predictions: Dict[str, Any],
        supabase_client: Any
    ) -> bool:
        """
        Log request details to Supabase
        """
        try:
            # Prepare log entry
            log_entry = {
                "request_id": request_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "predictions": predictions,
                "log_type": "prediction_completed"
            }
            
            # Log to console
            logger.info(f"Request {request_id} processed: {predictions.get('latency_ms')}ms, "
                       f"{predictions.get('total_tokens')} tokens")
            
            # You could also log to a separate logging table if needed
            # For now, the main requests table serves as the log
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log request {request_id}: {str(e)}")
            return False
    
    async def log_error(
        self,
        request_id: str,
        error: Exception,
        context: Dict[str, Any],
        supabase_client: Any
    ) -> bool:
        """
        Log error details
        """
        try:
            error_log = {
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context
            }
            
            logger.error(f"Request {request_id} failed: {str(error)}")
            
            # Update request with error
            supabase_client.table("requests").update({
                "status": "failed",
                "error_message": str(error),
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", request_id).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log error for request {request_id}: {str(e)}")
            return False
    
    async def log_execution_result(
        self,
        request_id: str,
        actual_metrics: Dict[str, Any],
        supabase_client: Any
    ) -> bool:
        """
        Log actual execution results for comparison with predictions
        """
        try:
            # This would be called after actual API execution
            comparison = {
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "actual_latency": actual_metrics.get("latency_ms"),
                "actual_tokens": actual_metrics.get("total_tokens"),
                "prediction_accuracy": {
                    "latency_diff_ms": actual_metrics.get("latency_ms", 0) - 
                                      actual_metrics.get("predicted_latency_ms", 0),
                    "token_diff": actual_metrics.get("total_tokens", 0) - 
                                 actual_metrics.get("predicted_tokens", 0)
                }
            }
            
            logger.info(f"Execution result for {request_id}: "
                       f"Latency diff: {comparison['prediction_accuracy']['latency_diff_ms']}ms")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log execution result for {request_id}: {str(e)}")
            return False