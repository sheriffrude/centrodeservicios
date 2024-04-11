import os
import qrcode

input_data = '2', 'CAMPEON', '5105', '6', '1100'

# Obtener la ruta absoluta del directorio 'static/images' dentro de tu proyecto Django
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
images_dir = os.path.join(static_dir, 'images')
filename = 'qrcercafe.png'
filepath = os.path.join(images_dir, filename)

# Crear el directorio si no existe
os.makedirs(images_dir, exist_ok=True)

# Crear el código QR
qr = qrcode.QRCode(version=1, box_size=10, border=5)
qr.add_data(input_data)
qr.make(fit=True)

# Crear la imagen del código QR
img = qr.make_image(fill='black', back_color='white')

# Guardar la imagen en la ruta especificada
img.save(filepath)

print(f"La imagen del código QR ha sido guardada en {filepath}")
