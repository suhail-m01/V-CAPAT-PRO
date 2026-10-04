"""Portable QR PNG pointing a judge's phone at the running dashboard."""
from io import BytesIO

def dashboard_qr_png(url):
    if not url.startswith(('https://','http://')):raise ValueError('Dashboard URL must be HTTP(S)')
    try:import qrcode
    except ImportError as exc:raise RuntimeError('Install the qrcode dependency from requirements.txt') from exc
    code=qrcode.QRCode(version=None,box_size=6,border=2,error_correction=qrcode.constants.ERROR_CORRECT_M)
    code.add_data(url);code.make(fit=True)
    image=code.make_image(fill_color='#06231e',back_color='#f4fffa').convert('RGB')
    stream=BytesIO();image.save(stream,format='PNG');return stream.getvalue()
