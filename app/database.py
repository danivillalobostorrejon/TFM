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

        # Create contingencias comunes table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS contingencias_comunes (
            worker_id VARCHAR(100),
            base_contingencias_comunes DECIMAL(24, 4) NOT NULL,
            dias_cotizados INT NOT NULL,
            periodo VARCHAR(10) NOT NULL,
        UNIQUE(worker_id, periodo, base_contingencias_comunes, dias_cotizados)
        )
        """)

        # Create convenio table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS convenio (
            horas_convenio_anuales DECIMAL(10, 2) NOT NULL UNIQUE
        )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS cargas_sociales (
                id SERIAL PRIMARY KEY,
                concepto VARCHAR(100) UNIQUE NOT NULL,
                porcentaje DECIMAL(5, 2) NOT NULL
            )
        """)

            # Insertar valores fijos si no existen
        cur.execute("""
            INSERT INTO cargas_sociales (concepto, porcentaje) VALUES 
            ('Contingencias comunes', 23.60),
            ('Formación profesional + Desempleo', 5.50),
            ('FOGASA', 0.80),
            ('ÍT', 1.50)
            ON CONFLICT (concepto) DO NOTHING
        """)

        
        # Create 10t table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS doc_10t (
            worker_id VARCHAR(100) UNIQUE,
            worker_name VARCHAR(255) NOT NULL,
            rendimiento_integrar DECIMAL(10, 2) NOT NULL
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

    def insert_contingencias_comunes(self, worker_data: Dict[str, Any]):
        """Insert or update worker information."""
        conn = self.connect()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO contingencias_comunes (worker_id, base_contingencias_comunes, dias_cotizados, periodo)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (worker_id, periodo, base_contingencias_comunes, dias_cotizados) DO NOTHING 
            """, (
                worker_data['worker_id'],
                worker_data['base_contingencias_comunes'],
                worker_data['dias_cotizados'],
                worker_data['periodo']
        ))
        
        conn.commit()
        cur.close()
        conn.close()

    def insert_convenio(self, convenio_data: Dict[str, Any]):
        """Insert or update convenio information."""
        conn = self.connect()
        cur = conn.cursor()
        
        cur.execute("""
        INSERT INTO convenio (horas_convenio_anuales)
        VALUES (%s)
        ON CONFLICT (horas_convenio_anuales) DO NOTHING
        """, (convenio_data['horas_convenio_anuales'],))
        
        conn.commit()
        cur.close()
        conn.close()
        
    def insert_10t(self, worker_data: Dict[str, Any]):
        """Insert or update 10t information."""
        conn = self.connect()
        cur = conn.cursor()
        
        cur.execute("""
        INSERT INTO doc_10t (worker_id, worker_name, rendimiento_integrar)
        VALUES (%s, %s, %s)
        ON CONFLICT (worker_id) DO UPDATE 
        SET worker_name = EXCLUDED.worker_name, rendimiento_integrar = EXCLUDED.rendimiento_integrar
        """, (worker_data['worker_id'], worker_data['worker_name'], worker_data['rendimiento_integrar']))
        
        conn.commit()
        cur.close()
        conn.close()
    
    def get_all_workers(self):
        """Get list of all workers."""
        conn = self.connect()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT * FROM workers left join convenio on true")
        workers = cur.fetchall()

        cur.execute("SELECT * FROM contingencias_comunes")
        contingencias_comunes = cur.fetchall()
        
        # cur.execute("SELECT * FROM convenio")
        # convenios = cur.fetchall()

        cur.execute("SELECT * FROM cargas_sociales")
        cargas_sociales = cur.fetchall()

        cur.execute("SELECT * FROM doc_10t")
        doc_10t = cur.fetchall()

        cur.close()
        conn.close()
        
        return {
            "trabajadores": workers, 
            "contingencias_comunes": contingencias_comunes, 
            # "convenios": convenios, 
            "cargas_sociales": cargas_sociales,
            "doc_10t": doc_10t
        }
