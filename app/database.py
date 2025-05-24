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
    
    def clean_database(self):
        """Clean the database by dropping all tables."""
        conn = self.connect()
        cur = conn.cursor()
        
        # Drop all tables
        cur.execute("DROP TABLE IF EXISTS workers CASCADE")
        cur.execute("DROP TABLE IF EXISTS contingencias_comunes CASCADE")
        cur.execute("DROP TABLE IF EXISTS convenio CASCADE")
        cur.execute("DROP TABLE IF EXISTS cargas_sociales CASCADE")
        
        conn.commit()
        cur.close()
        conn.close()
        print("Database cleaned successfully.")

    def create_tables(self):
        """Create necessary tables if they don't exist."""
        conn = self.connect()
        cur = conn.cursor()

        
        # Create workers table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            worker_id VARCHAR(100),
            year INT NOT NULL,
            worker_name VARCHAR(255) NOT NULL,
            percepcion_integra DECIMAL(10, 2) NOT NULL,
            company_id VARCHAR(100) NOT NULL,
            company_name VARCHAR(255) NOT NULL,
            UNIQUE(worker_id, company_id, year)
        )
        """)

        # Create contingencias comunes table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS contingencias_comunes (
                worker_id VARCHAR(100),
                year INT NOT NULL,
                base_contingencias_comunes DECIMAL(24, 4) NOT NULL,
                dias_cotizados INT NOT NULL,
                periodo VARCHAR(10) NOT NULL,
                company_id VARCHAR(100) NOT NULL,
                company_name VARCHAR(255) NOT NULL,
                UNIQUE(worker_id, year, periodo, base_contingencias_comunes, dias_cotizados, company_id, company_name)
            )
        """)

        # Create convenio table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS convenio (
            year INT NOT NULL,
            horas_convenio_anuales DECIMAL(10, 2) NOT NULL,
            UNIQUE(year)
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
        
        conn.commit()
        cur.close()
        conn.close()
    
    def insert_worker(self, worker_data: Dict[str, Any]):
        """Insert or update worker information."""
        conn = self.connect()
        cur = conn.cursor()
        
        cur.execute("""
        INSERT INTO workers (worker_id, year, worker_name, percepcion_integra, company_id, company_name)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (worker_id, company_id, year) DO NOTHING
        """, (
                worker_data['worker_id'], 
                worker_data['year'], 
                worker_data['worker_name'], 
                worker_data['percepcion_integra'],
                worker_data['company_id'],
                worker_data['company_name']
            )
        )
        
        conn.commit()
        cur.close()
        conn.close()

    def insert_contingencias_comunes(self, worker_data: Dict[str, Any]):
        """Insert or update worker information."""
        conn = self.connect()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO contingencias_comunes (
                worker_id, year, base_contingencias_comunes, dias_cotizados,
                periodo, company_id, company_name
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (
                worker_id, year, periodo, base_contingencias_comunes,
                dias_cotizados, company_id, company_name
            ) DO NOTHING
        """, (
            worker_data['worker_id'],
            worker_data['year'],
            worker_data['base_contingencias_comunes'],
            worker_data['dias_cotizados'],
            worker_data['periodo'],
            worker_data['company_id'],
            worker_data['company_name']
        ))
        
        conn.commit()
        cur.close()
        conn.close()

    def insert_convenio(self, convenio_data: Dict[str, Any]):
        """Insert or update convenio information."""
        conn = self.connect()
        cur = conn.cursor()
        
        cur.execute("""
        INSERT INTO convenio (year, horas_convenio_anuales)
        VALUES (%s, %s)
        ON CONFLICT (year) DO NOTHING
        """, (convenio_data['year'], convenio_data['horas_convenio_anuales'],))
        
        conn.commit()
        cur.close()
        conn.close()

    def get_workers_data(self):

        conn = self.connect()
        cur = conn.cursor(cursor_factory=RealDictCursor)
# (Salario bruto + (costes seguridad social RNT * 12 meses) * 31,4%) / horas convenio

        cur.execute("""
                    
        with porcentaje_cte as (
            select sum(porcentaje) as porcentaje from cargas_sociales
        ),
        contingencias_comunes_cte as (
            select worker_id, year, sum(base_contingencias_comunes) as base_contingencias_comunes
            from contingencias_comunes
            group by worker_id, year
        )
                    
        SELECT 
            workers.worker_id, 
            workers.year, 
            workers.worker_name, 
            sum(percepcion_integra) as percepcion_integra,
            max(base_contingencias_comunes) as base_contingencias_comunes,
            max(porcentaje)/100 as porcentaje,
            max(horas_convenio_anuales) as horas_convenio_anuales,
            (sum(percepcion_integra) + ((max(base_contingencias_comunes)/12 )*(max(porcentaje)/100))) / max(horas_convenio_anuales)  as coste_hora
        FROM workers
        left join porcentaje_cte on true
        left join convenio on workers.year = convenio.year
        left join contingencias_comunes_cte 
            on workers.worker_id = contingencias_comunes_cte.worker_id
            and workers.year = contingencias_comunes_cte.year
        GROUP BY workers.worker_id, workers.year, workers.worker_name
        """)
        workers = cur.fetchall()
        cur.close()
        conn.close()

        return workers

    def get_all_workers(self):
        """Get list of all workers."""
        conn = self.connect()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT * FROM workers")
        workers = cur.fetchall()

        cur.execute("SELECT worker_id, periodo, sum(base_contingencias_comunes) as base_contingencias_comunes FROM contingencias_comunes group by worker_id, periodo")
        contingencias_comunes = cur.fetchall()
        
        workers_data = self.get_workers_data()

        cur.close()
        conn.close()
        
        return {
            "trabajadores": workers, 
            "contingencias_comunes": contingencias_comunes, 
            "coste_hora": workers_data, 
        }
