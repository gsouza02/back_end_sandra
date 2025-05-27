from PIL import Image
import io



def compress_image(image_data, quality=85, max_size=(800, 800)):
    # Abre a imagem a partir dos bytes
    img = Image.open(io.BytesIO(image_data))
    
    if img.mode == 'P':
        img = img.convert('RGB')
    
    # Redimensiona a imagem
    img.thumbnail(max_size)
    
    # Salva a imagem comprimida em um objeto BytesIO
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG', quality=quality, optimize=True)
    
    # Retorna os bytes da imagem comprimida
    return img_byte_arr.getvalue()