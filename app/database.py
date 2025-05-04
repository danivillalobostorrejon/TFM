# database.py
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from typing import Dict, Any, List

class Database:
    def __init__(self, connection_string=None):
        if connection_string is None:
            # Default to environment variables if not provided
            self.connection_string = f"host={os.getenv('DB_HOST')} dbname={os.getenv('DB_NAME')} user={os.getenv('DB_USER')} password={os.getenv('DB_PASSWORD')}"
        else:
            self.connection_string = connection_string
        
    def connect(self):
        """Establish a connection to the PostgreSQL database."""
        return psycopg2.connect(self.connection_string)
    
    def clear_all_data(self):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("TRUNCATE TABLE salary_data, work_hours, workers CASCADE;")
        conn.commit()
        cur.close()
        conn.close()

    
    def create_tables(self):
        """Create necessary tables if they don't exist."""
        conn = self.connect()
        cur = conn.cursor()
        
        # Create workers table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            worker_id VARCHAR(100) PRIMARY KEY,
            worker_name VARCHAR(255) NOT NULL,
            percepcion_integra DECIMAL(10, 2) NOT NULL
        )
        """)
        
        # Create work_hours table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS work_hours (
            id SERIAL PRIMARY KEY,
            worker_id VARCHAR(100) REFERENCES workers(worker_id),
            hours_worked DECIMAL(10, 2) NOT NULL,
            work_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        conn.commit()
        cur.close()
        conn.close()
    
    def insert_worker(self, worker_data: Dict[str, Any]):
        """Insert or update worker information."""
        conn = self.connect()
        cur = conn.cursor()
        
        cur.execute("""
        INSERT INTO workers (worker_id, worker_name, percepcion_integra)
        VALUES (%s, %s, %s)
        ON CONFLICT (worker_id) DO UPDATE 
        SET worker_name = EXCLUDED.worker_name, percepcion_integra = EXCLUDED.percepcion_integra
        """, (worker_data['worker_id'], worker_data['worker_name'], worker_data['percepcion_integra']))
        
        conn.commit()
        cur.close()
        conn.close()
        
    def insert_work_hours(self, worker_id: str, hours_worked: float, work_date: str):
        """Record work hours for a worker."""
        conn = self.connect()
        cur = conn.cursor()
        
        cur.execute("""
        INSERT INTO work_hours (worker_id, hours_worked, work_date)
        VALUES (%s, %s, %s)
        """, (worker_id, hours_worked, work_date))
        
        conn.commit()
        cur.close()
        conn.close()
        
    def get_worker_information(self, worker_id: str, start_date: str = None, end_date: str = None):
        """Calculate cost for a worker within a date range."""
        conn = self.connect()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
        SELECT w.worker_id, w.worker_name, w.percepcion_integra, 
               SUM(wh.hours_worked) as total_hours,
               SUM(w.percepcion_integra) as total_percepcion_integra
        FROM workers w
        JOIN work_hours wh ON w.worker_id = wh.worker_id
        WHERE w.worker_id = %s
        """
        
        params = [worker_id]
        
        if start_date:
            query += " AND wh.work_date >= %s"
            params.append(start_date)
            
        if end_date:
            query += " AND wh.work_date <= %s"
            params.append(end_date)
            
        query += " GROUP BY w.worker_id, w.worker_name, w.percepcion_integra"
        
        cur.execute(query, params)
        result = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return result
    
    def get_all_workers(self):
        """Get list of all workers."""
        conn = self.connect()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT * FROM workers")
        workers = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return workers
