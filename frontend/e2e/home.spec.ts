import { expect, test } from '@playwright/test'

test('carrega a página inicial compilada sem erros de execução', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))

  const response = await page.goto('/')

  expect(response?.status()).toBe(200)
  await expect(page).toHaveTitle('TaskFlow')
  await expect(page.getByRole('heading', { level: 1 })).toHaveText(
    'Organize o trabalho. Simplifique o dia.',
  )
  await expect(page.getByRole('main')).toContainText('próximas etapas')
  const fitsViewport = await page.evaluate(
    () => document.documentElement.scrollWidth <= window.innerWidth,
  )
  expect(fitsViewport).toBe(true)
  expect(errors).toEqual([])
})
