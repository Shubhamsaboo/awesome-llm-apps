"""
LLM primitives: model loading, greedy generation, and per-token log-probs for
REINFORCE. Single frozen backbone, fp16, greedy decoding.
"""
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

from config import MODEL_NAME


def load_base(device):
    tok = AutoTokenizer.from_pretrained(MODEL_NAME)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    m = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME, torch_dtype=torch.float16, device_map=device)
    return m, tok


def gen(model, tok, prompt, device, mt):
    """Greedy generation; returns decoded continuation."""
    inp = tok(prompt, return_tensors="pt", truncation=True, max_length=2048).to(device)
    il = inp.input_ids.shape[1]
    with torch.no_grad():
        out = model.generate(**inp, max_new_tokens=mt, do_sample=False,
                             pad_token_id=tok.pad_token_id)
    return tok.decode(out[0][il:], skip_special_tokens=True)


def gen_lp(model, tok, prompt, device, mt):
    """Greedy generation + per-token log-probs of the produced tokens (for REINFORCE)."""
    inp = tok(prompt, return_tensors="pt", truncation=True, max_length=2048).to(device)
    il = inp.input_ids.shape[1]
    with torch.no_grad():
        out = model.generate(**inp, max_new_tokens=mt, do_sample=False,
                             pad_token_id=tok.pad_token_id)
    gids = out[0][il:]
    text = tok.decode(gids, skip_special_tokens=True)
    with torch.amp.autocast('cuda'):
        mo = model(out[0].unsqueeze(0)); logits = mo.logits
    lps = []
    for i, tid in enumerate(gids):
        log_probs = torch.log_softmax(logits[0, il + i - 1, :], dim=-1)
        lps.append(log_probs[tid])
    del mo, logits
    return text, (torch.stack(lps) if lps else torch.tensor([]))
