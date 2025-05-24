Table workers {
  worker_id varchar
  year int
  worker_name varchar
  percepcion_integra decimal
  company_id varchar
  company_name varchar
  Note: "PRIMARY KEY (worker_id, year)"
}

Table contingencias_comunes {
  worker_id varchar
  year int
  base_contingencias_comunes decimal
  dias_cotizados int
  periodo varchar
  company_id varchar
  company_name varchar
}

Table convenio {
  year int [pk]
  horas_convenio_anuales decimal
}

Table cargas_sociales {
  tipo varchar [pk]
  porcentaje decimal
}


Ref: contingencias_comunes.worker_id > workers.worker_id
Ref: contingencias_comunes.year > workers.year
Ref: convenio.year > workers.year
