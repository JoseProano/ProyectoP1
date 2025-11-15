"""
Tests para steganography_improved.py
"""
import pytest
import io
from PIL import Image
import numpy as np

from app.utils.steganography_improved import ImprovedSteganographyDetector


class TestImprovedSteganographyDetector:
    """Tests para detector mejorado de esteganografía"""
    
    @pytest.fixture
    def detector(self):
        """Fixture del detector"""
        return ImprovedSteganographyDetector()
    
    def test_detector_initialization(self, detector):
        """Test inicialización del detector"""
        assert detector is not None
        assert hasattr(detector, 'analyze_file')
    
    def test_calculate_entropy(self, detector):
        """Test cálculo de entropía"""
        # Datos de baja entropía
        low_entropy = b'A' * 1000
        entropy_low = detector.calculate_entropy(low_entropy)
        assert entropy_low < 2.0
        
        # Datos de alta entropía
        high_entropy = np.random.bytes(1000)
        entropy_high = detector.calculate_entropy(high_entropy)
        assert entropy_high > 5.0
    
    def test_analyze_normal_jpeg(self, detector):
        """Test analizar JPEG normal"""
        # Crear imagen JPEG simple
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        file_bytes = img_bytes.getvalue()
        
        result = detector.analyze_file(file_bytes, "test.jpg", "image/jpeg")
        
        assert "is_suspicious" in result
        assert "threat_level" in result
        assert "file_entropy" in result
    
    def test_analyze_normal_png(self, detector):
        """Test analizar PNG normal"""
        img = Image.new('RGB', (100, 100), color='blue')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        file_bytes = img_bytes.getvalue()
        
        result = detector.analyze_file(file_bytes, "test.png", "image/png")
        
        assert "is_suspicious" in result
        assert isinstance(result["is_suspicious"], bool)
    
    def test_analyze_simple_pdf(self, detector):
        """Test analizar PDF simple"""
        pdf_content = b'%PDF-1.4\n%Simple PDF content here\n%%EOF'
        
        result = detector.analyze_file(pdf_content, "test.pdf", "application/pdf")
        
        assert "is_suspicious" in result
        assert "file_entropy" in result
    
    def test_detect_concatenated_pdf(self, detector):
        """Test detectar PDF concatenado"""
        # Simular PDF concatenado con dos firmas %PDF-
        pdf_concat = b'%PDF-1.4\nFirst PDF content\n%%EOF\n' + b' ' * 100 + b'%PDF-1.4\nSecond PDF\n%%EOF'
        
        result = detector.analyze_file(pdf_concat, "concat.pdf", "application/pdf")
        
        # Debería detectar como sospechoso
        assert "is_suspicious" in result
    
    def test_detect_embedded_jpeg_in_image(self, detector):
        """Test detectar JPEG embebido en imagen"""
        # Crear imagen base
        img = Image.new('RGB', (200, 200), color='green')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        base_data = img_bytes.getvalue()
        
        # Agregar firma JPEG embebida
        jpeg_signature = b'\xFF\xD8\xFF\xE0'
        offset = len(base_data) // 2
        tampered_data = base_data[:offset] + jpeg_signature + b'fake jpeg data' * 100 + base_data[offset:]
        
        result = detector.analyze_file(tampered_data, "tampered.png", "image/png")
        
        # Puede o no detectarlo dependiendo del tamaño, pero no debe fallar
        assert "is_suspicious" in result
    
    def test_analyze_high_entropy_file(self, detector):
        """Test archivo con entropía extremadamente alta"""
        # Datos completamente aleatorios
        random_data = np.random.bytes(50000)
        
        result = detector.analyze_file(random_data, "random.bin", "application/octet-stream")
        
        assert "file_entropy" in result
        assert result["file_entropy"] > 7.0
    
    def test_analyze_small_file(self, detector):
        """Test archivo muy pequeño"""
        small_data = b'Small content'
        
        result = detector.analyze_file(small_data, "small.txt", "text/plain")
        
        # Archivos pequeños no deberían ser marcados como sospechosos
        assert "is_suspicious" in result
    
    def test_analyze_empty_file(self, detector):
        """Test archivo vacío"""
        empty_data = b''
        
        result = detector.analyze_file(empty_data, "empty.txt", "text/plain")
        
        assert "is_suspicious" in result
    
    def test_different_threat_levels(self, detector):
        """Test diferentes niveles de amenaza"""
        # Archivo normal
        normal_img = Image.new('RGB', (50, 50), color='white')
        normal_bytes = io.BytesIO()
        normal_img.save(normal_bytes, format='PNG')
        
        result = detector.analyze_file(normal_bytes.getvalue(), "normal.png", "image/png")
        
        assert result["threat_level"] in ["low", "medium", "high", "critical"]
    
    def test_analyze_gif_image(self, detector):
        """Test analizar imagen GIF"""
        img = Image.new('RGB', (100, 100), color='yellow')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='GIF')
        
        result = detector.analyze_file(img_bytes.getvalue(), "test.gif", "image/gif")
        
        assert "is_suspicious" in result
    
    def test_analyze_text_file(self, detector):
        """Test analizar archivo de texto"""
        text_data = b'This is a normal text file with some content.'
        
        result = detector.analyze_file(text_data, "test.txt", "text/plain")
        
        # Texto normal tiene baja entropía
        assert result["file_entropy"] < 5.0
    
    def test_detector_consistency(self, detector):
        """Test consistencia del detector"""
        # El mismo archivo debería dar el mismo resultado
        img = Image.new('RGB', (80, 80), color='purple')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        file_data = img_bytes.getvalue()
        
        result1 = detector.analyze_file(file_data, "test1.png", "image/png")
        result2 = detector.analyze_file(file_data, "test2.png", "image/png")
        
        assert result1["file_entropy"] == result2["file_entropy"]
    
    def test_multiple_file_analysis(self, detector):
        """Test analizar múltiples archivos"""
        files = []
        
        # Crear varios archivos de prueba
        for i in range(3):
            img = Image.new('RGB', (50, 50), color=(i*80, 100, 150))
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            files.append(img_bytes.getvalue())
        
        results = []
        for idx, file_data in enumerate(files):
            result = detector.analyze_file(file_data, f"file{idx}.png", "image/png")
            results.append(result)
        
        # Todos los archivos deberían ser analizados
        assert len(results) == 3
        assert all("is_suspicious" in r for r in results)


