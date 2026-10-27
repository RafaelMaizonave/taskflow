import { expect, test, type Page } from '@playwright/test'

const password = 'Senha-segura-123'

async function register(page: Page) {
  const email = `browser-${crypto.randomUUID()}@example.com`
  await page.goto('/cadastro')
  await page.getByLabel(/^Nome\s*\*?\s*$/).fill('Rafael Teste')
  await page.getByLabel(/^E-mail\s*\*?\s*$/).fill(email)
  await page.getByLabel(/^Senha\s*\*?\s*$/).fill(password)
  await page.getByLabel(/^Confirmar senha\s*\*?\s*$/).fill('Outra-senha-123')
  await page.getByRole('button', { name: 'Criar minha conta' }).click()
  await expect(page.getByRole('alert')).toContainText('senhas')
  await page.getByLabel(/^Confirmar senha\s*\*?\s*$/).fill(password)
  await page.getByRole('button', { name: 'Criar minha conta' }).click()
  await expect(page).toHaveURL(/\/login/)
  await expect(page.getByRole('status')).toContainText('Conta criada')
  return email
}

async function login(page: Page, email: string, secret = password) {
  const destination = new URL(page.url()).searchParams.get('redirect') || '/app/dashboard'
  await page.getByLabel(/^E-mail\s*\*?\s*$/).fill(email)
  await page.getByLabel(/^Senha\s*\*?\s*$/).fill(secret)
  await page.getByRole('button', { name: 'Entrar no TaskFlow' }).click()
  await expect(page).toHaveURL(new RegExp(`${destination}$`))
  await expect(page.locator('.topbar')).toBeVisible()
  await expect(page.locator('.tasks-loading')).toHaveCount(0)
}

async function navigate(page: Page, label: string) {
  await expect(page.locator('.topbar')).toBeVisible()
  if (
    await page
      .getByRole('button', { name: 'Abrir menu', exact: true })
      .isVisible()
  ) {
    await page.getByRole('button', { name: 'Abrir menu', exact: true }).click()
  }
  if (label === 'Meu perfil') await page.locator('.sidebar__profile').click()
  else
    await page
      .locator('.sidebar')
      .getByRole('link', { name: label, exact: true })
      .click()
}

async function logout(page: Page) {
  await navigate(page, 'Meu perfil')
  await page.getByRole('button', { name: 'Sair', exact: true }).click()
  await expect(page).toHaveURL(/\/login$/)
}

async function createTask(page: Page, title: string) {
  await page
    .getByRole('button', { name: 'Nova tarefa', exact: true })
    .first()
    .click()
  const drawer = page.getByRole('dialog')
  await expect(drawer.getByLabel(/^Título\s*\*?\s*$/)).toBeFocused()
  await drawer.getByLabel(/^Título\s*\*?\s*$/).fill(title)
  await drawer
    .getByLabel(/^Descrição\s*\*?\s*$/)
    .fill('Teste completo no navegador')
  await drawer.getByRole('combobox', { name: 'Prioridade', exact: true }).selectOption('high')
  await drawer.getByLabel(/^Prazo\s*\*?\s*$/).fill('2020-01-01')
  await drawer.getByLabel(/^Tags\s*\*?\s*$/).fill('Produto, Revisão')
  await drawer
    .getByRole('button', { name: 'Criar tarefa', exact: true })
    .click()
  await expect(drawer).toHaveCount(0)
}

function taskCard(page: Page, title: string) {
  return page
    .locator('.task-card')
    .filter({ has: page.getByText(title, { exact: true }) })
}

async function setFilter(page: Page, label: string, value: string) {
  await page.getByRole('button', { name: label, exact: true }).click()
  if (value === 'Baixa' || value === 'Backlog') {
    await page.screenshot({ path: test.info().outputPath(label === 'Filtrar por status' ? 'status-filter-menu.png' : 'priority-filter-menu.png') })
  }
  await page.getByRole('menuitemradio', { name: value, exact: true }).click()
}

