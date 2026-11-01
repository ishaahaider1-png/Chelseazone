-- One level of replies on discussion comments.
--
-- The frontend (index.html, Discuss panel) already renders and posts replies,
-- but it degrades to a reply-less thread list until this migration has run:
-- it probes for comments.parent_id on load and hides the Reply controls if the
-- column is absent, so the panel is never broken, just reduced. Running this
-- turns replies on with no frontend change.
--
-- Safe to re-run.

begin;

alter table public.comments
  add column if not exists parent_id uuid
    references public.comments (id) on delete cascade;

-- Every page load groups replies by parent, so this is the one index that matters.
create index if not exists comments_parent_id_idx
  on public.comments (parent_id);

-- Keep threads exactly one level deep. The UI always posts a reply against the
-- top-level comment, so this is a backstop rather than the main mechanism: if
-- anything ever aims a reply at another reply, it is re-pointed at that reply's
-- parent instead of creating a second level the renderer cannot draw.
--
-- security definer so the lookup is not filtered by the row-level policy of
-- whoever happens to be inserting; without it the parent row could read back as
-- invisible and the flattening would silently not apply.
create or replace function public.flatten_comment_parent()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  grandparent uuid;
begin
  if new.parent_id is null then
    return new;
  end if;

  if new.parent_id = new.id then          -- a comment cannot be its own parent
    new.parent_id := null;
    return new;
  end if;

  select c.parent_id into grandparent
    from public.comments c
   where c.id = new.parent_id;

  if grandparent is not null then
    new.parent_id := grandparent;
  end if;

  return new;
end;
$$;

drop trigger if exists comments_flatten_parent on public.comments;
create trigger comments_flatten_parent
  before insert or update of parent_id on public.comments
  for each row execute function public.flatten_comment_parent();

commit;
