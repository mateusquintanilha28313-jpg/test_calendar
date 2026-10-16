# Calendário de Testes

A aplicação em `site/` é JavaScript estático para GitHub Pages e usa Supabase para partilhar contas e dados. O GitHub Pages não executa código de servidor nem fornece uma base de dados.

## Configuração

1. Crie um projeto no Supabase.
2. No SQL Editor do Supabase, execute [`supabase-schema.sql`](supabase-schema.sql).
3. Nas definições de autenticação do Supabase, escolha se os utilizadores têm de confirmar o email. Se a confirmação estiver ativa, cada pessoa terá de validar o endereço antes de iniciar sessão.
4. Copie o URL do projeto e a chave publicável/anon para [`site/supabase-config.js`](site/supabase-config.js). A chave anon pode estar no navegador; nunca coloque neste ficheiro uma chave `service_role`. As políticas RLS do SQL protegem os dados.
5. Envie o repositório para o GitHub. Em **Settings > Pages**, selecione **GitHub Actions** como origem de publicação. O workflow publica `site/`, incluindo o `CNAME` para `teoriadosnumeros.eu.org`.
6. Depois de obter o endereço Pages, adicione-o à lista de URLs de redirecionamento permitidos em **Authentication > URL Configuration** do Supabase.
7. No SQL Editor do Supabase, defina o código que dá acesso às contas de professor (mínimo 6 caracteres). Não guarde este código no repositório:

   ```sql
   insert into private.teacher_signup_code (code)
   values ('O-SEU-CODIGO')
   on conflict (id) do update set code = excluded.code, updated_at = now();
   ```

   Use o mesmo comando para mudar o código mais tarde. Pode guardá-lo num ficheiro `*.local.sql`, que o git ignora.
8. Abra o site publicado e crie a sua conta. Em **Criar conta**, escolha **Aluno** ou **Professor**. As contas de professor só são criadas se o código estiver correto; a verificação é feita na base de dados.
9. Os professores podem alterar os perfis das outras contas na aplicação.

## Testar localmente

```sh
python3 -m http.server 8000 --directory site
```

Abra `http://localhost:8000`. O site local usa o mesmo projeto Supabase do site publicado.

## Importar agendamentos atuais

Inicie sessão como professor, escolha **Importar JSON** e selecione o ficheiro legado `agendamentos.json`. A importação aceita os campos (`nome`, `ano`, `disciplina`, `data`, `nota`) e transfere-os para as tabelas partilhadas do Supabase. Se o campo `usuario` ou o nome do aluno corresponder a uma conta, o teste será associado a essa conta; caso contrário, fica associado ao professor que o importar. As palavras-passe antigas não são importadas; cada pessoa terá de criar uma conta.

A versão JavaScript mantém criação de conta e início de sessão, perfis de aluno/professor, gestão de utilizadores, registo e filtro de testes, atualização de notas e exportação CSV filtrada. A autenticação usa email e palavra-passe. O acesso à base de dados é limitado por conta e perfil com Row Level Security.