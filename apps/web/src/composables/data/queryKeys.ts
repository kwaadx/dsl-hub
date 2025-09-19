type KeyAtom = string | number | boolean | null | undefined;
type KeyScope =
  | readonly KeyAtom[]
  | readonly [Record<string, KeyAtom>];

export type EntityKeys<E extends string> = {
  base: (...scope: KeyScope) => readonly [E, ...KeyScope];
  list: (...scope: KeyScope) => readonly [E, ...KeyScope, 'list'];
  detail: (id: KeyAtom, ...scope: KeyScope) => readonly [E, ...KeyScope, 'detail', KeyAtom];
  paged: (
    page: number,
    pageSize?: number,
    params?: Record<string, KeyAtom>,
    ...scope: KeyScope
  ) => readonly [E, ...KeyScope, 'paged', Readonly<{
    page: number;
    pageSize: number | undefined
  } & Record<string, KeyAtom>>];
};

export function makeEntityKeys<E extends string>(entity: E): EntityKeys<E> {
  return {
    base: (...scope) => [entity, ...scope] as const,
    list: (...scope) => [entity, ...scope, 'list'] as const,
    detail: (id, ...scope) => [entity, ...scope, 'detail', id] as const,
    paged: (page, pageSize, params = {}, ...scope) =>
      [entity, ...scope, 'paged', {page, pageSize, ...params}] as const,
  };
}

export function makeQK<const Entities extends readonly string[]>(
  entities: Entities
): { [K in Entities[number]]: EntityKeys<K> } {
  return entities.reduce((acc, name) => {
    acc[name] = makeEntityKeys(name);
    return acc;
  }, {} as any);
}

export const qk = makeQK(['flows'] as const);
