import { expect, test } from '@playwright/test'

test('protege a área autenticada', async ({ page }) => {
  await page.goto('/tarefas')
  await expect(page).toHaveURL(/\/login$/)
  await expect(page.getByRole('heading', { name: 'Bom ter você de volta' })).toBeVisible()
})

test('cadastro, login e logout com API real', async ({ page }) => {
  const email = `auth-${crypto.randomUUID()}@example.com`
  const password = 'Senha-segura-123'
  await page.goto('/cadastro')
  await page.getByLabel('E-mail', { exact: true }).fill(email)
  await page.getByLabel('Senha', { exact: true }).fill(password)
  await page.getByLabel('Confirmar senha').fill(password)
  await page.getByRole('button', { name: 'Criar conta' }).click()
  await expect(page.getByRole('status')).toContainText('Conta criada')
  await page.getByLabel('E-mail', { exact: true }).fill(email)
  await page.getByLabel('Senha', { exact: true }).fill(password)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page.getByRole('heading', { name: 'Sua conta' })).toBeVisible()
  await page.getByRole('button', { name: 'Sair' }).click()
  await expect(page).toHaveURL(/\/login$/)
})
