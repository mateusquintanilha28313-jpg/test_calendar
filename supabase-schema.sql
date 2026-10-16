create table if not exists public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  username text not null check (char_length(username) between 2 and 40),
  role text not null default 'aluno' check (role in ('aluno', 'professor')),
  created_at timestamptz not null default now()
);

create unique index if not exists profiles_username_lower_unique
  on public.profiles (lower(username));

create table if not exists public.tests (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  name text not null,
  school_year text not null,
  subject text not null,
  test_date date not null,
  grade numeric(4, 1) check (grade is null or grade between 0 and 20),
  created_at timestamptz not null default now()
);

create or replace function public.current_user_is_professor()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1 from public.profiles
    where id = auth.uid() and role = 'professor'
  );
$$;

create schema if not exists private;
revoke all on schema private from public, anon, authenticated;

create table if not exists private.teacher_signup_code (
  id boolean primary key default true check (id),
  code text not null check (char_length(code) >= 6),
  updated_at timestamptz not null default now()
);

revoke all on private.teacher_signup_code from public, anon, authenticated;

create or replace function public.create_profile_for_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  requested_role text := coalesce(new.raw_user_meta_data ->> 'account_type', 'aluno');
  provided_code text := nullif(trim(new.raw_user_meta_data ->> 'teacher_code'), '');
  new_role text := 'aluno';
begin
  if requested_role = 'professor' then
    if provided_code is null or not exists (
      select 1 from private.teacher_signup_code where code = provided_code
    ) then
      raise exception 'invalid_teacher_code' using errcode = 'P0001';
    end if;
    new_role := 'professor';
  end if;

  insert into public.profiles (id, username, role)
  values (
    new.id,
    coalesce(nullif(trim(new.raw_user_meta_data ->> 'username'), ''), split_part(new.email, '@', 1)),
    new_role
  );

  update auth.users
  set raw_user_meta_data = raw_user_meta_data - 'teacher_code'
  where id = new.id;

  return new;
end;
$$;

drop trigger if exists on_auth_user_created_profile on auth.users;
create trigger on_auth_user_created_profile
  after insert on auth.users
  for each row execute procedure public.create_profile_for_new_user();

alter table public.profiles enable row level security;
alter table public.tests enable row level security;

drop policy if exists "Read own profile or professor reads all" on public.profiles;
create policy "Read own profile or professor reads all"
  on public.profiles for select to authenticated
  using (id = (select auth.uid()) or (select public.current_user_is_professor()));

drop policy if exists "Professor manages roles" on public.profiles;
create policy "Professor manages roles"
  on public.profiles for update to authenticated
  using ((select public.current_user_is_professor()))
  with check ((select public.current_user_is_professor()));

drop policy if exists "Users read own tests and professors read all" on public.tests;
create policy "Users read own tests and professors read all"
  on public.tests for select to authenticated
  using (user_id = (select auth.uid()) or (select public.current_user_is_professor()));

drop policy if exists "Users create own tests" on public.tests;
create policy "Users create own tests"
  on public.tests for insert to authenticated
  with check (user_id = (select auth.uid()) or (select public.current_user_is_professor()));

drop policy if exists "Users and professors update permitted tests" on public.tests;
create policy "Users and professors update permitted tests"
  on public.tests for update to authenticated
  using (user_id = (select auth.uid()) or (select public.current_user_is_professor()))
  with check (user_id = (select auth.uid()) or (select public.current_user_is_professor()));

drop policy if exists "Professors delete tests" on public.tests;
create policy "Professors delete tests"
  on public.tests for delete to authenticated
  using ((select public.current_user_is_professor()));

revoke all on public.profiles from anon, authenticated;
grant select on public.profiles to authenticated;
grant update (role) on public.profiles to authenticated;

revoke all on public.tests from anon, authenticated;
grant select, insert, delete on public.tests to authenticated;
grant update (grade) on public.tests to authenticated;

revoke all on function public.current_user_is_professor() from public;
grant execute on function public.current_user_is_professor() to authenticated;
revoke all on function public.create_profile_for_new_user() from public, anon, authenticated;