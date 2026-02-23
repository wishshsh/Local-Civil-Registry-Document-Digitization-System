"""
Dataset Handler for Philippine Civil Registry Documents
Supports: Form 1A (Birth), Form 2A (Death), Form 3A (Marriage), Form 90 (Marriage License)

Features:
- Document-specific preprocessing
- Handles both printed and handwritten text
- Data augmentation for robustness
- Form field extraction
"""

import cv2
import numpy as np
import torch
from torch.utils.data import Dataset
import albumentations as A
from pathlib import Path
import json


class CivilRegistryDataset(Dataset):
    """
    Dataset for Philippine Civil Registry Forms
    """
    
    def __init__(
        self,
        data_dir,
        annotations_file,
        img_height=64,
        img_width=200,
        augment=False,
        form_type='all'
    ):
        """
        Args:
            data_dir: Directory containing images
            annotations_file: JSON file with image paths and labels
            img_height: Target image height
            img_width: Target image width
            augment: Whether to apply data augmentation
            form_type: 'all', 'form1a', 'form2a', 'form3a', 'form90'
        """
        self.data_dir = Path(data_dir)
        self.img_height = img_height
        self.img_width = img_width
        self.augment = augment
        self.form_type = form_type
        
        # Load annotations
        with open(annotations_file, 'r', encoding='utf-8') as f:
            self.annotations = json.load(f)
        
        # Filter by form type if specified
        if form_type != 'all':
            self.annotations = [
                ann for ann in self.annotations 
                if ann.get('form_type') == form_type
            ]
        
        # Build character set for Philippine civil registry
        # Includes English letters, numbers, and common Filipino characters
        self.chars = self._build_charset()
        self.char_to_idx = {char: idx + 1 for idx, char in enumerate(self.chars)}
        self.char_to_idx['<blank>'] = 0  # CTC blank token
        self.idx_to_char = {v: k for k, v in self.char_to_idx.items()}
        self.num_chars = len(self.char_to_idx)
        
        # Data augmentation pipeline
        if self.augment:
            self.transform = A.Compose([
                A.OneOf([
                    A.GaussNoise(var_limit=(10.0, 50.0), p=0.5),
                    A.ISONoise(color_shift=(0.01, 0.05), intensity=(0.1, 0.5), p=0.5),
                ], p=0.3),
                A.OneOf([
                    A.MotionBlur(blur_limit=3, p=0.5),
                    A.GaussianBlur(blur_limit=3, p=0.5),
                ], p=0.2),
                A.RandomBrightnessContrast(
                    brightness_limit=0.2,
                    contrast_limit=0.2,
                    p=0.3
                ),
                A.OneOf([
                    A.ElasticTransform(alpha=1, sigma=50, alpha_affine=50, p=0.5),
                    A.GridDistortion(num_steps=5, distort_limit=0.3, p=0.5),
                ], p=0.2),
            ])
        
        print(f"✓ Dataset initialized")
        print(f"  Total samples: {len(self)}")
        print(f"  Form type: {form_type}")
        print(f"  Character set size: {self.num_chars}")
        print(f"  Augmentation: {'ON' if augment else 'OFF'}")
    
    def _build_charset(self):
        """
        Build character set for Philippine civil registry
        Includes: A-Z, a-z, 0-9, common punctuation, and special characters
        """
        chars = set()
        
        # Uppercase letters
        chars.update([chr(i) for i in range(ord('A'), ord('Z') + 1)])
        
        # Lowercase letters
        chars.update([chr(i) for i in range(ord('a'), ord('z') + 1)])
        
        # Numbers
        chars.update([chr(i) for i in range(ord('0'), ord('9') + 1)])
        
        # Common punctuation and symbols in civil registry
        chars.update([' ', '.', ',', '-', '/', '(', ')', ':', ';', "'", '"'])
        
        # Additional Filipino-specific characters
        chars.update(['ñ', 'Ñ', 'á', 'é', 'í', 'ó', 'ú'])
        
        return sorted(list(chars))
    
    def __len__(self):
        return len(self.annotations)
    
    def __getitem__(self, idx):
        """
        Get a single sample
        Returns: image, label_encoded, label_length, original_text
        """
        annotation = self.annotations[idx]
        
        # Load image
        img_path = self.data_dir / annotation['image_path']
        img = cv2.imread(str(img_path))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        if img is None:
            raise ValueError(f"Failed to load image: {img_path}")
        
        # Get label
        text = annotation['text']
        
       # Apply augmentation if enabled
        if self.augment:
            augmented = self.transform(image=img)
            img = augmented['image']
        
        # Preprocess image
        img = self._preprocess_image(img)
        
        # Normalize
        img = img.astype(np.float32) / 255.0
        
        # Convert to tensor [1, H, W]
        img = torch.FloatTensor(img).unsqueeze(0)
        
        # Encode label
        label_encoded = self._encode_text(text)
        
        return img, torch.IntTensor(label_encoded), len(label_encoded), text
    
    def _preprocess_image(self, img):
        """
        Preprocess image for civil registry forms
        - Resize to target dimensions
        - Apply adaptive thresholding for better text clarity
        - Denoise
        """
        # Denoise
        img = cv2.fastNlMeansDenoising(img, None, 10, 7, 21)
        
        img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        # Adaptive thresholding for better text extraction
        img = cv2.adaptiveThreshold(
            img, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11, 2
        )
        
        # Resize to target dimensions
        img = cv2.resize(img, (self.img_width, self.img_height))
        
        return img
    
    def _encode_text(self, text):
        """
        Encode text to indices
        Characters not in charset are ignored
        """
        encoded = []
        for char in text:
            if char in self.char_to_idx:
                encoded.append(self.char_to_idx[char])
            # Skip unknown characters
        return encoded
    
    def decode_prediction(self, indices):
        """
        Decode prediction indices to text
        """
        chars = []
        for idx in indices:
            if idx != 0 and idx in self.idx_to_char:  # Skip blank
                chars.append(self.idx_to_char[idx])
        return ''.join(chars)


