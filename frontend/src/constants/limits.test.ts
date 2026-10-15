import { describe, expect, it } from 'vitest'
import { LIMITS, TAGS_TEXT_MAX } from './limits'

describe('LIMITS', () => {
  it('reflete os limites da API e do banco', () => {
    expect(LIMITS).toMatchObject({
      NAME: 100,
      EMAIL: 254,
      PASSWORD_MIN: 8,
      PASSWORD_MAX: 128,
      CURRENT_PASSWORD_MIN: 1,
      TITLE: 200,
      DESCRIPTION: 10_000,
      TAG: 40,
      TAGS_MAX: 10,
      SEARCH: 200,
    })
    expect(TAGS_TEXT_MAX).toBe(418)
  })
})
