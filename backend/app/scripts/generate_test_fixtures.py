# scripts/generate_test_fixtures.py
import zipfile
from pathlib import Path

# XML FEL de muestra (simplificado pero válido)
SAMPLE_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<dte:DTE xmlns:dte="http://www.sat.gob.gt/dte/fel/0.2.0" Version="0.1">
  <dte:DatosEmision ID="DatosEmision">
    <dte:Emisor>
      <dte:NITEmisor>1234567</dte:NITEmisor>
      <dte:NombreEmisor>Empresa Test S.A.</dte:NombreEmisor>
    </dte:Emisor>
    <dte:Receptor>
      <dte:NITReceptor>7654321</dte:NITReceptor>
      <dte:NombreReceptor>Cliente Test</dte:NombreReceptor>
    </dte:Receptor>
    <dte:Totales>
      <dte:Total>1000.00</dte:Total>
      <dte:TotalImpuestos>
        <dte:Impuesto>
          <dte:NombreIVA>IVA</dte:NombreIVA>
          <dte:MontoIVA>120.00</dte:MontoIVA>
        </dte:Impuesto>
      </dte:TotalImpuestos>
    </dte:Totales>
  </dte:DatosEmision>
</dte:DTE>"""

def create_test_zip():
    fixtures_dir = Path(__file__).parent.parent / "tests" / "fel" / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    
    zip_path = fixtures_dir / "sample_fel.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr("factura_001.xml", SAMPLE_XML)
        zipf.writestr("factura_002.xml", SAMPLE_XML)
    
    print(f"✅ ZIP creado: {zip_path}")

if __name__ == "__main__":
    create_test_zip()