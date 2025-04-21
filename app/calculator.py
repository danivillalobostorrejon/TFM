# calculator.py
from typing import Dict, Any
from database import Database

class CostCalculator:
    def __init__(self, db: Database):
        self.db = db
        
    def calculate_worker_cost(self, worker_id: str, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Calculate the cost for a specific worker within a date range."""
        return self.db.get_worker_cost(worker_id, start_date, end_date)
    
    def calculate_all_workers_cost(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Calculate costs for all workers within a date range."""
        workers = self.db.get_all_workers()
        results = []
        
        for worker in workers:
            cost_data = self.calculate_worker_cost(worker['worker_id'], start_date, end_date)
            if cost_data:
                results.append(cost_data)
                
        return {
            'workers': results,
            'total_cost': sum(worker['total_cost'] for worker in results),
            'total_hours': sum(worker['total_hours'] for worker in results)
        }
