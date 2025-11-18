"""
Test directo del detector de esteganografía
"""
import io
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
    
    channel_results = []
    for c in range(min(channels, 3)):
        channel_data = pixels[:, :, c]
        lsb_bits = channel_data & 1
        
        lsb_bytes = np.packbits(lsb_bits.flatten())
        entropy = calculate_entropy(lsb_bytes.tobytes())
        ones_ratio = float(np.sum(lsb_bits)) / float(lsb_bits.size)
        is_suspicious = entropy > 7.8 and abs(ones_ratio - 0.5) > 0.1
        
        channel_results.append({
            'channel': c,
            'lsb_entropy': entropy,
            'ones_ratio': ones_ratio,
            'suspicious': is_suspicious
        })
    
    suspicious_count = sum(1 for r in channel_results if r['suspicious'])
    return {'channels': channel_results, 'suspicious_count': suspicious_count, 'is_suspicious': suspicious_count >= 2}

# Cargar y analizar
with open('espe_test.png', 'rb') as f:
    file_bytes = f.read()

image = Image.open(io.BytesIO(file_bytes))
file_entropy = calculate_entropy(file_bytes)

tail_start = int(len(file_bytes) * 0.7)
tail_data = file_bytes[tail_start:]
tail_entropy = calculate_entropy(tail_data)

expected_size = image.width * image.height * 3
actual_size = len(file_bytes)
size_ratio = actual_size / expected_size

lsb_result = analyze_lsb(image)
lsb_suspicious = lsb_result['is_suspicious']

# DECISIÓN con nueva lógica
is_suspicious = False
threat_level = "low"
reason = "Imagen normal"

if file_entropy > 7.9 and tail_entropy > 7.9:
    is_suspicious = True
    threat_level = 'medium'
    reason = f"Alta entropía general ({file_entropy:.2f}) y en cola ({tail_entropy:.2f}) - posible esteganografía avanzada"

print("=" * 70)
print("RESULTADO DEL ANÁLISIS - Sistema de Chat Mejorado")
print("=" * 70)
print(f"\n📁 Archivo: espe_test.png")
print(f"📊 Tipo: image/png")
print(f"\n🔍 ANÁLISIS:")
print(f"  • Entropía general: {file_entropy:.4f}")
print(f"  • Entropía cola: {tail_entropy:.4f}")
print(f"  • Ratio de tamaño: {size_ratio:.4f}")

print(f"\n📋 Análisis LSB:")
for channel in lsb_result['channels']:
    status = "⚠️ Sospechoso" if channel['suspicious'] else "✅ Normal"
    print(f"  • Canal {channel['channel']}: entropía={channel['lsb_entropy']:.4f}, ratio_1s={channel['ones_ratio']:.4f} - {status}")

print(f"\n⚖️ VEREDICTO:")
print(f"  • ¿Sospechoso?: {'❌ SÍ' if is_suspicious else '✅ NO'}")
print(f"  • Nivel de amenaza: {threat_level.upper()}")
print(f"  • Razón: {reason}")
print("\n" + "=" * 70)
