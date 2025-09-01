# api_test_qwen.py
import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct"
# allow MPS fallback for unsupported ops (helps on older macOS / torch)
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

def pick_device():
    if torch.backends.mps.is_available():
        return "mps", torch.float16
    # CPU fallback (slow but works)
    return "cpu", torch.float32

device, dtype = pick_device()

# --- Load ---
tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(
    MODEL,
    torch_dtype=dtype,
    # NOTE: don't pass device_map when you also .to(device)
    low_cpu_mem_usage=True
).to(device)

# make sure we have stopping/ padding set (Qwen works with eos as pad)
eos_id = tokenizer.eos_token_id
pad_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else eos_id

system = "You are a helpful assistant."
history = []

def chat_once(user_text: str) -> str:
    # Use the model's chat template (safer than manual string concat)
    messages = [{"role": "system", "content": system}]
    for u, a in history:
        messages.append({"role": "user", "content": u})
        messages.append({"role": "assistant", "content": a})
    messages.append({"role": "user", "content": user_text})

    prompt = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=False
    )

    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=256,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            eos_token_id=eos_id,
            pad_token_id=pad_id
        )

    text = tokenizer.decode(out[0], skip_special_tokens=True)
    # robust split: take the last assistant turn if present
    if "assistant" in text.lower():
        parts = text.rsplit("assistant", 1)
        reply = parts[-1].lstrip(": ").strip()
    else:
        reply = text.strip()

    history.append((user_text, reply))
    return reply

if __name__ == "__main__":
    while True:
        try:
            msg = input("You: ")
            if msg.strip().lower() in {"exit", "quit"}:
                break
            print("Assistant:", chat_once(msg))
        except (EOFError, KeyboardInterrupt):
            break