async function setTaskStatus(page: Page, title: string, status: string) {
  await taskCard(page, title).getByRole('button', { name: `Alterar status de ${title}`, exact: true }).click()
  await page.getByRole('menuitemradio', { name: status, exact: true }).click()
}

test('protege rotas e apresenta autenticação responsiva', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  await page.goto('/tarefas')
  await expect(page).toHaveURL(/\/login/)
  await expect(
    page.getByRole('heading', { name: 'Entre na sua conta' }),
  ).toBeVisible()
  await expect(page.getByLabel(/^E-mail\s*\*?\s*$/)).toBeVisible()
  await page.screenshot({
    path: test.info().outputPath('login.png'),
    fullPage: true,
  })
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true)
  expect(errors).toEqual([])
})

test('cadastro, CRUD, filtros, quadro, avisos e persistência com API real', async ({
  page,
}) => {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  const email = await register(page)
  await page.getByLabel(/^E-mail\s*\*?\s*$/).fill(email)
  await page.getByLabel(/^Senha\s*\*?\s*$/).fill('Senha-incorreta-123')
  await page.getByRole('button', { name: 'Entrar no TaskFlow' }).click()
  await expect(page.getByRole('alert')).toContainText('Credenciais inválidas')
  await login(page, email)
  await navigate(page, 'Minhas tarefas')
  await expect(
    page.getByRole('heading', { name: 'Seu fluxo começa aqui' }),
  ).toBeVisible()
  await createTask(page, 'Revisar a entrega')
  let card = taskCard(page, 'Revisar a entrega')
  await expect(card).toContainText('Produto')
  await expect(card).toContainText('Alta')
  await card.getByRole('button', { name: 'Editar tarefa', exact: true }).click()
  await page
    .getByRole('dialog')
    .getByLabel(/^Título\s*\*?\s*$/)
    .fill('Entrega revisada')
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Salvar alterações' })
    .click()
  card = taskCard(page, 'Entrega revisada')
  await expect(card).toBeVisible()
  await setFilter(page, 'Filtrar por prioridade', 'Baixa')
  await expect(
    page.getByRole('heading', { name: 'Nenhum resultado encontrado' }),
  ).toBeVisible()
  await setFilter(page, 'Filtrar por prioridade', 'Alta')
  await page.getByRole('button', { name: 'Visualização em quadro' }).click()
  await expect(page.locator('.kanban')).toBeVisible()
  await card.getByRole('button', { name: 'Alterar status de Entrega revisada', exact: true }).click()
  await page.screenshot({ path: test.info().outputPath('kanban-status-menu.png') })
  await page.getByRole('menuitemradio', { name: 'Em andamento', exact: true }).click()
  await expect(
    page
      .locator('.kanban-column')
      .filter({ has: page.locator('header').getByText('Em andamento', { exact: true }) }),
  ).toContainText('Entrega revisada')
  await page.getByRole('button', { name: 'Notificações', exact: true }).click()
  await expect(page.locator('.notifications-popover')).toContainText(
    'Entrega revisada',
  )
  await page.getByRole('button', { name: 'Notificações', exact: true }).click()
  await setTaskStatus(page, 'Entrega revisada', 'Concluída')
  await setFilter(page, 'Filtrar por status', 'Backlog')
  await expect(
    page.getByRole('heading', { name: 'Nenhum resultado encontrado' }),
  ).toBeVisible()
  await setFilter(page, 'Filtrar por status', 'Concluídas')
  await expect(card).toBeVisible()
  await page.getByRole('button', { name: 'Visualização em lista' }).click()
  const search = (await page
    .getByLabel('Buscar em todo o TaskFlow')
    .isVisible())
    ? page.getByLabel('Buscar em todo o TaskFlow')
    : page.getByLabel('Buscar por tarefa ou tag')
  await search.fill('inexistente')
  await expect(
    page.getByRole('heading', { name: 'Nenhum resultado encontrado' }),
  ).toBeVisible()
  await search.fill('Revisão')
  await expect(card).toBeVisible()
  await search.fill('')
  await page.screenshot({
    path: test.info().outputPath('tasks.png'),
    fullPage: true,
  })
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true)
  await page.reload()
  await expect(page).toHaveURL(/\/app\/tarefas$/)
  await expect(page.locator('.topbar')).toBeVisible()
  card = taskCard(page, 'Entrega revisada')
  await expect(card).toContainText('Concluída')
  await card
    .getByRole('button', { name: 'Excluir tarefa', exact: true })
    .click()
  const deleteDialog = page.getByRole('dialog', { name: 'Excluir tarefa' })
  await expect(deleteDialog).toBeVisible()
  await deleteDialog.getByRole('button', { name: 'Cancelar' }).click()
  await expect(deleteDialog).toHaveCount(0)
  await expect(card).toBeVisible()
  await card
    .getByRole('button', { name: 'Excluir tarefa', exact: true })
    .click()
  await expect(deleteDialog).toBeVisible()
  await deleteDialog.getByRole('button', { name: 'Excluir' }).click()
  await expect(deleteDialog).toHaveCount(0)
  await expect(
    page.getByRole('heading', { name: 'Seu fluxo começa aqui' }),
  ).toBeVisible()
  await logout(page)
  expect(await page.evaluate(() => sessionStorage.length)).toBe(0)
  expect(
    await page.evaluate(() =>
      Object.keys(localStorage).every((key) => key === 'taskflow-view'),
    ),
  ).toBe(true)
  expect(errors).toEqual([])
})

