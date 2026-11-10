"""
NeuroMAS engine: state-swapping LoRA adapters, structure-aware (role-free) prompts,
section-routed inter-agent messages, shared-terminal-reward REINFORCE, and
progressive growth (NeuroMAS-3 -> -5 -> -7).

Per-task quantities (input formatting, answer format, generation length, reward)
are supplied through a Task object.
"""
import re, gc
import torch
import torch.optim as optim
from peft import LoraConfig, get_peft_model, TaskType
from tqdm import tqdm

import config
from llm import load_base, gen, gen_lp


# ----------------------------------------------------------------------
# State-swapping adapter manager
# ----------------------------------------------------------------------
class AM:
    def __init__(self, pm, n):
        self.pm = pm; self.states = []; self.cur = 0
        self.states.append(self._g())
        for _ in range(n - 1):
            for n_, p in self.pm.named_parameters():
                if 'lora_' in n_ and p.requires_grad:
                    if 'lora_A' in n_: torch.nn.init.kaiming_uniform_(p, a=5 ** 0.5)
                    elif 'lora_B' in n_: torch.nn.init.zeros_(p)
            self.states.append(self._g())

    def _g(self):
        return {n: p.data.clone() for n, p in self.pm.named_parameters() if p.requires_grad}

    def _l(self, s):
        for n, p in self.pm.named_parameters():
            if n in s: p.data.copy_(s[n])

    def sw(self, i):
        if i != self.cur:
            self.states[self.cur] = self._g(); self._l(self.states[i]); self.cur = i

    def save(self):
        self.states[self.cur] = self._g()
        return [{k: v.clone().cpu() for k, v in s.items()} for s in self.states]

    def load(self, saved, dev):
        for i, s in enumerate(saved):
            self.states[i] = {k: v.to(dev) for k, v in s.items()}
        self._l(self.states[0]); self.cur = 0

    def get_state(self, i):
        if i == self.cur: return self._g()
        return {k: v.clone() for k, v in self.states[i].items()}


def grow_2_to_4(): return {0: 0, 1: 2, 2: 4}
def grow_4_to_6(): return {0: 0, 1: 1, 2: 2, 3: 3, 4: 6}


def init_grown_am(pm, n_new, old_am, mapping, device):
    new_am = AM(pm, n_new)
    for old_idx, new_idx in mapping.items():
        new_am.states[new_idx] = {k: v.to(device) for k, v in old_am.get_state(old_idx).items()}
    new_am._l(new_am.states[0]); new_am.cur = 0
    return new_am


def node_idx_to_layer_pos(nidx, topo):
    cum = 0
    for l, w in enumerate(topo):
        if nidx < cum + w: return l, nidx - cum
        cum += w
    raise ValueError(f"nidx {nidx} out of range for topo {topo}")


# ----------------------------------------------------------------------
# Section routing + structure-aware role-free prompts
# ----------------------------------------------------------------------
SECTION_RE = re.compile(r'TO\s*#\s*(\d+)\s*[:\uff1a]', re.IGNORECASE)


def parse_sections(text, num_recipients, sec_max_chars=config.SEC_MAX_CHARS):
    matches = list(SECTION_RE.finditer(text))
    if not matches:
        fb = text.strip()[:sec_max_chars] if text.strip() else "(empty)"
        return [fb] * num_recipients, False
    sections = [None] * num_recipients
    for i, m in enumerate(matches):
        pos = int(m.group(1)) - 1
        if not (0 <= pos < num_recipients): continue
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        if sections[pos] is None:
            sections[pos] = text[start:end].strip()[:sec_max_chars]
    fb = text.strip()[:sec_max_chars] if text.strip() else "(empty)"
    for i in range(num_recipients):
        if sections[i] is None:
            sections[i] = fb
    return sections, True


def _final_instruction(task, q):
    if task.kind == "code":
        return f"\nProvide the function body:\n{q}"
    return f"\n{task.answer_format}"


