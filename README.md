# Calendário de Testes

A aplicação em `site/` é JavaScript estático para GitHub Pages e usa Supabase para partilhar contas e dados. O GitHub Pages não executa código de servidor nem fornece uma base de dados.

## Configuração

1. Crie um projeto no Supabase.
2. No SQL Editor do Supabase, execute [`supabase-schema.sql`](supabase-schema.sql).
3. Nas definições de autenticação do Supabase, escolha se os utilizadores têm de confirmar o email. Se a confirmação estiver ativa, cada pessoa terá de validar o endereço antes de iniciar sessão.
4. Copie o URL do projeto e a chave publicável/anon para [`site/supabase-config.js`](site/supabase-config.js). A chave anon pode estar no navegador; nunca coloque neste ficheiro uma chave `service_role`. As políticas RLS do SQL protegem os dados.
5. Envie o repositório para o GitHub. Em **Settings > Pages**, selecione **GitHub Actions** como origem de publicação. O workflow publica `site/`, incluindo o `CNAME` para `teoriadosnumeros.eu.org`.
6. Depois de obter o endereço Pages, adicione-o à lista de URLs de redirecionamento permitidos em **Authentication > URL Configuration** do Supabase.
7. Abra o site publicado e crie a sua conta. As novas contas começam com o perfil de aluno.
8. No SQL Editor do Supabase, promova a primeira conta a professor, substituindo o email no comando abaixo:

   ```sql
   update public.profiles
   set role = 'professor'
   where id = (select id from auth.users where email = 'professor@example.com');
   ```

   Depois disso, os professores podem alterar os perfis das outras contas na aplicação.

## Importar agendamentos atuais

Inicie sessão como professor, escolha **Importar JSON** e selecione o ficheiro legado `agendamentos.json`. A importação aceita os campos (`nome`, `ano`, `disciplina`, `data`, `nota`) e transfere-os para as tabelas partilhadas do Supabase. Se o campo `usuario` ou o nome do aluno corresponder a uma conta, o teste será associado a essa conta; caso contrário, fica associado ao professor que o importar. As palavras-passe antigas não são importadas; cada pessoa terá de criar uma conta.

A versão JavaScript mantém criação de conta e início de sessão, perfis de aluno/professor, gestão de utilizadores, registo e filtro de testes, atualização de notas e exportação CSV filtrada. A autenticação usa email e palavra-passe. O acesso à base de dados é limitado por conta e perfil com Row Level Security.