test('perfil e mudança de senha persistem e exigem a senha atual', async ({
  page,
}) => {
  const email = await register(page)
  await login(page, email)
  await navigate(page, 'Meu perfil')
  await page.getByLabel(/^Nome\s*\*?\s*$/).fill('Rafael Atualizado')
  const nextEmail = `updated-${crypto.randomUUID()}@example.com`
  await page.getByLabel(/^E-mail\s*\*?\s*$/).fill(nextEmail)
  await page.getByRole('button', { name: 'Salvar perfil' }).click()
  await expect(page.getByRole('status')).toContainText('Perfil atualizado')
  await page.getByLabel(/^Senha atual\s*\*?\s*$/).fill('Senha-errada-123')
  await page.getByLabel(/^Nova senha\s*\*?\s*$/).fill('Nova-senha-456')
  await page
    .getByLabel(/^Confirmar nova senha\s*\*?\s*$/)
    .fill('Nova-senha-456')
  await page.getByRole('button', { name: 'Alterar senha', exact: true }).click()
  await expect(page.getByRole('alert')).toBeVisible()
  await page.getByLabel(/^Senha atual\s*\*?\s*$/).fill(password)
  await page.getByRole('button', { name: 'Alterar senha', exact: true }).click()
  await expect(page.getByRole('status')).toContainText('Senha alterada')
  await navigate(page, 'Minhas tarefas')
  await createTask(page, 'Tarefa após a senha')
  await expect(taskCard(page, 'Tarefa após a senha')).toBeVisible()
  await logout(page)
  await login(page, nextEmail, 'Nova-senha-456')
  await expect(page.getByRole('heading', { name: /Olá, Rafael/ })).toBeVisible()
})

test('limpa a sessão após 401 e permite uma nova autenticação', async ({
  page,
}) => {
  const email = await register(page)
  await login(page, email)
  await page.route('**/api/v1/tasks*', (route) =>
    route.fulfill({
      status: 401,
      contentType: 'application/json',
      body: '{"detail":"Token inválido ou expirado"}',
    }),
  )
  await page
    .getByRole('button', { name: 'Nova tarefa', exact: true })
    .first()
    .click()
  await page
    .getByRole('dialog')
    .getByLabel(/^Título\s*\*?\s*$/)
    .fill('Sessão expirada')
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Criar tarefa', exact: true })
    .click()
  await expect(page).toHaveURL(/\/login\?expired=1$/)
  await expect(page.getByRole('alert')).toContainText('Sua sessão expirou')
  await page.unroute('**/api/v1/tasks*')
  await login(page, email)
})