def node_prompt(task, topo, layer, node, q, incoming):
    nl = len(topo); total = sum(topo)
    h = (f"[Network: {nl}-layer {'-'.join(map(str, topo))}, {total} nodes | "
         f"Layer {layer + 1}/{nl}, Position {node + 1}/{topo[layer]}]")
    parts = [h, f"\nPROBLEM:\n{q}"]
    if incoming:
        prev = "\n".join([f"[from L{fl + 1}P{fp + 1}]: {msg}" for fl, fp, msg in incoming])
        parts.append(f"\nPREVIOUS:\n{prev}")
    if layer == nl - 1:
        parts.append(_final_instruction(task, q))
    else:
        nxt = topo[layer + 1]
        fmt = "\n".join([f"TO #{k + 1}: <message for downstream node {k + 1}>" for k in range(nxt)])
        parts.append(f"\nWrite a private message to each downstream node:\n{fmt}")
    return "\n".join(parts)


def sum_prompt(task, topo, q, all_text):
    nl = len(topo); total = sum(topo)
    h = f"[Summarizer | Network: {nl}-layer {'-'.join(map(str, topo))}, {total} nodes]"
    return f"{h}\n\nPROBLEM:\n{q}\n\nALL OUTPUTS:\n{all_text}{_final_instruction(task, q)}"


def _tok(task):
    if task.kind == "code":
        return config.TOK_CODE_INNER, config.TOK_CODE_OUTER
    return config.TOK_MCQ_INNER, config.TOK_MCQ_OUTER


# ----------------------------------------------------------------------
# Forward / train / eval
# ----------------------------------------------------------------------
def fwd(task, topo, pm, tok, am, q, device, lp=True, frozen_nodes=None):
    if frozen_nodes is None: frozen_nodes = set()
    n_nodes = sum(topo); sum_idx = n_nodes; n_layers = len(topo)
    tin, tout = _tok(task)
    layer_outputs = []; all_out = []
    nidx = 0
    for layer in range(n_layers):
        is_last = (layer == n_layers - 1)
        cur_layer = []
        for node in range(topo[layer]):
            incoming = []
            if layer > 0:
                for prev in layer_outputs[layer - 1]:
                    fl, fp = node_idx_to_layer_pos(prev['nidx'], topo)
                    secs = prev['sections']
                    if secs and node < len(secs):
                        incoming.append((fl, fp, secs[node]))
            am.sw(nidx); pm.train() if lp else pm.eval()
            prompt = node_prompt(task, topo, layer, node, q, incoming)
            mt = tout if is_last else tin
            if lp and nidx not in frozen_nodes:
                t, lp_ = gen_lp(pm, tok, prompt, device, mt=mt)
            else:
                t = gen(pm, tok, prompt, device, mt=mt); lp_ = None
            sections, _ = (parse_sections(t, topo[layer + 1]) if not is_last else (None, False))
            cur_layer.append({'nidx': nidx, 'text': t, 'lp': lp_, 'sections': sections})
            all_out.append((nidx, t, lp_))
            nidx += 1
        layer_outputs.append(cur_layer)
    all_text = "\n".join([f"[N{nid + 1}]: {t[:250]}" for nid, t, _ in all_out])
    am.sw(sum_idx); pm.train() if lp else pm.eval()
    sp = sum_prompt(task, topo, q, all_text)
    if lp:
        st, slp = gen_lp(pm, tok, sp, device, mt=tout)
    else:
        st = gen(pm, tok, sp, device, mt=tout); slp = None
    return all_out, st, slp


