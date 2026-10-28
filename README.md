# quadro-servidores-dados-abertos
Painel interativo que mostra como o quadro de servidores mudou mês a mês entre dez/2024 e mai/2025, a partir de seis arquivos de dados abertos do Governo Federal.

O que fiz:
• Leitura e padronização de 6 arquivos mensais em Python (pandas), com tratamento de codificações diferentes entre os meses
• Remoção de nome, CPF e matrícula antes de qualquer análise, e comparação entre meses por chave anônima, com atenção à LGPD
• Cálculo de entradas, saídas e variação do quadro por período, cargo, estado e situação funcional
• Painel com filtro de período, gráficos clicáveis, modos de visualização e tema claro e escuro

Principais achados:
• O quadro passou de 5.346 para 5.267 servidores (−79, ou −1,5%)
• Foram 145 saídas e 66 entradas no período, e as saídas diminuíram ao longo dos meses (39 em dez a jan, 19 em abr a mai)
• Parte relevante da movimentação é de vínculos temporários: das 145 saídas, 66 eram de pessoas sem cargo efetivo e 30 de estagiários

Cuidados metodológicos:
• "Saída" significa apenas que a pessoa deixou de constar na base entre dois meses. A base não informa o motivo, por isso o painel não fala em demissões
• A data de ingresso foi ignorada: cerca de 96% aparecem como 01/01/2024, provavelmente por reestruturação administrativa
• O período é de apenas seis meses, então não indica tendência de longo prazo

Ferramentas: Python (pandas), HTML/CSS/JavaScript, GitHub Pages e IA generativa (Claude) como apoio na construção.