test('trocar de conta não revela tarefas da conta anterior', async ({
  page,
}) => {
  const emails = [await register(page), await register(page)]
  await login(page, emails[0]!)
  await navigate(page, 'Minhas tarefas')
  await createTask(page, 'Tarefa privada da primeira conta')
  await expect(taskCard(page, 'Tarefa privada da primeira conta')).toBeVisible()
  await logout(page)
  await login(page, emails[1]!)
  await navigate(page, 'Minhas tarefas')
  await expect(
    page.getByRole('heading', { name: 'Seu fluxo começa aqui' }),
  ).toBeVisible()
  await expect(page.getByText('Tarefa privada da primeira conta')).toHaveCount(
    0,
  )
  await logout(page)
  await login(page, emails[0]!)
  await navigate(page, 'Minhas tarefas')
  await expect(taskCard(page, 'Tarefa privada da primeira conta')).toBeVisible()
})


test('a ordem do quadro persiste após entrar novamente', async ({ page }, testInfo) => {
  const email = await register(page)
  await login(page, email)
  await navigate(page, 'Minhas tarefas')
  await createTask(page, 'Primeiro item')
  await createTask(page, 'Segundo item')
  await page.getByRole('button', { name: 'Visualização em quadro' }).click()
  if (testInfo.project.name === 'mobile') {
    await setTaskStatus(page, 'Primeiro item', 'Em andamento')
    await expect(taskCard(page, 'Primeiro item').getByRole('button', { name: 'Alterar status de Primeiro item', exact: true })).toContainText('Em andamento')
    await setTaskStatus(page, 'Primeiro item', 'Backlog')
  } else {
    await taskCard(page, 'Segundo item').dragTo(taskCard(page, 'Primeiro item'))
  }
  const cards = page.locator('.kanban-column').first().locator('.task-card')
  await expect(cards.first()).toContainText('Segundo item')
  await logout(page)
  await login(page, email)
  await navigate(page, 'Minhas tarefas')
  await page.getByRole('button', { name: 'Visualização em quadro' }).click()
  await expect(cards.first()).toContainText('Segundo item')
})


test('edita status pela coluna, bloqueia enquanto salva e recupera falhas sem modal', async ({ page }) => {
  const email = await register(page)
  await login(page, email)
  await navigate(page, 'Minhas tarefas')
  await createTask(page, 'Edição rápida de status')
  const card = taskCard(page, 'Edição rápida de status')
  const status = card.getByRole('button', { name: 'Alterar status de Edição rápida de status', exact: true })
  async function chooseStatus(value: string) {
    await status.click()
    await page.getByRole('menuitemradio', { name: value, exact: true }).click()
  }
  await status.focus()
  await page.keyboard.press('ArrowDown')
  await expect(page.getByRole('menu')).toBeVisible()
  await page.keyboard.press('End')
  await expect(page.getByRole('menuitemradio', { name: 'Concluída', exact: true })).toBeFocused()
  await page.keyboard.press('Home')
  await expect(page.getByRole('menuitemradio', { name: 'Backlog', exact: true })).toBeFocused()
  const menuBounds = await page.getByRole('menu').boundingBox()
  const viewport = page.viewportSize()!
  expect(menuBounds!.x).toBeGreaterThanOrEqual(0)
  expect(menuBounds!.y).toBeGreaterThanOrEqual(0)
  expect(menuBounds!.x + menuBounds!.width).toBeLessThanOrEqual(viewport.width)
  expect(menuBounds!.y + menuBounds!.height).toBeLessThanOrEqual(viewport.height)
  await page.screenshot({ path: test.info().outputPath('status-menu.png') })
  await page.keyboard.press('Escape')
  await expect(status).toBeFocused()

  await expect(page.getByRole('button', { name: 'Concluir tarefa', exact: true })).toHaveCount(0)
  await expect(page.locator('.task-check')).toHaveCount(0)
  let release!: () => void
  const pending = new Promise<void>(resolve => { release = resolve })
  await page.route('**/api/v1/tasks/*', async route => {
    if (route.request().method() !== 'PATCH') return route.continue()
    await pending
    await route.fulfill({ status: 503, contentType: 'application/json', body: '{"detail":"Falha temporária"}' })
  })
  try {
    await chooseStatus('Concluída')
    await expect(status).toBeDisabled()
    await expect(status).toContainText('Backlog')
    await expect(page.getByRole('dialog')).toHaveCount(0)
  } finally {
    release()
  }
  await expect(page.getByText('Não foi possível mover a tarefa.', { exact: true })).toBeVisible()
  await expect(status).toBeEnabled()
  await expect(status).toContainText('Backlog')
  await page.unroute('**/api/v1/tasks/*')
  await chooseStatus('Em andamento')
  await expect(status).toContainText('Em andamento')
  await chooseStatus('Concluída')
  await expect(status).toContainText('Concluída')
  await expect(page.getByRole('dialog')).toHaveCount(0)
  await logout(page)
  await login(page, email)
  await navigate(page, 'Minhas tarefas')
  await expect(status).toContainText('Concluída')
  await chooseStatus('Backlog')
  await expect(status).toContainText('Backlog')
})


