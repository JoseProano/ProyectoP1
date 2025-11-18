"""
Test del detector de esteganografía mejorado
"""
import sys
sys.path.insert(0, 'backend')

from app.utils.steganography_improved import improved_detector

# Cargar imagen de prueba
with open('espe_test.png', 'rb') as f:
    file_bytes = f.read()

# Analizar
result = improved_detector.analyze_file(file_bytes, 'espe_test.png', 'image/png')

print("=" * 70)
print("RESULTADO DEL ANÁLISIS - Sistema de Chat")
print("=" * 70)
print(f"\n📁 Archivo: {result['filename']}")
print(f"📊 Tipo: {result['file_type']}")
print(f"\n🔍 ANÁLISIS:")
print(f"  • Entropía general: {result['file_entropy']:.4f}")
print(f"  • Entropía cola: {result['tail_entropy']:.4f}")
print(f"  • Ratio de tamaño: {result['size_ratio']:.4f}")
print(f"  • Archivos embebidos: {len(result['embedded_files'])}")

print(f"\n📋 Análisis LSB:")
for channel in result['lsb_analysis']['channels']:
    status = "⚠️ Sospechoso" if channel['suspicious'] else "✅ Normal"
    print(f"  • Canal {channel['channel']}: entropía={channel['lsb_entropy']:.4f}, ratio_1s={channel['ones_ratio']:.4f} - {status}")

print(f"\n⚖️ VEREDICTO:")
print(f"  • ¿Sospechoso?: {'❌ SÍ' if result['is_suspicious'] else '✅ NO'}")
print(f"  • Nivel de amenaza: {result['threat_level'].upper()}")
print(f"  • Razón: {result['reason']}")
print("\n" + "=" * 70)
