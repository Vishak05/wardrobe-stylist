from pathlib import Path

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

from models.orm import EMBEDDING_DIM

MODEL_NAME = "openai/clip-vit-large-patch14"

_processor = CLIPProcessor.from_pretrained(MODEL_NAME)
_model = CLIPModel.from_pretrained(MODEL_NAME)
_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
_model.to(_device)
_model.eval()


def generate_image_embedding(image_path: Path) -> list[float]:
    image = Image.open(image_path).convert("RGB")
    inputs = _processor(images=image, return_tensors="pt")
    inputs = {k: v.to(_device) for k, v in inputs.items()}

    with torch.no_grad():
        image_features = _model.get_image_features(**inputs)

    image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
    vector = image_features[0].cpu().tolist()

    if len(vector) != EMBEDDING_DIM:
        raise ValueError(
            f"Embedding must be {EMBEDDING_DIM}-dim, got {len(vector)}"
        )
    return vector
