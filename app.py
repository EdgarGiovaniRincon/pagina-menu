from flask import Flask, jsonify, Response, send_from_directory, render_template  # <-- render_template agregado
from flask_cors import CORS
import pyodbc
import os  # <-- Importación adicional para manejo de archivos

app = Flask(__name__)
CORS(app)

# Configuración de conexión
conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=DESKTOP-VEEAS9N;"
    "DATABASE=Menu;"
    "UID=sa;"
    "PWD=123456789"
)

def determinar_categoria(nombre_platillo):
    """Clasifica el platillo según palabras clave en su nombre"""
    try:
        nombre = nombre_platillo.lower()
        if "entrada" in nombre:
            return "Entrada"
        elif "plato" in nombre or "fuerte" in nombre or "principal" in nombre:
            return "Platos Fuertes"
        elif "postre" in nombre or "dulce" in nombre:
            return "Postre"
        elif "bebida" in nombre or "jugo" in nombre or "agua" in nombre or "refresco" in nombre:
            return "Bebida"
        return "Otros"
    except AttributeError:
        return "Otros"

@app.route('/')
def home():  # <-- Ruta agregada
    return render_template('menu.html')

@app.route('/api/menu')
def get_menu():
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT IdMenu, Platillo, Descripcion, Imagen, Imagen_GXI, Status 
        FROM Menu
        WHERE Status = 1
        """)
        
        menu_data = {
            "Entrada": [],
            "Platos Fuertes": [],
            "Postre": [],
            "Bebida": [],
            "Otros": []
        }
        
        for row in cursor:
            try:
                # Detectar si la imagen proviene del sistema interno de GeneXus
                if row.Imagen_GXI and row.Imagen_GXI.startswith("gxdbfile:"):
                    imagen_filename = row.Imagen_GXI.replace("gxdbfile:", "")
                    imagen_url = f"/gx_images/{imagen_filename}"
                else:
                    imagen_url = f"/multimedia/{row.Imagen_GXI}" if row.Imagen_GXI else None

                platillo_data = {
                    "id": row.IdMenu,
                    "nombre": row.Platillo,
                    "descripcion": row.Descripcion,
                    "imagen_url": imagen_url,
                    "imagen_gxi": row.Imagen_GXI,
                    "status": row.Status
                }

                categoria = determinar_categoria(row.Platillo)
                if categoria in menu_data:
                    menu_data[categoria].append(platillo_data)
                else:
                    menu_data["Otros"].append(platillo_data)
            
            except Exception as e:
                print(f"Error procesando fila: {e}")
                continue
        
        conn.close()
        return jsonify(menu_data)
    
    except pyodbc.Error as e:
        print(f"Error de base de datos: {e}")
        return jsonify({"error": "Error al conectar con la base de datos"}), 500
    except Exception as e:
        print(f"Error inesperado: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route('/imagen/<int:id_menu>')
def get_imagen(id_menu):
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("SELECT Imagen FROM Menu WHERE IdMenu = ?", (id_menu,))
        row = cursor.fetchone()
        
        if row and row[0]:
            imagen_bytes = row[0]
            conn.close()
            return Response(imagen_bytes, mimetype='image/jpeg')
        else:
            conn.close()
            return send_from_directory('static', 'default.jpg')
            
    except pyodbc.Error as e:
        print(f"Error de base de datos: {e}")
        return send_from_directory('static', 'default.jpg')
    except Exception as e:
        print(f"Error inesperado: {e}")
        return send_from_directory('static', 'default.jpg')

@app.route('/gx_images/<filename>')
def get_gx_image(filename):
    try:
        gx_image_path = 'C:/GeneXus/WebApps/Comedor/wwwroot/gad/files/'
        return send_from_directory(gx_image_path, filename)
    except Exception as e:
        print(f"Error al cargar imagen GX: {e}")
        return send_from_directory('static', 'default.jpg')

# ====== NUEVAS RUTAS PARA IMÁGENES ======

@app.route('/imagenes')
def listar_imagenes():
    imagenes_dir = r'C:\Models\Comedor\CSharpModel\Web\PublicTempStorage\multimedia'
    try:
        archivos = os.listdir(imagenes_dir)
        imagenes = [f'/multimedia/{archivo}' for archivo in archivos if archivo.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp'))]
        return jsonify(imagenes)
    except Exception as e:
        print(f"Error al listar imágenes: {e}")
        return jsonify({"error": "No se pudieron listar las imágenes"}), 500

@app.route('/multimedia/<path:filename>')
def servir_imagen(filename):
    imagenes_dir = r'C:\Models\Comedor\CSharpModel\Web\PublicTempStorage\multimedia'
    try:
        return send_from_directory(imagenes_dir, filename)
    except Exception as e:
        print(f"Error al servir la imagen: {e}")
        return send_from_directory('static', 'default.jpg')

# =========================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Obtiene el puerto de Render
    app.run(debug=True, host='0.0.0.0', port=port)  # Asegura que se escuche en todas las IPs

