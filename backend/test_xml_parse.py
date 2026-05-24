# test_xml_parse.py (en la raíz del proyecto)
import xml.etree.ElementTree as ET
import sys

def test_parse_xml(filepath):
    print(f"🔍 Probando: {filepath}")
    
    with open(filepath, 'rb') as f:
        content = f.read()
    
    print(f"📄 Size: {len(content)} bytes")
    print(f"🔍 First 300 bytes (hex): {content[:300].hex()}")
    print(f"🔍 First 300 bytes (text): {content[:300]!r}\n")
    
    # Intentar decodificar con diferentes encodings
    for encoding in ['utf-8', 'utf-8-sig', 'iso-8859-1', 'windows-1252']:
        try:
            xml_str = content.decode(encoding)
            print(f"✅ Decodificado con {encoding}")
            
            # Intentar parsear
            root = ET.fromstring(xml_str)
            print(f"✅ Parseado exitosamente. Root tag: {root.tag}")
            
            # Helper para buscar ignorando namespaces
            def find_any(parent, tag):
                # 🔹 CORRECCIÓN: concatenación en lugar de f-string con {*}
                elem = parent.find(f'.//{{*}}{tag}')  # wildcard namespace: {.//{*}Tag}
                if elem is None:
                    elem = parent.find(f'.//{tag}')  # sin namespace
                return elem
            
            # Buscar elementos comunes de FEL Guatemala
            for tag in ['NumeroAutorizacion', 'Numero', 'Serie', 'FechaEmision', 'Total']:
                elem = find_any(root, tag)
                if elem is not None:
                    print(f"   ├─ {tag}: {elem.text}")
            
            return True
            
        except UnicodeDecodeError:
            print(f"⚠️  No se pudo decodificar con {encoding}")
            continue
        except ET.ParseError as e:
            print(f"❌ Error de parseo con {encoding}: {e}")
            # Mostrar línea aproximada del error si es posible
            if hasattr(e, 'position'):
                line, col = e.position
                lines = xml_str.split('\n')
                if line <= len(lines):
                    print(f"   └─ Línea {line}: {lines[line-1][:100]}")
            return False
        except Exception as e:
            print(f"❌ Error inesperado: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print("❌ No se pudo procesar con ningún encoding")
    return False

if __name__ == "__main__":
    filepath = sys.argv[1] if len(sys.argv) > 1 else "5E151425-DEB8-4193-82ED-CF196D527BFF.xml"
    success = test_parse_xml(filepath)
    sys.exit(0 if success else 1)