test('restaura sessão ao recarregar, redireciona login e respeita logout e expiração', async ({ page, context }) => {
  const email = await register(page)
  await login(page, email)
  const session = (await context.cookies()).find(cookie => cookie.name === 'taskflow_session')
  expect(session?.httpOnly).toBe(true)
  expect(await page.evaluate(() => document.cookie.includes('taskflow_session'))).toBe(false)
  await page.reload()
  await expect(page).toHaveURL(/\/app\/dashboard$/)
  await expect(page.getByRole('heading', { name: /Olá, Rafael/ })).toBeVisible()
  await page.goto('/login?redirect=/app/dashboard')
  await expect(page).toHaveURL(/\/app\/dashboard$/)
  await page.goto('/app/tarefas')
  await expect(page.getByRole('heading', { name: 'Minhas tarefas', exact: true })).toBeVisible()
  await logout(page)
  await page.reload()
  await expect(page).toHaveURL(/\/login$/)
  await page.goto('/app/tarefas')
  await expect(page).toHaveURL(/\/login/)
  await login(page, email)
  await context.clearCookies({ name: 'taskflow_session' })
  await page.reload()
  await expect(page).toHaveURL(/\/login/)
})


test('datas da agenda permanecem legíveis em uma linha', async ({ page }) => {
  const email = await register(page)
  await login(page, email)
  for (const date of ['2026-02-28', '2026-09-30', '2026-10-14', '2026-11-30']) {
    const response = await page.request.post('/api/v1/tasks', {
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      data: { titulo: `Prazo ${date}`, due_date: date },
    })
    expect(response.status()).toBe(201)
  }
  await page.reload()
  const dates = page.locator('.date-tile time')
  await expect(dates).toHaveCount(4)
  await expect(page.locator('time[datetime="2026-10-14"]')).toHaveText('14 out.')
  await page.evaluate(() => document.fonts.ready)
  for (const date of await dates.all()) {
    const layout = await date.evaluate(element => {
      const range = document.createRange()
      range.selectNodeContents(element)
      const bounds = element.getBoundingClientRect()
      const tile = element.parentElement!.getBoundingClientRect()
      return { lines: range.getClientRects().length, fits: bounds.left >= tile.left && bounds.right <= tile.right }
    })
    expect(layout.lines).toBe(1)
    expect(layout.fits).toBe(true)
  }
  await page.locator('.upcoming-panel').screenshot({ path: test.info().outputPath('agenda-datas.png') })
})
