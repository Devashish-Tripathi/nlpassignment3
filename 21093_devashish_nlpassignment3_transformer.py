# -*- coding: utf-8 -*-
"""21093_Devashish_nlpassignment3_transformer.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1I-6m4XK9wKS4jSI9n1_ezShHQ_ENMYal

# Imports
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tqdm.notebook import tqdm

import torch
import torch.nn as nn
import transformers

from torch.utils.data import TensorDataset, DataLoader

from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score

"""# Load the data"""

!wget https://raw.githubusercontent.com/debajyotimaz/nlp_assignment/main/train_split.csv
!wget https://raw.githubusercontent.com/debajyotimaz/nlp_assignment/main/test_split.csv

!git clone https://github.com/Devashish-Tripathi/nlpassignment3.git

train_split = pd.read_csv('train_split.csv')
test_split = pd.read_csv('test_split.csv')

train_text = train_split['text'].values
emotions = list(train_split.drop('text', axis = 1).columns)
tr_labels = train_split[emotions].values

"""# Set up BERT for training

Loading BERT tokenizer and creating encodings
"""

tokenizer = transformers.BertTokenizer.from_pretrained('bert-base-uncased')
encodings = tokenizer.batch_encode_plus(train_text, padding= 'longest')

# input_ids = encodings['input_ids']
# token_type_ids = encodings['token_type_ids']
# attention_mask = encodings['attention_mask']

"""Doing train-val split for 75:25 and converting to torch tensor"""

# train_ids, val_ids, train_labels, val_labels, train_token, val_token, train_attn, val_attn = train_test_split(input_ids, tr_labels, token_type_ids, attention_mask, test_size= 0.25, random_state= 0)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
batch_size = 32

# train_ids = torch.tensor(train_ids)
# train_labels = torch.tensor(train_labels)
# train_token = torch.tensor(train_token)
# train_attn = torch.tensor(train_attn)

# val_ids = torch.tensor(val_ids)
# val_labels = torch.tensor(val_labels)
# val_token = torch.tensor(val_token)
# val_attn = torch.tensor(val_attn)

# train_ds = TensorDataset(train_ids, train_labels, train_token, train_attn)
# train_loader = DataLoader(train_ds, batch_size= batch_size)
# val_ds = TensorDataset(val_ids, val_labels, val_token, val_attn)
# val_loader = DataLoader(val_ds, batch_size= batch_size)

"""# Training

## Helper Functions

Helper Function -- train code
"""

# def train_model(model, epochs, loss_func, optimizer, train_loader, val_loader, device, emotions, th= 0.5):
#   model = model.to(device)
#   n_ems = len(emotions)
#   train_losses = []
#   train_f1s = []
#   val_losses = []
#   val_f1s = []
#   for epoch in tqdm(range(epochs), desc = 'Epoch'):
#     # Training
#     model.train()
#     train_loss = 0.0
#     pred_labels, true_labels = [], []
#     for batch in tqdm(train_loader, desc = 'Train Loader' , leave= False):
#       ids = batch[0].to(device)
#       labels = batch[1].to(device)
#       token = batch[2].to(device)
#       attn = batch[3].to(device)

#       optimizer.zero_grad()
#       outputs = model(ids, token_type_ids = None, attention_mask = attn)
#       logits = outputs[0]
#       loss = loss_func(logits.view(-1, n_ems), labels.type_as(logits).view(-1, n_ems))

#       loss.backward()
#       optimizer.step()

#       train_loss += loss.item()
#       pred = torch.sigmoid(logits)
#       pred_lbs = pred.detach().cpu().numpy()
#       true_lbs = labels.to('cpu').numpy()

#       pred_labels.extend(pred_lbs)
#       true_labels.extend(true_lbs)

#     pred_bools = [p1 > th for p1 in pred_labels]
#     true_bools = [t1 == 1 for t1 in true_labels]
#     train_losses.append(train_loss/len(train_loader))
#     train_f1s.append(f1_score(true_bools, pred_bools, average= 'macro'))

#     # Validation
#     model.eval()
#     val_loss = 0.0
#     pred_labels, true_labels = [], []
#     for batch in tqdm(val_loader, desc= 'Val Batch', leave= False):
#       ids = batch[0].to(device)
#       labels = batch[1].to(device)
#       token = batch[2].to(device)
#       attn = batch[3].to(device)

#       with torch.no_grad():
#         outputs = model(ids, token_type_ids = None, attention_mask = attn)
#         logits = outputs[0]
#         pred = torch.sigmoid(logits)
#         loss = loss_func(logits.view(-1, n_ems), labels.type_as(logits).view(-1, n_ems))