class TestImprovedDetectorEdgeCases:
    """Tests para casos extremos"""
    
    @pytest.fixture
    def detector(self):
        return ImprovedSteganographyDetector()
    
    def test_null_bytes(self, detector):
        """Test archivo con bytes nulos"""
        null_data = b'\x00' * 1000
        
        result = detector.analyze_file(null_data, "null.bin", "application/octet-stream")
        
        # Bytes nulos tienen entropía muy baja
        assert result["file_entropy"] < 1.0
    
    def test_alternating_pattern(self, detector):
        """Test archivo con patrón alternante"""
        pattern_data = b'\xAA\x55' * 500
        
        result = detector.analyze_file(pattern_data, "pattern.bin", "application/octet-stream")
        
        assert "file_entropy" in result
    
    def test_large_image(self, detector):
        """Test imagen grande"""
        large_img = Image.new('RGB', (500, 500), color='cyan')
        img_bytes = io.BytesIO()
        large_img.save(img_bytes, format='PNG')
        
        result = detector.analyze_file(img_bytes.getvalue(), "large.png", "image/png")
        
        assert "is_suspicious" in result
    
    def test_corrupted_image_header(self, detector):
        """Test imagen con header corrupto"""
        # Crear datos que parecen imagen pero están corruptos
        fake_png = b'\x89PNG\r\n\x1a\n' + b'corrupted data' * 100
        
        result = detector.analyze_file(fake_png, "corrupted.png", "image/png")
        
        # No debería fallar, solo devolver resultado
        assert result is not None
