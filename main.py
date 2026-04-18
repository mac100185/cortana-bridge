from flask import Flask, request, render_template_string, send_from_directory, jsonify
import os

app = Flask(__name__)

# Configuración de rutas
UPLOAD_FOLDER = 'incoming'
OUTPUT_FOLDER = 'outgoing'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

HTML = """
<!DOCTYPE html>
<html style="background: #0a0a23; color: #00d4ff; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
<head>
    <title>Cortana Bridge v3.0</title>
    <style>
        body { text-align: center; padding: 50px; margin: 0; }
        .container { display: flex; justify-content: center; gap: 30px; flex-wrap: wrap; }
        .card { 
            background: rgba(0, 75, 99, 0.3); 
            border: 2px solid #00d4ff; 
            border-radius: 15px; 
            padding: 30px; 
            width: 380px; 
            box-shadow: 0 0 20px rgba(0, 212, 255, 0.2);
            position: relative;
        }
        h1 { text-shadow: 0 0 10px #00d4ff; margin-bottom: 40px; }
        h3 { border-bottom: 1px solid #00d4ff; padding-bottom: 10px; margin-bottom: 20px; }
        input[type="file"] { margin: 20px 0; color: white; display: block; width: 100%; }
        input[type="submit"] { 
            background: #00d4ff; color: #0a0a23; 
            border: none; padding: 12px 25px; 
            border-radius: 5px; cursor: pointer; 
            font-weight: bold; transition: 0.3s; 
            width: 100%;
        }
        input[type="submit"]:hover { background: #fff; box-shadow: 0 0 15px #fff; }
        .file-link { 
            display: block; 
            color: #fff; 
            text-decoration: none; 
            background: rgba(0, 212, 255, 0.2); 
            margin: 10px 0; 
            padding: 10px; 
            border-radius: 5px; 
            border: 1px solid #00d4ff;
            transition: 0.2s;
            text-align: left;
            font-size: 0.9em;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .file-link:hover { background: rgba(0, 212, 255, 0.5); }
        
        #notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #00d4ff;
            color: #0a0a23;
            padding: 15px 25px;
            border-radius: 10px;
            font-weight: bold;
            box-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
            display: none;
            z-index: 1000;
            animation: slideIn 0.5s ease-out;
        }
        @keyframes slideIn {
            from { transform: translateX(100%); }
            to { transform: translateX(0); }
        }
        .recent-list {
            text-align: left;
            font-size: 0.85em;
            color: #aaa;
            max-height: 200px;
            overflow-y: auto;
        }
        .recent-item {
            padding: 5px 0;
            border-bottom: 1px solid rgba(0, 212, 255, 0.2);
        }
    </style>
</head>
<body>
    <div id="notification"></div>
    <h1>💙 Cortana Bridge v3.0</h1>
    <div class="container">
        <div class="card">
            <h3>📤 Enviar a Cortana</h3>
            <form id="uploadForm">
                <input type="file" name="files" id="fileInput" multiple>
                <input type="submit" value="Sincronizar Archivos">
            </form>
            <div style="margin-top: 20px; text-align: left;">
                <h4 style="color: #00d4ff; font-size: 0.9em;">Recientes:</h4>
                <div class="recent-list" id="recentFiles"></div>
            </div>
        </div>
        <div class="card">
            <h3>📥 Descargar de Cortana</h3>
            <div id="download-list">
                {% for file in files %}
                    <a class="file-link" href="/download/{{ file }}">{{ file }}</a>
                {% endfor %}
                {% if not files %}
                    <p style="color: #aaa;">No hay archivos pendientes.</p>
                {% endif %}
            </div>
        </div>
    </div>

    <script>
        async function showNotification(text) {
            const note = document.getElementById('notification');
            note.innerText = text;
            note.style.display = 'block';
            setTimeout(() => { note.style.display = 'none'; }, 4000);
        }

        async function loadRecents() {
            const res = await fetch('/list-incoming');
            const files = await res.json();
            const container = document.getElementById('recentFiles');
            container.innerHTML = files.map(f => `<div class="recent-item">📄 ${f}</div>`).join('') || 'Ninguno';
        }

        document.getElementById('uploadForm').onsubmit = async (e) => {
            e.preventDefault();
            const input = document.getElementById('fileInput');
            if (input.files.length === 0) return;

            const formData = new FormData();
            for (let file of input.files) {
                formData.append('files', file);
            }

            try {
                const res = await fetch('/upload', { method: 'POST', body: formData });
                const text = await res.text();
                showNotification(text);
                input.value = '';
                loadRecents();
            } catch (err) {
                showNotification('Error al subir archivos');
            }
        };

        loadRecents();
        setInterval(loadRecents, 5000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    files = os.listdir(OUTPUT_FOLDER)
    return render_template_string(HTML, files=files)

@app.route('/list-incoming')
def list_incoming():
    files = os.listdir(UPLOAD_FOLDER)
    return jsonify(files[-5:][::-1])

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return 'Error: No se encontraron archivos.', 400
    
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return 'Error: No seleccionaste ningún archivo.', 400
    
    uploaded_count = 0
    for file in files:
        file.save(os.path.join(UPLOAD_FOLDER, file.filename))
        uploaded_count += 1
        
    return f'Éxito: {uploaded_count} archivo(s) sincronizado(s) con Cortana. 💙', 200

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
