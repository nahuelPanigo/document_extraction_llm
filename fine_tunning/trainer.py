from transformers import Trainer, TrainingArguments,Seq2SeqTrainingArguments
from constants import LOG_DIR,CHECKPOINT_MODEL_PATH,MAX_TOKENS_OUTPUT
import torch
from torch.utils.data import DataLoader
from torch.optim import AdamW
import torch.nn.functional as F


def parse_output(tokenizer,output):
    output =tokenizer.decode(output[0], skip_special_tokens=True, errors="replace")
    output_text = output.split("<|output|>")[1].split("<|end-output|>")[0]
    return tokenizer(output_text, truncation=True, padding=True, return_tensors="pt", max_length=MAX_TOKENS_OUTPUT).input_ids



def collate_fn_custom(batch):
    """
    Collate function para agrupar batches de datos tokenizados.
    Filtra solo las claves necesarias y convierte listas en tensores.
    """
    keys_to_keep = ["input_ids", "attention_mask", "labels"]  # Solo las claves necesarias

    # Construir el batch asegurando que cada clave tenga tensores
    batch_dict = {key: [d[key] for d in batch] for key in keys_to_keep}
    batch_dict = {key: torch.tensor(value) for key, value in batch_dict.items()}

    return batch_dict


def traditional_train(model, tokenized_datasets, learning_rate=2e-5, epochs=3, batch_size=1):
    """
    Entrenamiento manual sin `Trainer`.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.model.to(device)

    train_loader = DataLoader(
        tokenized_datasets["training"],
        batch_size=batch_size,
        shuffle=True,
        collate_fn=collate_fn_custom  # Usa la función personalizada
    )

    optimizer = AdamW(model.model.parameters(), lr=learning_rate)
    
    for epoch in range(epochs):
        print(f"Epoch {epoch+1}/{epochs}")
        model.model.train()
        total_loss = 0
        
        for step, batch in enumerate(train_loader):
            batch = {key: val.to(device) for key, val in batch.items()}
            optimizer.zero_grad()
            
            input_ids = batch["input_ids"]
            attention_mask = batch["attention_mask"]
            outputs = model.model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits  # Output sin procesar
            labels = batch["labels"]  # Esto puede ser un tensor de tamaño [2048]
            labels = labels.unsqueeze(0)
            print(labels.shape)
            print(logits.shape)

            logits = logits.view(-1, logits.size(-1))  # Aplana la secuencia [batch_size * seq_len, vocab_size]
            labels = labels.view(-1)  # Aplana las labels [batch_size * seq_len]

            # Calcula la pérdida con CrossEntropyLoss
            loss = F.cross_entropy(logits, labels, ignore_index=model.tokenizer.pad_token_id)
            loss = F.cross_entropy(logits.permute(0, 2, 1), labels, ignore_index=model.tokenizer.pad_token_id)

            loss.backward()

            # Gradiente clipping
            torch.nn.utils.clip_grad_norm_(model.model.parameters(), 1.0)

            # Optimizer step
            optimizer.step()

            total_loss += loss.item()

            if step % 50 == 0:
                print(f"Step {step}: Loss {loss.item()}")

        avg_loss = total_loss / len(train_loader)
        print(f"Epoch {epoch+1} completed. Average Loss: {avg_loss:.4f}")

    print("Training complete.")
    return model

def trainer_train(model,tokenized_datasets,model_type):
    # Configurar los argumentos de entrenamiento
    common_args = dict(
            output_dir= CHECKPOINT_MODEL_PATH,
            eval_strategy="epoch",
            logging_dir= LOG_DIR,            # Directorio de los registros
            logging_steps=10,     
            learning_rate=2e-5,
            per_device_train_batch_size=2,
            per_device_eval_batch_size=2,
            num_train_epochs=3,
            weight_decay=0.01,
            save_total_limit=2,
            save_steps=50,
            warmup_steps=100,

        )
    if model_type == "causal":
        training_args = TrainingArguments(**common_args,)
    else:
        training_args = Seq2SeqTrainingArguments(**common_args,
            predict_with_generate=True,                                    
        )
    trainer = Trainer(
    model=model.model,
    args=training_args,
    train_dataset=tokenized_datasets["training"],
    eval_dataset=tokenized_datasets["validation"])
    #convert model tu gpu
    model.model = model.model.to('cuda')
    model.model = torch.nn.DataParallel(model.model)
    # Habilitar la depuración en PyTorch
    torch.autograd.set_detect_anomaly(True)
    trainer.train()
    return model

  

def train(model,tokenized_datasets,MODEL_SELECTED,model_type):
    # if MODEL_SELECTED == "NUEXTRACT":
    #     return  traditional_train(model,tokenized_datasets)
    # else:
    return  trainer_train(model,tokenized_datasets, model_type)
