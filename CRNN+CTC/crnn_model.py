"""
CRNN+CTC Model for Philippine Civil Registry Document OCR
Based on: Local Civil Registry Document Digitization and Data Extraction
Target Documents: Form 1A (Birth), Form 2A (Death), Form 3A (Marriage), Form 90 (Marriage License)

Architecture:
- CNN: Feature extraction from document images
- Bidirectional LSTM: Sequential modeling
- CTC: Alignment-free decoding
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class CRNN_CivilRegistry(nn.Module):
    """
    CRNN model optimized for Philippine Civil Registry forms
    Handles both printed and handwritten text recognition
    """
    
    def __init__(self, img_height=64, num_chars=95, hidden_size=256, num_lstm_layers=2):
        super(CRNN_CivilRegistry, self).__init__()
        
        self.img_height = img_height
        self.num_chars = num_chars  # Includes alphanumeric + special characters
        self.hidden_size = hidden_size
        
        # CNN Feature Extractor
        # Optimized for civil registry form structure
        self.cnn = nn.Sequential(
            # Block 1: Initial feature extraction
            nn.Conv2d(1, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 64 -> 32
            
            # Block 2: Deeper features
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 32 -> 16
            
            # Block 3: Complex pattern recognition
            nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            
            nn.Conv2d(256, 256, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(2, 1), stride=(2, 1)),  # 16 -> 8 (height only)
            
            # Block 4: Fine details for handwriting
            nn.Conv2d(256, 512, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            
            nn.Conv2d(512, 512, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(2, 1), stride=(2, 1)),  # 8 -> 4
            
            # Block 5: Final refinement
            nn.Conv2d(512, 512, kernel_size=2, stride=1, padding=0),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
        )
        
        # Calculate RNN input size
        # After CNN: height becomes smaller, channels increase
        self.rnn_input_size = 512 * (img_height // 16 - 1)  # Approximate
        
        # Bidirectional LSTM for sequential modeling
        # Handles both left-to-right and right-to-left context
        self.rnn = nn.LSTM(
            input_size=self.rnn_input_size,
            hidden_size=hidden_size,
            num_layers=num_lstm_layers,
            bidirectional=True,
            batch_first=False,
            dropout=0.3 if num_lstm_layers > 1 else 0
        )
        
        # Output layer for character prediction
        self.fc = nn.Linear(hidden_size * 2, num_chars)  # *2 for bidirectional
        
    def forward(self, x):
        """
        Forward pass
        Args:
            x: Input tensor [batch, 1, height, width]
        Returns:
            Output tensor [seq_len, batch, num_chars]
        """
        # CNN feature extraction
        conv_features = self.cnn(x)  # [batch, channels, height, width]
        
        # Prepare for RNN
        batch_size, channels, height, width = conv_features.size()
        
        # Reshape: collapse height into channels, sequence is width
        conv_features = conv_features.permute(3, 0, 1, 2)  # [width, batch, channels, height]
        conv_features = conv_features.reshape(width, batch_size, channels * height)
        
        # RNN processing
        rnn_output, _ = self.rnn(conv_features)  # [seq_len, batch, hidden*2]
        
        # Character prediction
        output = self.fc(rnn_output)  # [seq_len, batch, num_chars]
        
        return output


class CRNN_Ensemble(nn.Module):
    """
    Ensemble model for better accuracy
    Combines predictions from multiple CRNN models
    """
    
    def __init__(self, num_models=3, **kwargs):
        super(CRNN_Ensemble, self).__init__()
        
        self.models = nn.ModuleList([
            CRNN_CivilRegistry(**kwargs) for _ in range(num_models)
        ])
        
    def forward(self, x):
        outputs = [model(x) for model in self.models]
        # Average ensemble
        return torch.mean(torch.stack(outputs), dim=0)


def get_crnn_model(model_type='standard', **kwargs):
    """
    Factory function to create CRNN models
    
    Args:
        model_type: 'standard', 'ensemble', 'lightweight'
        **kwargs: Model parameters
        
    Returns:
        CRNN model instance
    """
    if model_type == 'ensemble':
        return CRNN_Ensemble(**kwargs)
    elif model_type == 'lightweight':
        # Lighter version for faster inference
        kwargs['hidden_size'] = kwargs.get('hidden_size', 128)
        kwargs['num_lstm_layers'] = 1
        return CRNN_CivilRegistry(**kwargs)
    else:
        return CRNN_CivilRegistry(**kwargs)


def initialize_weights(model):
    """Initialize model weights properly"""
    for m in model.modules():
        if isinstance(m, nn.Conv2d):
            nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            if m.bias is not None:
                nn.init.constant_(m.bias, 0)
        elif isinstance(m, nn.BatchNorm2d):
            nn.init.constant_(m.weight, 1)
            nn.init.constant_(m.bias, 0)
        elif isinstance(m, nn.Linear):
            nn.init.normal_(m.weight, 0, 0.01)
            nn.init.constant_(m.bias, 0)
        elif isinstance(m, nn.LSTM):
            for name, param in m.named_parameters():
                if 'weight' in name:
                    nn.init.orthogonal_(param)
                elif 'bias' in name:
                    nn.init.constant_(param, 0)


if __name__ == "__main__":
    # Test the model
    print("=" * 60)
    print("CRNN Model for Philippine Civil Registry Documents")
    print("=" * 60)
    
    # Create model
    model = get_crnn_model(
        model_type='standard',
        img_height=64,
        num_chars=95,
        hidden_size=256,
        num_lstm_layers=2
    )
    
    # Initialize weights
    initialize_weights(model)
    
    # Test with dummy input
    batch_size = 4
    img_height = 64
    img_width = 200
    
    dummy_input = torch.randn(batch_size, 1, img_height, img_width)
    
    # Forward pass
    output = model(dummy_input)
    
    print(f"\n✓ Model initialized successfully")
    print(f"  Input shape:  {dummy_input.shape}")
    print(f"  Output shape: {output.shape}")
    print(f"  Parameters:   {sum(p.numel() for p in model.parameters()):,}")
    
    # Model summary
    print("\n" + "=" * 60)
    print("Model Architecture:")
    print("=" * 60)
    print(model)
