# Edição de Natal — Teoria dos Números

## Objetivo

Aplicar ao Calendário de Testes uma identidade visual natalícia elegante e responsiva, mantendo os fluxos existentes de autenticação, registo e gestão de testes.

## Direção visual

- Verde-escuro `#123F35` como cor principal, vermelho `#A83232` para destaques, dourado `#D4AF62` para detalhes e creme `#FAF9F4` nos fundos; verde-claro em acentos discretos.
- Preservar o logótipo, o nome Teoria dos Números e a disposição funcional dos controlos existentes.
- Acrescentar ao cabeçalho autenticado uma grinalda subtil e a mensagem «Feliz Natal!».
- No ecrã de acesso, colocar uma árvore de Natal minimalista acima do título e usar detalhes dourados na caixa.
- Aplicar detalhes natalícios discretos aos painéis, cartões, datas, filtros e ações do calendário, sem alterar os seus controlos ou identificadores.
- Adicionar neve subtil às vistas de login e da aplicação, e um brilho dourado discreto. A decoração não deve captar eventos nem competir com o conteúdo.
- Respeitar `prefers-reduced-motion` e manter os pontos de quebra responsivos existentes.

## Implementação

Limitar as alterações a `site/index.html` e `site/styles.css`. Usar HTML e CSS existentes, sem dependências externas, JavaScript de animação ou novos assets. Os elementos puramente decorativos serão ocultados de tecnologias de apoio.

## Comportamento e dados preservados

Não alterar `site/app.js`, `site/supabase-config.js`, `supabase-schema.sql`, autenticação, registo, permissões, filtros, pesquisa, notas, calendário, operações de importação/exportação ou dados existentes.

## Validação

- Verificar a página de acesso em desktop e telemóvel.
- Confirmar que os controlos e identificadores do HTML usados por `site/app.js` continuam presentes.
- Validar a sintaxe do JavaScript existente e inspecionar a apresentação da vista autenticada sem alterar dados ou credenciais.
- Confirmar que as animações são reduzidas/desativadas com `prefers-reduced-motion`.
