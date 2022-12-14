# Importing the libraries needed
import pandas as pd
from transformers import AutoTokenizer
from torch.utils.data import DataLoader
import torch
import argparse
import logging
#export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:7
import gc
gc.collect()
torch.cuda.empty_cache()
from ImplicatureData import ImplicatureData
from BertClass import BertClass
from train_model import *
logging.basicConfig(level=logging.ERROR)
args = argparse.ArgumentParser(description='fine-tuning on tuned-BERT model')
args.add_argument('-a', '--train_file', type=str, help='train file', required=True)
args.add_argument('-v', '--val_file', type=str, help='val file', required=True)
args.add_argument('-m', '--model_file', type=str, help='model file', required=True)

args = args.parse_args()

train_file = args.train_file
val_file = args.val_file
PATH = args.model_file

#global variables

MAX_LEN = 100
BATCH_SIZE = 25
EPOCHS = 5
LEARNING_RATE = 1e-05


if __name__=="__main__":

    # Setting up the device for GPU usage

    device = 'cuda' if cuda.is_available() else 'cpu'
    model = BertClass()
    model.to(device)
    #freeze the weights
    #for param in model.parameters():
        #param.requires_grad = False

    optimizer = torch.optim.Adam(params=model.parameters(), lr=LEARNING_RATE)
    #when using GPU
    checkpoint = torch.load(PATH)
    #if saved using GPU, and loaded to CPU
    #checkpoint = torch.load(PATH, map_location=torch.device('cpu'))
    model.load_state_dict(checkpoint['model_state_dict'])
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    #model.classifier = torch.nn.Linear(21128,3)
    #for gpu further training
    #model = nn.DataParallel(model, device_ids=[0,1,2,3])
    #model.to(device)

    train_params = {'batch_size': BATCH_SIZE,
                    'shuffle': True,
                    'num_workers': 0
                    }

    #load the data
    train_data = pd.read_csv(train_file, encoding='utf-8-sig')
    val_data = pd.read_csv(val_file, encoding='utf-8-sig')

    train_context = train_data["context"]
    train_utterance = train_data["utterance"]
    train_categories = train_data["implicature"]

    val_context = val_data["context"]
    val_utterance = val_data["utterance"]
    val_categories = val_data["implicature"]

    tokenizer = AutoTokenizer.from_pretrained("bert-base-chinese", truncation=True)

    training_set = ImplicatureData(train_context, train_utterance, train_categories, tokenizer, MAX_LEN)
    training_loader = DataLoader(training_set, **train_params)

    val_set = ImplicatureData(val_context, val_utterance, val_categories, tokenizer, MAX_LEN)
    val_loader = DataLoader(val_set)

    #start training
    model, loss, optimizer = train(model,optimizer, EPOCHS, training_loader, val_loader)
    #save the model
    torch.save({'epoch': EPOCHS,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'loss': loss},'transfer_model1.pt')

    print('All files saved')