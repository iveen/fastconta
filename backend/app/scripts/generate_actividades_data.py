"""
Script para generar el archivo de datos de Actividades Económicas 
a partir del Excel TR2026.xlsx.
Ejecutar: python app/scripts/generate_actividades_data.py
"""
import os

import pandas as pd


def generate_data_file():
    excel_path = "TR2026.xlsx" 
    output_path = "app/scripts/data/actividades_economicas.py"
    
    if not os.path.exists(excel_path):
        print(f"❌ No se encontró el archivo {excel_path}. Asegúrate de estar en el directorio correcto.")
        return
        
    print(f"📖 Leyendo {excel_path}...")
    
    # Leer la columna como string para preservar ceros a la izquierda y decimales
    df = pd.read_excel(excel_path, dtype={'Código Actividad': str})
    
    # Limpiar espacios en blanco
    df['Código Actividad'] = df['Código Actividad'].str.strip()
    
    # Obtener combinaciones únicas y ordenarlas
    unique_activities = df[['Código Actividad', 'Nombre Actividad', 'Nombre Sección']].drop_duplicates()
    unique_activities = unique_activities.sort_values(by='Código Actividad').reset_index(drop=True)
    
    # Generar el contenido del archivo Python
    lines = [
        '"""',
        'Catálogo de Actividades Económicas de la SAT',
        'Generado automáticamente desde TR2026.xlsx',
        '"""',
        '',
        'ACTIVIDADES_ECONOMICAS_SAT = ['
    ]
    
    for _, row in unique_activities.iterrows():
        codigo = str(row['Código Actividad']).strip()
        nombre = str(row['Nombre Actividad']).strip().replace('"', '\\"')
        seccion = str(row['Nombre Sección']).strip().replace('"', '\\"')
        
        lines.append('    {')
        lines.append(f'        "codigo_sat": "{codigo}",')
        lines.append(f'        "nombre_actividad": "{nombre}",')
        lines.append(f'        "seccion": "{seccion}"')
        lines.append('    },')
        
    lines.append(']')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
        
    print(f"✅ Archivo generado exitosamente en: {output_path}")
    print(f"📊 Total de actividades económicas únicas procesadas: {len(unique_activities)}")

if __name__ == "__main__":
    generate_data_file()