#         pred_lbs = pred.detach().cpu().numpy()
#         true_lbs = labels.to('cpu').numpy()
#         val_loss += loss.item()

#       pred_labels.extend(pred_lbs)
#       true_labels.extend(true_lbs)

#     pred_bools = [p1 > th for p1 in pred_labels]
#     true_bools = [t1 == 1 for t1 in true_labels]
#     val_f1s.append(f1_score(true_bools, pred_bools, average= 'macro'))
#     val_losses.append(val_loss/len(val_loader))

#     print(f'Epoch: {epoch+1}\tTrain Loss: {train_losses[epoch]:.3f}\tVal Loss: {val_losses[epoch]:.3f}\tTrain F1: {train_f1s[epoch]:.3f}\tVal F1: {val_f1s[epoch]:.3f}')

#   return train_losses, val_losses, train_f1s, val_f1s

"""Helper function -- Inference code"""

def inference(model, loader, kind, device, emotions, th= 0.5):
  model.eval()
  pred_labels, true_labels = [], []
  for batch in tqdm(loader, desc = f'{kind} Loader', leave= False):
    with torch.no_grad():
      ids = batch[0].to(device)
      labels = batch[1].to(device)
      token = batch[2].to(device)
      attn = batch[3].to(device)

      outputs = model(ids, token_type_ids = None, attention_mask = attn)
      logits = outputs[0]
      pred = torch.sigmoid(logits)

      pred_lbs = pred.detach().cpu().numpy()
      true_lbs = labels.to('cpu').numpy()

      pred_labels.extend(pred_lbs)
      true_labels.extend(true_lbs)

  pred_bools = [p1 > th for p1 in pred_labels]
  true_bools = [t1 == 1 for t1 in true_labels]

  print(f"F1- Macro on {kind} : {f1_score(true_bools, pred_bools, average= 'macro'):.3f}")
  print(classification_report(true_bools, pred_bools, target_names = emotions, zero_division= 0))

"""Helper function -- Curve plot"""

# def disp_plots(train, val, n_epochs, kind):
#   plt.figure()
#   plt.title(f'{kind} curves')
#   plt.plot(range(1, n_epochs+1), train,  label= "Train")
#   plt.plot(range(1, n_epochs+1), val,  label= "Val")
#   plt.xlabel('Epochs')
#   plt.ylabel(kind)
#   plt.legend()
#   plt.tight_layout()
#   plt.show()

"""## Training BERT

Initializing model
"""

# bert_model = transformers.BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels = len(emotions), )

# for name, param in bert_model.named_parameters():
#   if name != 'classifier.weight' and name != 'classifier.bias':
#     param.requires_grad = False

# for name, param in bert_model.named_parameters():
#   if param.requires_grad: print(name)

# epochs = 10
# threshold = 0.5
# lr = 1e-5
# wt_decay = 1e-5

# optimizer = torch.optim.Adam(bert_model.parameters(), lr= lr, weight_decay= wt_decay)
# loss_func = nn.BCEWithLogitsLoss()

"""Training"""

# if device == 'cuda': torch.cuda.clear_cache()

# train_losses, val_losses, train_f1s, val_f1s = train_model(bert_model, epochs, loss_func, optimizer, train_loader, val_loader, device, emotions, threshold)

# disp_plots(train_losses, val_losses, epochs, 'Loss')
# disp_plots(train_f1s, val_f1s, epochs, 'f1_macro')

# torch.save(bert_model.state_dict(), 'bert_model_emotions.pth')

"""# Test inference"""

# Try doing so with Run All

bert_model = transformers.BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels= len(emotions))
wts = torch.load('/content/nlpassignment3/bert_model_emotions_nov12.pth', map_location= device)
bert_model.load_state_dict(wts)

def prep_test(split, emotions, batch_size):

  text = split['text'].values
  labels = split[emotions].values
  encodings = tokenizer.batch_encode_plus(text, padding= 'longest')
  input_ids = torch.tensor(encodings['input_ids'])
  token_type_ids = torch.tensor(encodings['token_type_ids'])
  attention_mask = torch.tensor(encodings['attention_mask'])
  labels = torch.tensor(labels)

  ds = TensorDataset(input_ids, labels, token_type_ids, attention_mask)
  loader = DataLoader(ds, batch_size= batch_size)

  return loader

test_loader = prep_test(test_split, emotions, batch_size)

inference(bert_model, test_loader, 'Test', device, emotions, th= 0.5)