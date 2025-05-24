from flask import Flask, request, send_file, render_template
import pandas as pd

app = Flask(__name__, static_url_path='/static')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        archivo_sii = request.files['file']
        if not archivo_sii:
            return 'No se subió ningún archivo.'

        try:
            # Leer el archivo del SII
            df_sii = pd.read_csv(archivo_sii, encoding='latin1', sep=None, engine='python', dtype=str)
            df_sii.columns = df_sii.columns.str.strip()

            # Filtrar registros con Nro = 33
            df_filtrado = df_sii[df_sii['Nro'].astype(str) == '33']

            # ✅ RUT desde Tipo Compra
            rut_proveedores = df_filtrado['Tipo Compra'].dropna().reset_index(drop=True)

            # ✅ FOLIO desde Razon Social (confirmado que ahí están los números como 30342, etc.)
            folios = df_filtrado['Razon Social'].astype(str).dropna().reset_index(drop=True)

            # Leer base fija
            df_base = pd.read_csv('archivo_base_fijo.csv', encoding='latin1', sep=';', dtype=str)

            # Crear archivo nuevo
            min_filas = min(len(rut_proveedores), len(folios))
            df_modificada = df_base.iloc[:min_filas].copy()
            df_modificada['Rut-DV'] = rut_proveedores[:min_filas]
            df_modificada['Folio_Doc'] = folios[:min_filas]

            # Guardar CSV
            output_path = 'archivo_modificado.csv'
            df_modificada.to_csv(output_path, index=False, sep=';', encoding='latin1')

            return send_file(output_path, as_attachment=True)

        except Exception as e:
            return f'Error al procesar el archivo: {e}'

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)















