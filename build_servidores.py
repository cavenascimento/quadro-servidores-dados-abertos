"""Painel de movimentação do quadro de servidores (dados abertos do Governo Federal).
Uso: python build_servidores.py PASTA_COM_OS_CSV saida.html logo.png
Remove nome, CPF e matrícula antes de qualquer agregação."""
import sys, glob, io, json, hashlib, re, base64
import pandas as pd

src, out, logo = sys.argv[1], sys.argv[2], sys.argv[3]
COLS = ['mes','nome','siape','cpf','sexo','cor','pcd','sit','forma','dt_ing','cargo','nivel','classe','padrao','funcao','dt_func','ativ','org_o','org_r','uf','uorg']
MES = ['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez']
lab = lambda ym: f"{MES[int(ym[4:]) - 1]}/{ym[2:4]}"

def ler(f):
    b = open(f, 'rb').read()
    for e in ('utf-8', 'cp1252', 'latin-1'):          # os meses vêm com codificações diferentes
        try: b.decode(e); break
        except UnicodeDecodeError: pass
    d = pd.read_csv(io.BytesIO(b), sep=';', encoding=e, dtype=str); d.columns = COLS   # colunas por posição, evita acentos quebrados
    d['key'] = (d.nome.str.strip() + '|' + d.cpf).map(lambda s: hashlib.sha256(s.encode()).hexdigest()[:12])  # chave anônima
    d['cargo'] = d.cargo.fillna('Sem cargo efetivo').str.strip().str.title().str.replace(r'\b(Do|De|Em|Da)\b', lambda m: m.group(1).lower(), regex=True).replace({'Sem Cargo Efetivo': 'Sem cargo efetivo'})
    d['sit'] = d.sit.str.replace(r'\s+', ' ', regex=True).str.strip().str.capitalize().replace({'Estagiario sigepe': 'Estagiário (SIGEPE)', 'Exerc. 7 art93 8112': 'Exercício art. 93 (Lei 8.112)'})
    d['tem_funcao'] = d.funcao.notna(); d['ing_0124'] = d.dt_ing == '01/01/2024'
    return d[['key','sexo','sit','cargo','uf','tem_funcao','ing_0124']].copy(), d.mes.iloc[0], e, int(d.duplicated(['nome','cpf']).sum())

D, ENC, DUP = {}, {}, 0
for f in sorted(glob.glob(src + '/RelaodeServidores*.csv')):
    d, ym, e, dp = ler(f); D[ym] = d.set_index('key'); ENC[lab(ym)] = e; DUP += dp
ms = sorted(D); last = D[ms[-1]]
TOP = list(last.cargo.value_counts().head(6).index)
gc = lambda c: c if c in TOP or c == 'Sem cargo efetivo' else 'Demais cargos'

def agg(S, E, base):
    def tab(col, fn=lambda x: x):
        s = S[col].map(fn).value_counts(); e = E[col].map(fn).value_counts()
        return pd.DataFrame({'s': s, 'e': e}).fillna(0).astype(int)
    c = tab('cargo', gc).sort_values('s', ascending=False)
    u = tab('uf'); u['t'] = u.s + u.e
    pq = u[u.t < 5]; u = u[u.t >= 5].sort_values('t', ascending=False)
    if len(u) > 10: pq = pd.concat([pq, u.iloc[10:]]); u = u.iloc[:10]
    rows = [[i, int(r.s), int(r.e)] for i, r in u.iterrows()]
    if len(pq): rows.append(['Demais UFs', int(pq.s.sum()), int(pq.e.sum())])
    st = S.sit.value_counts(); sit = [[i, int(v)] for i, v in st.head(5).items()]
    if len(st) > 5: sit.append(['Demais situações', int(st.iloc[5:].sum())])
    return dict(s=len(S), e=len(E), cargo=[[i, int(r.s), int(r.e)] for i, r in c.iterrows()], uf=rows, sit=sit)

hc = [len(D[m]) for m in ms]; trans = []; allS = []; allE = []; reent = 0
for i in range(len(ms) - 1):
    a, b = D[ms[i]], D[ms[i + 1]]
    S = a.loc[a.index.difference(b.index)]; E = b.loc[b.index.difference(a.index)]
    if i: ant = set().union(*[set(D[m].index) for m in ms[:i]]); reent += sum(k in ant for k in E.index)
    p = agg(S, E, a); p.update(label=f"{lab(ms[i])} a {lab(ms[i+1])}", short=f"{lab(ms[i])[:3]}→{lab(ms[i+1])[:3]}", den=len(a), hs=len(a), he=len(b))
    trans.append(p); allS.append(S); allE.append(E)
tot = agg(pd.concat(allS), pd.concat(allE), None); tot.update(label='Todo o período', den=sum(hc[:-1]), hs=hc[0], he=hc[-1])
def pf(col, n):
    v = last[col].value_counts(); r = [[i, int(x)] for i, x in v.head(n).items()]
    if len(v) > n: r.append(['Demais', int(v.iloc[n:].sum())])
    return r
perfil = dict(cargo=pf('cargo', 7), uf=pf('uf', 9), sexo=pf('sexo', 2), funcao=round(float(last.tem_funcao.mean()) * 100, 1),
              perm=round(float((last.sit == 'Ativo permanente').mean()) * 100, 1))
q = dict(enc=ENC, dup=DUP, unicos=len(set().union(*[set(D[m].index) for m in ms])), ing=round(float(pd.concat(D.values()).ing_0124.mean()) * 100),
         sem_cargo=round(float((last.cargo == 'Sem cargo efetivo').mean()) * 100), reent=reent)
data = dict(months=[lab(m) for m in ms], hc=hc, S=[t['s'] for t in trans], E=[t['e'] for t in trans], P=[tot] + trans, perfil=perfil, q=q)

# tabelas agregadas, sem dados pessoais, para o repositório
pd.DataFrame(dict(mes=[lab(m) for m in ms], servidores=hc, entradas=[None] + data['E'], saidas=[None] + data['S'])).to_csv('movimentacao_mensal.csv', index=False)
pd.concat([D[m].assign(mes=lab(m)).groupby(['mes', 'uf']).size().rename('servidores').reset_index() for m in ms]).to_csv('quadro_mensal_uf.csv', index=False)

from PIL import Image
im = Image.open(logo).convert('RGB'); im.thumbnail((192, 192)); bf = io.BytesIO(); im.save(bf, 'JPEG', quality=88)
logo64 = 'data:image/jpeg;base64,' + base64.b64encode(bf.getvalue()).decode()
html = open('template_servidores.html', encoding='utf-8').read().replace('__DATA__', json.dumps(data, ensure_ascii=False, separators=(',', ':'))).replace('__LOGO__', logo64)
open(out, 'w', encoding='utf-8').write(html); print('ok', len(html), q, hc, data['S'], data['E'])
