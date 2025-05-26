from flask import Flask, request, send_file, render_template, redirect, session, url_for
import pandas as pd
from supabase import create_client, Client
import os
import tempfile

# Configuración de Supabase
SUPABASE_URL = 'https://iyskzhgjvchokwfxgqyc.supabase.co'
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml5c2t6aGdqdmNob2t3ZnhncXljIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgyNjk5MjcsImV4cCI6MjA2Mzg0NTkyN30.r5KqQ4Ed1QUEZZ-zBOKNeApwtgyA4shhNHyu9zrqt5A"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__, static_url_path='/static')
app.secret_key = os.urandom(24)

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'usuario' not in session:
        return redirect('/login')

    if request.method == 'POST':
        archivo_sii = request.files['file']
        if not archivo_sii:
            return 'No se subió ningún archivo.'

        try:
            df_sii = pd.read_csv(archivo_sii, encoding='latin1', sep=None, engine='python', dtype=str)
            df_sii.columns = df_sii.columns.str.strip()
            df_filtrado = df_sii[df_sii['Nro'].astype(str) == '33']
            rut_proveedores = df_filtrado['Tipo Compra'].dropna().reset_index(drop=True)
            folios = df_filtrado['Razon Social'].astype(str).dropna().reset_index(drop=True)
            df_base = pd.read_csv('archivo_base_fijo.csv', encoding='latin1', sep=';', dtype=str)
            min_filas = min(len(rut_proveedores), len(folios))
            df_modificada = df_base.iloc[:min_filas].copy()
            df_modificada['Rut-DV'] = rut_proveedores[:min_filas]
            df_modificada['Folio_Doc'] = folios[:min_filas]
            output_path = 'archivo_modificado.csv'
            df_modificada.to_csv(output_path, index=False, sep=';', encoding='latin1')
            return send_file(output_path, as_attachment=True)
        except Exception as e:
            return f'Error al procesar el archivo: {e}'

    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']
        resultado = supabase.table('usuarios').select('*').eq('usuario', usuario).eq('password', password).execute()

        if resultado.data:
            session['usuario'] = resultado.data[0]['usuario']
            session['tipo'] = resultado.data[0].get('tipo_usuario', 'cliente')

            if session['tipo'] == 'admin':
                return redirect('/dashboard')
            else:
                return redirect('/')
        else:
            return render_template('login.html', error='Credenciales incorrectas')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session or session.get('tipo') != 'admin':
        return redirect(url_for('login'))
    return render_template('dashboard.html')


@app.route('/honorarios/retencion', methods=['POST'])
def generar_con_retencion():
    archivos = request.files.getlist('files')
    integrador_path = os.path.join(os.path.dirname(__file__), 'Integrador honorarios-2.xlsx')
    df_integrador = pd.read_excel(integrador_path)

    for archivo in archivos:
        df = pd.read_excel(archivo, skiprows=5)
        df.columns = df.columns.str.strip()
        df = df.dropna(subset=["Fecha", "Retenido"])
        df["Retenido"] = pd.to_numeric(df["Retenido"], errors="coerce").fillna(0)
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
        df = df.dropna(subset=["Fecha"])
        df["Periodo"] = df["Fecha"].dt.strftime("%Y%m")
        df_ret = df[df["Retenido"] > 0]
        df_integrador = pd.concat([df_integrador, df_ret], ignore_index=True)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    df_integrador.to_excel(temp_file.name, index=False)
    return send_file(temp_file.name, as_attachment=True, download_name="integrador_actualizado.xlsx")

@app.route('/honorarios/sin-retencion', methods=['POST'])
def depurar_sin_retencion():
    archivos = request.files.getlist('files')
    df_final = pd.DataFrame()

    for archivo in archivos:
        df = pd.read_excel(archivo, skiprows=5)
        df.columns = df.columns.str.strip()
        df = df.dropna(subset=["Fecha", "Retenido"])
        df["Retenido"] = pd.to_numeric(df["Retenido"], errors="coerce").fillna(0)
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
        df = df.dropna(subset=["Fecha"])
        df["Periodo"] = df["Fecha"].dt.strftime("%Y%m")
        df_sin_ret = df[df["Retenido"] == 0]
        df_final = pd.concat([df_final, df_sin_ret], ignore_index=True)

    df_final = df_final.sort_values(by="Fecha")

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    df_final.to_excel(temp_file.name, index=False)
    return send_file(temp_file.name, as_attachment=True, download_name="honorarios_sin_retencion.xlsx")
   
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/favicon.ico')
def favicon():
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)















