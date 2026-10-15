/** Limites alinhados ao banco SQLite e aos schemas Pydantic da API. */
export const LIMITS = {
  NAME: 100,
  EMAIL: 254,
  PASSWORD_MIN: 8,
  PASSWORD_MAX: 128,
  /** Senha atual na troca: a API aceita a partir de 1 caractere. */
  CURRENT_PASSWORD_MIN: 1,
  TITLE: 200,
  DESCRIPTION: 10_000,
  TAG: 40,
  TAGS_MAX: 10,
  SEARCH: 200,
} as const

/** Texto livre de tags: N tags de até TAG chars + separadores ", ". */
export const TAGS_TEXT_MAX =
  LIMITS.TAG * LIMITS.TAGS_MAX + Math.max(0, LIMITS.TAGS_MAX - 1) * 2
