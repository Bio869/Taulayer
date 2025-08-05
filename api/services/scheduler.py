from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import logging

logger = logging.getLogger(__name__)

class Scheduler:
    """Handles scheduling of requests for optimal execution times"""
    
    def __init__(self):
        self.peak_hours_utc = list(range(14, 23))  # 2 PM - 10 PM UTC
        self.off_peak_hours_utc = list(range(0, 6)) + list(range(23, 24))  # 11 PM - 6 AM UTC
        self.scheduled_tasks = {}
    
    def get_optimal_execution_time(self, priority: str = "medium") -> datetime:
        """
        Calculate optimal execution time based on current load and priority
        """
        now = datetime.utcnow()
        current_hour = now.hour
        
        # High priority: execute immediately
        if priority == "high":
            return now
        
        # If already in off-peak hours, execute now
        if current_hour in self.off_peak_hours_utc:
            return now
        
        # Find next off-peak hour
        hours_until_off_peak = self._hours_until_off_peak(current_hour)
        
        # Medium priority: wait up to 3 hours for off-peak
        if priority == "medium" and hours_until_off_peak <= 3:
            return now + timedelta(hours=hours_until_off_peak)
        elif priority == "medium":
            return now  # Don't wait too long for medium priority
        
        # Low priority: always wait for off-peak
        if priority == "low":
            return now + timedelta(hours=hours_until_off_peak)
        
        return now
    
    def _hours_until_off_peak(self, current_hour: int) -> int:
        """Calculate hours until next off-peak period"""
        # Next off-peak is either late night (23:00) or early morning (00:00)
        if current_hour < 23:
            return 23 - current_hour
        else:
            return 0
    
    async def schedule_request(
        self,
        request_id: str,
        execution_time: datetime,
        callback: Any,
        supabase_client: Any
    ) -> bool:
        """
        Schedule a request for later execution
        """
        try:
            delay_seconds = (execution_time - datetime.utcnow()).total_seconds()
            
            if delay_seconds <= 0:
                # Execute immediately
                await callback(request_id)
                return True
            
            # Update request status to scheduled
            supabase_client.table("requests").update({
                "status": "scheduled",
                "scheduled_for": execution_time.isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", request_id).execute()
            
            # Schedule the task
            task = asyncio.create_task(self._delayed_execution(
                request_id, delay_seconds, callback, supabase_client
            ))
            self.scheduled_tasks[request_id] = task
            
            logger.info(f"Request {request_id} scheduled for {execution_time.isoformat()}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to schedule request {request_id}: {str(e)}")
            return False
    
    async def _delayed_execution(
        self,
        request_id: str,
        delay_seconds: float,
        callback: Any,
        supabase_client: Any
    ):
        """
        Execute a request after a delay
        """
        try:
            await asyncio.sleep(delay_seconds)
            
            # Update status to processing
            supabase_client.table("requests").update({
                "status": "processing",
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", request_id).execute()
            
            # Execute the callback
            await callback(request_id)
            
            # Remove from scheduled tasks
            self.scheduled_tasks.pop(request_id, None)
            
        except asyncio.CancelledError:
            logger.info(f"Scheduled task for request {request_id} was cancelled")
            raise
        except Exception as e:
            logger.error(f"Error executing scheduled request {request_id}: {str(e)}")
            # Update status to failed
            supabase_client.table("requests").update({
                "status": "failed",
                "error_message": str(e),
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", request_id).execute()
    
    def cancel_scheduled_request(self, request_id: str) -> bool:
        """
        Cancel a scheduled request
        """
        task = self.scheduled_tasks.get(request_id)
        if task and not task.done():
            task.cancel()
            self.scheduled_tasks.pop(request_id, None)
            logger.info(f"Cancelled scheduled request {request_id}")
            return True
        return False
    
    def get_schedule_status(self) -> Dict[str, Any]:
        """
        Get current scheduling status
        """
        return {
            "scheduled_count": len(self.scheduled_tasks),
            "scheduled_requests": list(self.scheduled_tasks.keys()),
            "current_hour_utc": datetime.utcnow().hour,
            "is_peak_time": datetime.utcnow().hour in self.peak_hours_utc,
            "next_off_peak_hour": self._hours_until_off_peak(datetime.utcnow().hour)
        }