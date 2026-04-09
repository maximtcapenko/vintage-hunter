import torch
import logging

from sentence_transformers import SentenceTransformer
from PIL import Image
from transformers import CLIPProcessor, CLIPModel

lpgger = logging.getLogger(__name__) 

class EmbeddingService:
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            cls._model = SentenceTransformer('./ai-models/all-mpnet-base-v2')
        return cls._model

    @classmethod
    def encode(cls, text: str):
        if not text:
            return []
        
        model = cls.get_model()
        return model.encode(
            text, 
            convert_to_tensor=False, 
            show_progress_bar=False
        ).tolist()
    
class ImageVectorService:
    MODEL_PATH = './ai-models/clip-vit-base-patch32'
    _model = None
    _processor = None

    @classmethod
    def load_model(cls):
        if cls._model is None or cls._processor is None:
            cls._model = CLIPModel.from_pretrained(cls.MODEL_PATH)
            cls._processor = CLIPProcessor.from_pretrained(cls.MODEL_PATH)
            cls._model.eval()
            
            if torch.backends.mps.is_available():
                device = "mps"
            elif torch.cuda.is_available():
                device = "cuda"
            else:
                device = "cpu"
            cls._model.to(device)

    @classmethod
    def encode(cls, image_input):
        cls.load_model()
        
        try:
            image = Image.open(image_input).convert("RGB")            
            device = cls._model.device
            
            inputs = cls._processor(images=image, return_tensors="pt").to(device)

            with torch.no_grad():
                outputs = cls._model.get_image_features(**inputs)
                image_features = outputs.pooler_output if hasattr(outputs, 'pooler_output') else outputs
                image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
            
            return image_features.cpu().numpy().flatten().tolist()            
        except Exception as e:
            lpgger.error('Error encoding image: {e}', exc_info=True)
            return None
        