class FormFieldDataset(Dataset):
    """
    Dataset for specific form fields
    Used for training on specific sections like names, dates, addresses
    """
    
    def __init__(self, data_dir, field_type, **kwargs):
        """
        Args:
            data_dir: Directory containing field images
            field_type: 'name', 'date', 'address', 'place', etc.
        """
        self.field_type = field_type
        self.base_dataset = CivilRegistryDataset(data_dir, **kwargs)
        
        # Filter annotations by field type
        self.annotations = [
            ann for ann in self.base_dataset.annotations
            if ann.get('field_type') == field_type
        ]
    
    def __len__(self):
        return len(self.annotations)
    
    def __getitem__(self, idx):
        return self.base_dataset[idx]


def collate_fn(batch):
    """
    Custom collate function for DataLoader
    Handles variable-length sequences for CTC loss
    """
    images, labels, label_lengths, texts = zip(*batch)
    
    # Stack images
    images = torch.stack(images, dim=0)
    
    # Concatenate labels for CTC loss
    labels_cat = torch.cat(labels)
    label_lengths = torch.IntTensor(label_lengths)
    
    return images, labels_cat, label_lengths, texts


def create_annotation_file(image_dir, output_file):
    """
    Helper function to create annotation file from directory structure
    
    Expected structure:
    image_dir/
        form1a/
            name_001.jpg  -> text: "Juan Dela Cruz"
            date_001.jpg  -> text: "01/15/1990"
        form2a/
            ...
    
    Each image should have a corresponding .txt file with the same name
    """
    image_dir = Path(image_dir)
    annotations = []
    
    for img_path in image_dir.rglob('*.jpg'):
        txt_path = img_path.with_suffix('.txt')
        
        if txt_path.exists():
            with open(txt_path, 'r', encoding='utf-8') as f:
                text = f.read().strip()
            
            # Determine form type from directory
            form_type = img_path.parent.name
            
            # Determine field type from filename
            field_type = img_path.stem.split('_')[0]
            
            annotations.append({
                'image_path': str(img_path.relative_to(image_dir)),
                'text': text,
                'form_type': form_type,
                'field_type': field_type
            })
    
    # Save annotations
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(annotations, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Created annotation file: {output_file}")
    print(f"  Total annotations: {len(annotations)}")
    
    return annotations


if __name__ == "__main__":
    # Example usage
    print("=" * 60)
    print("Civil Registry Dataset Handler")
    print("=" * 60)
    
    # Create sample annotation file structure
    print("\nTo use this dataset:")
    print("1. Organize your images in this structure:")
    print("   data/")
    print("     form1a/")
    print("       name_001.jpg + name_001.txt")
    print("       date_001.jpg + date_001.txt")
    print("     form2a/")
    print("       ...")
    print("\n2. Create annotation file:")
    print("   create_annotation_file('data/', 'annotations.json')")
    print("\n3. Load dataset:")
    print("   dataset = CivilRegistryDataset('data/', 'annotations.json')")
