"""
AI-Generated Image Detection Service

Detects if uploaded images are AI-generated to prevent fraudulent complaints.
Uses multiple detection methods:
1. Metadata analysis (AI tools often leave signatures)
2. File size and compression patterns
3. EXIF data analysis
4. Image characteristics analysis
"""

import base64
import io
import re
from PIL import Image
from PIL.ExifTags import TAGS
import hashlib

class AIImageDetector:
    """
    Detect AI-generated images using multiple heuristics
    """
    
    # Known AI generation tool signatures in metadata
    AI_TOOL_SIGNATURES = [
        'midjourney', 'stable diffusion', 'dall-e', 'dalle', 'craiyon',
        'leonardo.ai', 'playground ai', 'nightcafe', 'artbreeder',
        'deepai', 'starryai', 'wombo', 'dream', 'jasper art',
        'canva ai', 'adobe firefly', 'bing image creator',
        'stable-diffusion', 'sd-', 'automatic1111', 'invoke',
        'diffusion', 'generated', 'synthesized', 'artificial'
    ]
    
    # Suspicious patterns in filenames
    SUSPICIOUS_FILENAME_PATTERNS = [
        r'generated', r'ai[_-]?gen', r'dalle', r'midjourney',
        r'stable[_-]?diffusion', r'sd[_-]?\d+', r'img2img',
        r'txt2img', r'dream', r'synthesized'
    ]
    
    @staticmethod
    def detect_ai_image(base64_image_data):
        """
        Main detection function - analyzes image for AI generation indicators
        
        Args:
            base64_image_data (str): Base64 encoded image with data URL prefix
            
        Returns:
            dict: {
                'is_ai_generated': bool,
                'confidence': float (0-100),
                'reasons': list of detection reasons,
                'warnings': list of warnings
            }
        """
        try:
            # Parse base64 data
            if ',' in base64_image_data:
                header, base64_data = base64_image_data.split(',', 1)
            else:
                base64_data = base64_image_data
            
            # Decode image
            image_bytes = base64.b64decode(base64_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Run multiple detection methods
            detection_results = []
            confidence_scores = []
            warnings = []
            
            # Method 1: Metadata Analysis
            metadata_result = AIImageDetector._check_metadata(image)
            if metadata_result['detected']:
                detection_results.append(metadata_result['reason'])
                confidence_scores.append(metadata_result['confidence'])
            
            # Method 2: EXIF Data Analysis
            exif_result = AIImageDetector._check_exif_data(image)
            if exif_result['detected']:
                detection_results.append(exif_result['reason'])
                confidence_scores.append(exif_result['confidence'])
            
            # Method 3: Image Characteristics
            characteristics_result = AIImageDetector._check_image_characteristics(image, len(image_bytes))
            if characteristics_result['suspicious']:
                warnings.append(characteristics_result['warning'])
                confidence_scores.append(characteristics_result['confidence'])
            
            # Method 4: File Size Patterns
            filesize_result = AIImageDetector._check_file_size_patterns(image, len(image_bytes))
            if filesize_result['suspicious']:
                warnings.append(filesize_result['warning'])
                confidence_scores.append(filesize_result['confidence'])
            
            # Calculate overall confidence with weighted scoring
            # Only metadata and EXIF detections are strong indicators
            strong_indicators = [s for s in confidence_scores[:2] if s > 0]  # First 2 are metadata/EXIF
            weak_indicators = confidence_scores[2:] if len(confidence_scores) > 2 else []
            
            if len(strong_indicators) > 0:
                # Strong evidence found (metadata/EXIF)
                avg_confidence = sum(strong_indicators) / len(strong_indicators)
            elif len(weak_indicators) > 0:
                # Only weak evidence (characteristics/file size)
                avg_confidence = sum(weak_indicators) / len(weak_indicators) * 0.5  # Reduce weight
            else:
                avg_confidence = 0
            
            # Determine if AI-generated (VERY high confidence threshold to avoid false positives)
            # Only flag if we have strong evidence (metadata/EXIF) with 85%+ confidence
            is_ai_generated = (len(strong_indicators) > 0 and avg_confidence >= 85)
            
            return {
                'is_ai_generated': is_ai_generated,
                'confidence': round(avg_confidence, 2),
                'reasons': detection_results,
                'warnings': warnings,
                'recommendation': AIImageDetector._get_recommendation(is_ai_generated, avg_confidence)
            }
            
        except Exception as e:
            # If detection fails, allow image but log warning
            return {
                'is_ai_generated': False,
                'confidence': 0,
                'reasons': [],
                'warnings': [f'Detection error: {str(e)}'],
                'recommendation': 'Unable to verify image authenticity. Manual review recommended.'
            }
    
    @staticmethod
    def _check_metadata(image):
        """Check image metadata for AI generation signatures"""
        try:
            # Check image info
            info = image.info
            
            # Convert all metadata to lowercase for checking
            metadata_str = str(info).lower()
            
            # Check for AI tool signatures
            for signature in AIImageDetector.AI_TOOL_SIGNATURES:
                if signature in metadata_str:
                    return {
                        'detected': True,
                        'reason': f'AI tool signature detected in metadata: {signature}',
                        'confidence': 95
                    }
            
            # Check for common AI generation parameters
            ai_params = ['prompt', 'negative_prompt', 'steps', 'sampler', 'cfg_scale', 'seed']
            found_params = [param for param in ai_params if param in metadata_str]
            
            if len(found_params) >= 2:
                return {
                    'detected': True,
                    'reason': f'AI generation parameters found: {", ".join(found_params)}',
                    'confidence': 90
                }
            
            return {'detected': False, 'reason': None, 'confidence': 0}
            
        except:
            return {'detected': False, 'reason': None, 'confidence': 0}
    
    @staticmethod
    def _check_exif_data(image):
        """Check EXIF data for AI generation indicators"""
        try:
            exif_data = image._getexif()
            
            if not exif_data:
                # No EXIF data - suspicious for real photos
                return {
                    'detected': False,
                    'reason': None,
                    'confidence': 0
                }
            
            # Convert EXIF data to readable format
            exif_dict = {}
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                exif_dict[tag] = str(value).lower()
            
            # Check software field for AI tools
            if 'Software' in exif_dict:
                software = exif_dict['Software']
                for signature in AIImageDetector.AI_TOOL_SIGNATURES:
                    if signature in software:
                        return {
                            'detected': True,
                            'reason': f'AI generation software detected: {software}',
                            'confidence': 95
                        }
            
            # Check for missing camera data (real photos have camera info)
            camera_fields = ['Make', 'Model', 'LensModel']
            has_camera_data = any(field in exif_dict for field in camera_fields)
            
            if not has_camera_data:
                # Missing camera data - could be AI or screenshot
                return {
                    'detected': False,
                    'reason': None,
                    'confidence': 30  # Low confidence, just suspicious
                }
            
            return {'detected': False, 'reason': None, 'confidence': 0}
            
        except:
            return {'detected': False, 'reason': None, 'confidence': 0}
    
    @staticmethod
    def _check_image_characteristics(image, file_size):
        """Check image characteristics for AI generation patterns"""
        try:
            width, height = image.size
            
            # AI images often have specific aspect ratios
            aspect_ratio = width / height
            common_ai_ratios = [1.0, 1.5, 0.67, 1.78, 0.56]  # 1:1, 3:2, 2:3, 16:9, 9:16
            
            is_common_ai_ratio = any(abs(aspect_ratio - ratio) < 0.05 for ratio in common_ai_ratios)
            
            # AI images often have specific resolutions
            common_ai_resolutions = [512, 768, 1024, 1536, 2048]
            has_ai_resolution = width in common_ai_resolutions or height in common_ai_resolutions
            
            # Check if image is suspiciously perfect
            if is_common_ai_ratio and has_ai_resolution:
                return {
                    'suspicious': True,
                    'warning': f'Image has characteristics common to AI-generated images (resolution: {width}x{height})',
                    'confidence': 40
                }
            
            return {'suspicious': False, 'warning': None, 'confidence': 0}
            
        except:
            return {'suspicious': False, 'warning': None, 'confidence': 0}
    
    @staticmethod
    def _check_file_size_patterns(image, file_size):
        """Check file size patterns for AI generation indicators"""
        try:
            width, height = image.size
            total_pixels = width * height
            
            # Calculate bytes per pixel
            if total_pixels > 0:
                bytes_per_pixel = file_size / total_pixels
                
                # AI images often have unusual compression patterns
                # Real photos: 0.5-3 bytes/pixel
                # AI images: often very consistent compression
                
                if bytes_per_pixel < 0.3:
                    return {
                        'suspicious': True,
                        'warning': 'Unusually high compression detected (common in AI-generated images)',
                        'confidence': 35
                    }
                
                if bytes_per_pixel > 5:
                    return {
                        'suspicious': True,
                        'warning': 'Unusually low compression detected',
                        'confidence': 25
                    }
            
            return {'suspicious': False, 'warning': None, 'confidence': 0}
            
        except:
            return {'suspicious': False, 'warning': None, 'confidence': 0}
    
    @staticmethod
    def _get_recommendation(is_ai_generated, confidence):
        """Get recommendation based on detection results"""
        if is_ai_generated and confidence >= 85:
            return 'REJECT: Strong evidence of AI-generated image (metadata/EXIF signatures found). Please upload real photos taken with your camera/phone.'
        elif confidence >= 60:
            return 'FLAG: Possible AI generation indicators. Officer will verify during site visit.'
        elif confidence >= 30:
            return 'WARN: Minor indicators detected. Image accepted but will be verified.'
        else:
            return 'ACCEPT: Image appears authentic. No AI generation indicators found.'
    
    @staticmethod
    def batch_detect(base64_images):
        """
        Detect AI generation for multiple images
        
        Args:
            base64_images (list): List of base64 encoded images
            
        Returns:
            dict: {
                'all_authentic': bool,
                'ai_detected_count': int,
                'results': list of individual detection results
            }
        """
        results = []
        ai_count = 0
        
        for idx, img_data in enumerate(base64_images):
            result = AIImageDetector.detect_ai_image(img_data)
            result['image_index'] = idx + 1
            results.append(result)
            
            if result['is_ai_generated']:
                ai_count += 1
        
        return {
            'all_authentic': ai_count == 0,
            'ai_detected_count': ai_count,
            'total_images': len(base64_images),
            'results': results
        }