def train_stage(task, topo, pm, tok, am, tr, dev, device, rl_steps, frozen_nodes=None, label=""):
    n_nodes = sum(topo); sum_idx = n_nodes
    params = [p for p in pm.parameters() if p.requires_grad]
    opt = optim.AdamW(params, lr=config.LR)
    baselines = [0.0] * (n_nodes + 1); rewards = []
    if frozen_nodes is None: frozen_nodes = set()
    best_dev = -1.0; best_states = None
    dev_set = dev[:config.DEV_EVAL_N]
    for step in tqdm(range(rl_steps), desc=f"RL {label}"):
        torch.cuda.empty_cache()
        ex = tr[step % len(tr)]
        all_out, st, slp = fwd(task, topo, pm, tok, am, task.input_text(ex), device,
                               lp=True, frozen_nodes=frozen_nodes)
        r = 1.0 if task.score(st, ex) else 0.0
        rewards.append(r)
        baselines[sum_idx] = config.EMA_DECAY * baselines[sum_idx] + (1 - config.EMA_DECAY) * r
        if slp is not None and len(slp) > 0:
            am.sw(sum_idx)
            loss = -(slp.mean() * (r - baselines[sum_idx]))
            if not torch.isnan(loss):
                opt.zero_grad(); loss.backward()
                torch.nn.utils.clip_grad_norm_(params, config.GRAD_CLIP); opt.step()
        for nidx, _, lp in all_out:
            baselines[nidx] = config.EMA_DECAY * baselines[nidx] + (1 - config.EMA_DECAY) * r
            if nidx in frozen_nodes:
                continue
            if lp is not None and len(lp) > 0:
                am.sw(nidx)
                loss = -(lp.mean() * (r - baselines[nidx]))
                if not torch.isnan(loss):
                    opt.zero_grad(); loss.backward()
                    torch.nn.utils.clip_grad_norm_(params, config.GRAD_CLIP); opt.step()
        if (step + 1) % config.CKPT_EVERY == 0:
            c = sum(1 for de in dev_set
                    if task.score(fwd(task, topo, pm, tok, am, task.input_text(de), device,
                                      lp=False, frozen_nodes=frozen_nodes)[1], de))
            dev_acc = c / max(1, len(dev_set))
            if dev_acc > best_dev:
                best_dev = dev_acc; best_states = am.save()
    if best_states is not None:
        am.load(best_states, device)
    return am


def eval_net(task, topo, pm, tok, am, ev, device):
    c = 0
    for ex in tqdm(ev, desc=f"Eval {task.name} {sum(topo)+1}ag"):
        _, st, _ = fwd(task, topo, pm, tok, am, task.input_text(ex), device, lp=False)
        if task.score(st, ex):
            c += 1
    return c / len(ev)


def _peft(base):
    return get_peft_model(base, LoraConfig(
        task_type=TaskType.CAUSAL_LM, r=config.LORA_RANK, lora_alpha=config.LORA_ALPHA,
        lora_dropout=config.LORA_DROPOUT, target_modules=config.LORA_TARGETS, bias="none"))


def run_neuromas(task, device, up_to=7):
    """Progressive growth. Returns {'neuromas3':acc, 'neuromas5':acc, 'neuromas7':acc}
    for the stages requested by up_to (3, 5, or 7)."""
    s1, s2, s3 = config.STEPS_NEUROMAS
    tr, dev, ev = task.load()
    out = {}

    # Phase 1: NeuroMAS-3 (LNet-2 [1,1])
    base, tok = load_base(device); pm = _peft(base)
    am = AM(pm, 3)
    am = train_stage(task, [1, 1], pm, tok, am, tr, dev, device, s1, label="NeuroMAS-3")
    out['neuromas3'] = eval_net(task, [1, 1], pm, tok, am, ev, device)
    saved = am.save()
    if up_to <= 3:
        del pm; gc.collect(); torch.cuda.empty_cache(); return out

    # Phase 2: grow to NeuroMAS-5 (LNet-4 [2,2]); freeze copied prior-stage nodes {0,2}
    del pm; gc.collect(); torch.cuda.empty_cache()
    base, tok = load_base(device); pm = _peft(base)
    am_r = AM(pm, 3); am_r.load(saved, device)
    am = init_grown_am(pm, 5, am_r, grow_2_to_4(), device)
    am = train_stage(task, [2, 2], pm, tok, am, tr, dev, device, s2,
                     frozen_nodes={0, 2}, label="NeuroMAS-5")
    out['neuromas5'] = eval_net(task, [2, 2], pm, tok, am, ev, device)
    saved = am.save()
    if up_to <= 5:
        del pm; gc.collect(); torch.cuda.empty_cache(); return out

    # Phase 3: grow to NeuroMAS-7 (LNet-6 [2,2,2]); freeze {0,1}
    del pm; gc.collect(); torch.cuda.empty_cache()
    base, tok = load_base(device); pm = _peft(base)
    am_r = AM(pm, 5); am_r.load(saved, device)
    am = init_grown_am(pm, 7, am_r, grow_4_to_6(), device)
    am = train_stage(task, [2, 2, 2], pm, tok, am, tr, dev, device, s3,
                     frozen_nodes={0, 1}, label="NeuroMAS-7")
    out['neuromas7'] = eval_net(task, [2, 2, 2], pm, tok, am, ev, device)
    del pm; gc.collect(); torch.cuda.empty_cache()
    return out
