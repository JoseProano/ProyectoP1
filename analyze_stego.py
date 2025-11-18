"""
Script para analizar esteganografía en una imagen
Usa las mismas técnicas del sistema de chat
"""
import sys
import math
from collections import Counter
from PIL import Image
import numpy as np

def calculate_entropy(data):
    """Calcula la entropía de Shannon"""
    if len(data) == 0:
        return 0.0
    
    counter = Counter(data)
    length = len(data)
    
    entropy = 0.0
    for count in counter.values():
        probability = count / length
        if probability > 0:
            entropy -= probability * math.log2(probability)
    
    return entropy

def analyze_lsb(image):
    """Analiza bits menos significativos"""
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    pixels = np.array(image)
    height, width, channels = pixels.shape
    
    print("\n🔍 Análisis LSB (Least Significant Bit):")
    print("-" * 60)
    
    channel_results = []
    for c in range(min(channels, 3)):
        channel_name = ['Red', 'Green', 'Blue'][c]
        channel_data = pixels[:, :, c]
        lsb_bits = channel_data & 1
        
        # Calcular entropía de LSBs
        lsb_bytes = np.packbits(lsb_bits.flatten())
        entropy = calculate_entropy(lsb_bytes.tobytes())
        
        # Ratio de 1s
        ones_ratio = float(np.sum(lsb_bits)) / float(lsb_bits.size)
        
        # Evaluar
        is_suspicious = entropy > 7.8 and abs(ones_ratio - 0.5) > 0.1
        
        print(f"  Canal {channel_name}:")
        print(f"    - Entropía LSB: {entropy:.4f}")
        print(f"    - Ratio de 1s: {ones_ratio:.4f} (normal: ~0.5)")
        print(f"    - Estado: {'⚠️ SOSPECHOSO' if is_suspicious else '✅ Normal'}")
        
        channel_results.append(is_suspicious)
    
    suspicious_count = sum(channel_results)
    print(f"\n  Canales sospechosos: {suspicious_count}/3")
    
    return suspicious_count >= 2

def detect_embedded_files(file_bytes):
    """Detecta archivos embebidos (copy /b)"""
    signatures = [
        (b'\xFF\xD8\xFF\xE0', 'JPEG JFIF'),
        (b'\xFF\xD8\xFF\xE1', 'JPEG EXIF'),
        (b'\x89PNG\r\n\x1a\n', 'PNG'),
        (b'GIF89a', 'GIF89'),
        (b'GIF87a', 'GIF87'),
        (b'%PDF-', 'PDF'),
        (b'PK\x03\x04', 'ZIP'),
    ]
    
    embedded = []
    search_start = int(len(file_bytes) * 0.3)
    
    if len(file_bytes) < 10240:
        return embedded
    
    for signature, file_type in signatures:
        pos = file_bytes.find(signature, search_start)
        if pos != -1 and pos + 1024 < len(file_bytes):
            embedded.append({
                'type': file_type,
                'position': pos,
                'offset_percentage': pos / len(file_bytes) * 100
            })
    
    return embedded

def analyze_image(image_path):
    """Análisis completo de la imagen"""
    print("=" * 60)
    print("🔐 ANÁLISIS DE ESTEGANOGRAFÍA")
    print("=" * 60)
    print(f"\nArchivo: {image_path}\n")
    
    # Cargar imagen
    with open(image_path, 'rb') as f:
        file_bytes = f.read()
    
    image = Image.open(image_path)
    
    # 1. Información básica
    print("📋 Información Básica:")
    print("-" * 60)
    print(f"  Formato: {image.format}")
    print(f"  Tamaño: {image.width}x{image.height} píxeles")
    print(f"  Modo: {image.mode}")
    print(f"  Tamaño archivo: {len(file_bytes):,} bytes ({len(file_bytes)/1024:.2f} KB)")
    
    # 2. Entropía general
    file_entropy = calculate_entropy(file_bytes)
    print(f"\n📊 Análisis de Entropía:")
    print("-" * 60)
    print(f"  Entropía general: {file_entropy:.4f}")
    print(f"  Referencia:")
    print(f"    - Normal: 6.0 - 7.5")
    print(f"    - Sospechoso: 7.5 - 7.9")
    print(f"    - Muy sospechoso: > 7.9")
    
    # 3. Entropía de la cola (detecta archivos concatenados)
    tail_start = int(len(file_bytes) * 0.7)
    tail_data = file_bytes[tail_start:]
    tail_entropy = calculate_entropy(tail_data) if len(tail_data) > 100 else file_entropy
    print(f"  Entropía cola (últimos 30%): {tail_entropy:.4f}")
    
    # 4. Análisis de tamaño
    expected_size = image.width * image.height * 3
    actual_size = len(file_bytes)
    size_ratio = actual_size / expected_size
    
    print(f"\n📏 Análisis de Tamaño:")
    print("-" * 60)
    print(f"  Tamaño esperado (sin compresión): {expected_size:,} bytes")
    print(f"  Tamaño real: {actual_size:,} bytes")
    print(f"  Ratio de compresión: {size_ratio:.4f}")
    print(f"  Referencia JPEG normal: 0.05 - 0.2")
    print(f"  Estado: {'⚠️ Sospechoso (>0.3)' if size_ratio > 0.3 else '✅ Normal'}")
    
    # 5. Buscar archivos embebidos
    print(f"\n🔎 Búsqueda de Archivos Embebidos:")
    print("-" * 60)
    embedded = detect_embedded_files(file_bytes)
    if embedded:
        print("  ⚠️ ARCHIVOS EMBEBIDOS DETECTADOS:")
        for e in embedded:
            print(f"    - {e['type']} en posición {e['position']} ({e['offset_percentage']:.1f}%)")
    else:
        print("  ✅ No se detectaron archivos embebidos")
    
    # 6. Análisis LSB
    lsb_suspicious = analyze_lsb(image)
    
    # 7. VEREDICTO FINAL
    print("\n" + "=" * 60)
    print("⚖️  VEREDICTO FINAL")
    print("=" * 60)
    
    is_suspicious = False
    threat_level = "low"
    reasons = []
    
    # Evaluar criterios
    if embedded:
        is_suspicious = True
        threat_level = "critical"
        reasons.append(f"Archivos embebidos detectados: {', '.join([e['type'] for e in embedded])}")
    
    if lsb_suspicious and tail_entropy > 7.9:
        is_suspicious = True
        threat_level = "high" if threat_level != "critical" else threat_level
        reasons.append("Patrón LSB sospechoso con alta entropía en cola")
    
    if size_ratio > 0.3 and file_entropy > 7.9:
        is_suspicious = True
        threat_level = "medium" if threat_level == "low" else threat_level
        reasons.append("Tamaño inusual con alta entropía general")
    
    if is_suspicious:
        print(f"\n❌ IMAGEN SOSPECHOSA")
        print(f"   Nivel de amenaza: {threat_level.upper()}")
        print(f"\n   Razones:")
        for reason in reasons:
            print(f"   • {reason}")
    else:
        print(f"\n✅ IMAGEN NORMAL")
        print(f"   No se detectaron indicios de esteganografía")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python analyze_stego.py <ruta_imagen>")
        sys.exit(1)
    
    analyze_image(sys.argv[1])
