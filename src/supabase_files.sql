-- 「ファイル」画面用：Supabase の SQL Editor で 1 回だけ実行する
-- 非公開バケット files を作り、各ユーザーは自分の ID のフォルダだけ読み書きできるようにする

insert into storage.buckets (id, name, public, file_size_limit)
values ('files', 'files', false, 52428800)
on conflict (id) do nothing;

create policy "files: read own"   on storage.objects for select to authenticated
  using      (bucket_id = 'files' and (storage.foldername(name))[1] = auth.uid()::text);
create policy "files: insert own" on storage.objects for insert to authenticated
  with check (bucket_id = 'files' and (storage.foldername(name))[1] = auth.uid()::text);
create policy "files: update own" on storage.objects for update to authenticated
  using      (bucket_id = 'files' and (storage.foldername(name))[1] = auth.uid()::text);
create policy "files: delete own" on storage.objects for delete to authenticated
  using      (bucket_id = 'files' and (storage.foldername(name))[1] = auth.uid()::text);
