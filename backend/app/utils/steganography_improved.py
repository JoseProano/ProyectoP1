"""
Sistema mejorado de detección de esteganografía
Detecta específicamente:
- LSB steganography en imágenes
- Archivos concatenados (copy /b)
- Datos embebidos en PDFs
"""
import io
import math
from typing import Dict
from PIL import Image
import numpy as np
from collections import Counter

from app.config import settings


class ImprovedSteganographyDetector:
    """Detector mejorado de esteganografía"""
    
    def __init__(self, entropy_threshold: float = None):
        self.entropy_threshold = entropy_threshold or settings.ENTROPY_THRESHOLD
    
    def calculate_entropy(self, data: bytes) -> float:
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
    
    def analyze_file(self, file_bytes: bytes, filename: str, mime_type: str = None) -> Dict:
        """Análisis completo mejorado por tipo de archivo"""
        try:
            # Calcular entropía general
            file_entropy = self.calculate_entropy(file_bytes)
            
            # Determinar tipo
            is_pdf = mime_type and 'pdf' in mime_type.lower()
            is_image = mime_type and mime_type.startswith('image/')
            
            # Análisis específico
            if is_pdf:
                return self._analyze_pdf(file_bytes, filename, file_entropy)
            elif is_image:
                return self._analyze_image(file_bytes, filename, file_entropy, mime_type)
            else:
                return self._analyze_generic(file_bytes, filename, file_entropy)
        
        except Exception as e:
            return {
                'filename': filename,
                'error': str(e),
                'is_suspicious': True,
                'threat_level': 'unknown'
            }
    
    def _analyze_pdf(self, file_bytes: bytes, filename: str, file_entropy: float) -> Dict:
        """
        Análisis de PDFs: detecta PDFs concatenados y patrones maliciosos
        PDFs normales pueden tener entropía 7.5-8.0 debido a compresión y fuentes embebidas
        """
        # 1. Detectar PDFs concatenados (copy /b pdf1+pdf2)
        # Buscar firmas %PDF- adicionales después de la primera
        pdf_signature = b'%PDF-'
        first_pdf = file_bytes.find(pdf_signature)
        second_pdf = file_bytes.find(pdf_signature, first_pdf + 100)  # Buscar después de los primeros 100 bytes
        
        has_concatenated_pdf = second_pdf != -1
        
        # 2. Patrones maliciosos en PDFs
        malicious_patterns = [
            (b'/JavaScript', 'JavaScript embebido'),
            (b'/Launch', 'Comando de ejecución'),
            (b'/AA', 'Auto-acción'),
            (b'/OpenAction', 'Acción al abrir')
        ]
        
        detected = []
        for pattern, desc in malicious_patterns:
            if pattern in file_bytes:
                detected.append(desc)
        
        # 3. Contar archivos embebidos normales
        embedded_count = file_bytes.count(b'/EmbeddedFile')
        
        # === DECISIÓN ===
        # Marcar como sospechoso si:
        # - Tiene PDF concatenado (copy /b) - CRÍTICO
        # - Entropía > 8.2 (extremadamente alta) O
        # - Tiene patrones maliciosos O
        # - Múltiples archivos embebidos (>3)
        
        if has_concatenated_pdf:
            is_suspicious = True
            threat_level = 'critical'
            reason = f"PDF concatenado detectado (posición: {second_pdf})"
        elif len(detected) > 0:
            is_suspicious = True
            threat_level = 'high'
            reason = f"Patrones maliciosos: {', '.join(detected)}"
        elif embedded_count > 3:
            is_suspicious = True
            threat_level = 'medium'
            reason = f"{embedded_count} archivos embebidos"
        elif file_entropy > 8.2:
            is_suspicious = True
            threat_level = 'medium'
            reason = "Entropía extremadamente alta"
        else:
            is_suspicious = False
            threat_level = 'low'
            reason = "PDF normal"
        
        return {
            'filename': filename,
            'file_type': 'pdf',
            'file_entropy': float(file_entropy),
            'has_concatenated_pdf': bool(has_concatenated_pdf),
            'concatenated_position': int(second_pdf) if second_pdf != -1 else None,
            'malicious_patterns': detected,
            'embedded_files_count': int(embedded_count),
            'is_suspicious': bool(is_suspicious),
            'threat_level': threat_level,
            'reason': reason
        }
    
    def _analyze_image(self, file_bytes: bytes, filename: str, file_entropy: float, mime_type: str) -> Dict:
        """
        Análisis de imágenes: detecta LSB steganography y archivos concatenados
        """
        try:
            image = Image.open(io.BytesIO(file_bytes))
            
            # 1. Detectar archivos embebidos (copy /b)
            embedded_files = self._detect_embedded_files(file_bytes)
            has_embedded = len(embedded_files) > 0
            
            # 2. Análisis LSB
            lsb_result = self._analyze_lsb(image)
            lsb_suspicious = lsb_result['is_suspicious']
            
            # 3. Análisis de entropía en la cola del archivo
            # Archivos concatenados tienen alta entropía al final
            tail_start = int(len(file_bytes) * 0.7)
            tail_data = file_bytes[tail_start:]
            tail_entropy = self.calculate_entropy(tail_data) if len(tail_data) > 100 else file_entropy
            
            # 4. Análisis de tamaño
            expected_size = image.width * image.height * 3
            actual_size = len(file_bytes)
            size_ratio = actual_size / expected_size if expected_size > 0 else 0
            
            # Para JPEG, ratio normal es 0.05-0.2 (compresión 5:1 a 20:1)
            # Para PNG, ratio normal es 0.1-0.4 (compresión depende de contenido)
            # Si ratio > 0.3 para JPEG o > 0.6 para PNG, puede tener datos ocultos
            is_jpeg = 'jpeg' in mime_type.lower() or 'jpg' in mime_type.lower()
            is_png = 'png' in mime_type.lower()
            suspicious_size = (is_jpeg and size_ratio > 0.3) or (is_png and size_ratio > 0.6)
            
            # === DECISIÓN FINAL ===
            # CRÍTICO: archivos embebidos (copy /b) - PRIORIDAD MÁXIMA
            if has_embedded:
                is_suspicious = True
                threat_level = 'critical'
                reason = f"Archivos embebidos detectados: {', '.join([e['type'] for e in embedded_files])}"
            # ALTO: LSB sospechoso + entropía extrema
            elif lsb_suspicious and tail_entropy > 7.95:
                is_suspicious = True
                threat_level = 'high'
                reason = "Patrón LSB sospechoso con entropía extrema"
            # MEDIO: Solo marcar como sospechoso si tiene múltiples indicadores
            # Esto reduce drásticamente falsos positivos
            else:
                suspicious_indicators = 0
                reasons_list = []
                
                # Indicador 1: Entropía extremadamente alta y uniforme
                if file_entropy > 7.985 and tail_entropy > 7.985:
                    suspicious_indicators += 1
                    reasons_list.append(f"entropía extrema ({file_entropy:.4f})")
                
                # Indicador 2: Tamaño muy anómalo para el tipo
                if suspicious_size:
                    suspicious_indicators += 1
                    reasons_list.append(f"ratio de tamaño anómalo ({size_ratio:.2f})")
                
                # Indicador 3: Diferencia casi nula entre entropía general y cola
                # (indica datos muy uniformemente distribuidos, típico de cifrado/esteganografía)
                if file_entropy > 7.9 and tail_entropy > 7.9 and abs(file_entropy - tail_entropy) < 0.005:
                    suspicious_indicators += 1
                    reasons_list.append("entropía extremadamente uniforme")
                
                # Requiere AL MENOS 2 indicadores para marcar como sospechoso
                if suspicious_indicators >= 2:
                    is_suspicious = True
                    threat_level = 'medium'
                    reason = "Múltiples indicadores sospechosos: " + ", ".join(reasons_list)
                else:
                    is_suspicious = False
                    threat_level = 'low'
                    reason = "Imagen normal"
            
            return {
                'filename': filename,
                'file_type': 'image',
                'file_entropy': float(file_entropy),
                'tail_entropy': float(tail_entropy),
                'size_ratio': float(size_ratio),
                'embedded_files': embedded_files,
                'lsb_analysis': lsb_result,
                'is_suspicious': bool(is_suspicious),
                'threat_level': threat_level,
                'reason': reason
            }
        
        except Exception as e:
            # Si falla como imagen, analizar como genérico
            return self._analyze_generic(file_bytes, filename, file_entropy)
    
    def _analyze_generic(self, file_bytes: bytes, filename: str, file_entropy: float) -> Dict:
        """Análisis para archivos genéricos"""
        # Solo rechazar entropía extrema (>8.0)
        is_suspicious = file_entropy > 8.0
        
        return {
            'filename': filename,
            'file_type': 'generic',
            'file_entropy': float(file_entropy),
            'is_suspicious': bool(is_suspicious),
            'threat_level': 'high' if is_suspicious else 'low',
            'reason': 'Entropía extremadamente alta' if is_suspicious else 'Normal'
        }
    
    def _analyze_lsb(self, image: Image.Image) -> Dict:
        """Analiza bits menos significativos para detectar steganography"""
        try:
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            pixels = np.array(image)
            height, width, channels = pixels.shape
            
            # Analizar cada canal RGB
            channel_results = []
            for c in range(min(channels, 3)):
                channel_data = pixels[:, :, c]
                lsb_bits = channel_data & 1
                
                # Calcular entropía de LSBs
                lsb_bytes = np.packbits(lsb_bits.flatten())
                entropy = self.calculate_entropy(lsb_bytes.tobytes())
                
                # Ratio de 1s (debe estar cerca de 0.5 en imágenes normales)
                ones_ratio = float(np.sum(lsb_bits)) / float(lsb_bits.size)
                
                # Canal sospechoso si:
                # - Entropía LSB > 7.8 (muy alta para LSBs normales) Y
                # - Ratio desbalanceado (>0.6 o <0.4)
                is_suspicious = entropy > 7.8 and abs(ones_ratio - 0.5) > 0.1
                
                channel_results.append({
                    'channel': int(c),
                    'lsb_entropy': float(entropy),
                    'ones_ratio': float(ones_ratio),
                    'suspicious': bool(is_suspicious)
                })
            
            # Considerar LSB sospechoso si 2+ canales son sospechosos
            suspicious_count = sum(1 for r in channel_results if r['suspicious'])
            is_suspicious = suspicious_count >= 2
            
            return {
                'channels': channel_results,
                'suspicious_count': int(suspicious_count),
                'is_suspicious': bool(is_suspicious)
            }
        
        except Exception as e:
            return {
                'error': str(e),
                'is_suspicious': False
            }
    
    def _detect_embedded_files(self, file_bytes: bytes) -> list:
        """
        Detecta archivos embebidos buscando firmas (magic numbers)
        Esto detecta la técnica copy /b file1+file2
        Mejorado para reducir falsos positivos
        """
        # Firmas de archivos conocidos (solo las más confiables)
        # Excluimos BM (muy común en datos binarios) y otras firmas cortas
        signatures = [
            (b'\xFF\xD8\xFF\xE0', 'JPEG', 4),  # JPEG JFIF más específico
            (b'\xFF\xD8\xFF\xE1', 'JPEG', 4),  # JPEG EXIF
            (b'\x89PNG\r\n\x1a\n', 'PNG', 8),   # PNG completo
            (b'GIF89a', 'GIF', 6),
            (b'GIF87a', 'GIF', 6),
            (b'%PDF-', 'PDF', 5),
            (b'PK\x03\x04', 'ZIP', 4),
        ]
        
        embedded = []
        
        # Buscar firmas después del 30% inicial (más conservador)
        # Esto evita detectar datos del header como archivos embebidos
        search_start = int(len(file_bytes) * 0.3)
        
        # Solo considerar si el archivo es lo suficientemente grande (>10KB)
        # Archivos pequeños no suelen tener otros archivos embebidos
        if len(file_bytes) < 10240:  # 10KB
            return embedded
        
        for signature, file_type, min_length in signatures:
            pos = file_bytes.find(signature, search_start)
            if pos != -1:
                # Verificación adicional: el archivo embebido debe tener tamaño razonable
                # Debe haber al menos 1KB después de la firma
                if pos + 1024 < len(file_bytes):
                    embedded.append({
                        'type': file_type,
                        'position': int(pos),
                        'offset_percentage': float(pos / len(file_bytes) * 100)
                    })
        
        return embedded


# Crear instancia global
improved_detector = ImprovedSteganographyDetector()
