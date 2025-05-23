import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import inspect

from transformers import AutoModelForCausalLM

class TimerAdapter(nn.Module):
    """
    2D Image to Patch Embedding
    """
    def __init__(self, encoder_dim, project_dim, hidden_dim=None):

        super().__init__()
        self.encoder_dim = encoder_dim
        self.project_dim = project_dim
        self.hidden_dim = hidden_dim

        if self.hidden_dim is None:
            self.hidden_dim = project_dim * 2

        self.pre_norm = nn.LayerNorm(self.project_dim)
        self.proj = nn.Sequential(
            nn.Linear(self.encoder_dim, self.hidden_dim),
            nn.ReLU(),
            nn.Linear(self.hidden_dim, self.project_dim),
        )
        # self.proj = nn.Sequential(
        #     nn.Linear(self.encoder_dim, self.hidden_dim),
        #     nn.GELU(),
        #     nn.Linear(self.hidden_dim, self.hidden_dim),
        #     nn.GELU(),
        #     nn.Linear(self.hidden_dim, self.project_dim),
        # )

    def forward(self, x):        
        x = self.proj(x)
        return x + self.pre_norm(x)

class TimerEncoder(nn.Module):
    def __init__(
        self,
        encoder_path,
        project_dim,
        train_mode="adapter",
        device="cuda",
    ):
        super(TimerEncoder, self).__init__()
        self.device = device
        self.prediction_length = 96
        self.encoder_dim = 1024

        self.model = AutoModelForCausalLM.from_pretrained(encoder_path, trust_remote_code=True).to(self.device)
        self.adapter = TimerAdapter(self.encoder_dim, project_dim).to(self.device)
        self.train_mode = train_mode    
    def forward(self, x): 
        
        outputs = self.model.forward(x, output_hidden_states=True)
        outputs = outputs.hidden_states[-1]
        outputs = self.adapter(outputs)
        return outputs

if __name__ == "__main__":
    encoder = TimerEncoder(encoder_path='thuml/timer-base-84m', project_dim=1024, train_mode="adapter", device="cuda")
    batch_size, lookback_length = 1, 2880
    x = torch.randn(batch_size, lookback_length).cuda()
    outputs = encoder(x)
    print("last hidden_states shape:", outputs.shape)
    print("timer encoder test pass")