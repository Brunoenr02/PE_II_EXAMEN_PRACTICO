import { test, expect } from '@playwright/test'

test.describe('Complete Strategic Plan Flow', () => {
  test('full user journey: registration → login → plan creation → editing → dashboard', async ({ page }) => {
    // 1. User Registration
    await page.goto('/')
    await page.waitForSelector('a[href="/register"]', { timeout: 15000 })
    await page.click('a[href="/register"]')

    const timestamp = Date.now()
    const username = `testuser${timestamp}`
    const email = `test${timestamp}@example.com`

    await page.fill('input[name="username"]', username)
    await page.fill('input[name="email"]', email)
    await page.fill('input[name="full_name"]', 'Test User')
    await page.fill('input[name="password"]', 'testpassword123')
    await page.fill('input[name="confirmPassword"]', 'testpassword123')

    // Esperar a que el botón esté habilitado y hacer submit
    const submit = page.locator('button[type="submit"]')
    await expect(submit).toBeEnabled({ timeout: 15000 })
    await submit.click()

    // Should redirect to login
    await expect(page).toHaveURL(/\/login$/)

    // 2. User Login
    await page.fill('input[name="username"]', username)
    await page.fill('input[name="password"]', 'testpassword123')
    await page.click('button[type="submit"]')

    // Should be on dashboard
    await expect(page).toHaveURL(/\/dashboard/)

    // 3. Create Strategic Plan
    await page.click('text=Crear mi primer plan')
    await page.fill('input[name="title"]', 'Plan Estratégico de Prueba E2E')
    await page.fill('textarea[name="description"]', 'Descripción completa del plan estratégico')
    await page.click('button[type="submit"]')

    // Should navigate to plan editor
    await expect(page).toHaveURL(/\/plans\/\d+/)

    // 4. Edit Company Identity
    await page.click('text=Identidad Empresarial')
    await page.fill('textarea[name="mission"]', 'Nuestra misión es innovar y liderar')
    await page.fill('textarea[name="vision"]', 'Ser la empresa líder en tecnología')
    await page.fill('textarea[name="values"]', 'Innovación\nExcelencia\nIntegridad')
    await page.fill('textarea[name="objectives"]', 'Objetivo 1: Aumentar ventas\nObjetivo 2: Expandir mercado')
    await page.click('button[type="submit"]')

    // 5. Edit SWOT Analysis
    await page.click('text=Análisis SWOT')
    await page.fill('textarea[name="strengths"]', 'Fuerza técnica\nEquipo calificado')
    await page.fill('textarea[name="weaknesses"]', 'Dependencia de proveedores')
    await page.fill('textarea[name="opportunities"]', 'Mercado en crecimiento')
    await page.fill('textarea[name="threats"]', 'Competencia creciente')
    await page.click('button[type="submit"]')

    // 6. Edit Analysis Tools
    await page.click('text=Herramientas de Análisis')
    await page.fill('textarea[name="value_chain"]', '{"primary": {"inbound_logistics": "Optimizado"}}')
    await page.fill('textarea[name="porter_forces"]', '{"competitive_rivalry": "Alta"}')
    await page.click('button[type="submit"]')

    // 7. Edit Strategies
    await page.click('text=Estrategias')
    await page.fill('textarea[name="strategies"]', 'Estrategia de diferenciación\nEstrategia de costo')
    await page.fill('textarea[name="implementation_timeline"]', '{"Q1": "Implementar estrategia 1"}')
    await page.fill('textarea[name="success_indicators"]', 'Aumento de 20% en ventas\nMejora de 15% en satisfacción')
    await page.click('button[type="submit"]')

    // 8. View Executive Summary
    await page.click('text=Resumen Ejecutivo')
    await expect(page.locator('text=Plan Estratégico de Prueba E2E')).toBeVisible()

    // 9. Return to Dashboard
    await page.click('text=Dashboard')
    await expect(page).toHaveURL(/\/dashboard/)
    await expect(page.locator('text=Plan Estratégico de Prueba E2E')).toBeVisible()

    // 10. Verify WebSocket connection (if implemented)
    // This would require checking for real-time updates
    // For now, just verify the plan appears in dashboard
  })

  test('collaborative editing invitation flow', async ({ browser }) => {
    // Create two browser contexts for two users
    const context1 = await browser.newContext()
    const context2 = await browser.newContext()

    const page1 = await context1.newPage()
    const page2 = await context2.newPage()

    const timestamp = Date.now()
    const user1 = `owner${timestamp}`
    const user2 = `collaborator${timestamp}`

    // User 1: Register and create plan
    await page1.goto('/')
    await page1.waitForSelector('a[href="/register"]', { timeout: 15000 })
    await page1.click('a[href="/register"]')
    await page1.fill('input[name="username"]', user1)
    await page1.fill('input[name="email"]', `${user1}@example.com`)
    await page1.fill('input[name="full_name"]', 'Owner User')
    await page1.fill('input[name="password"]', 'password123')
    await page1.fill('input[name="confirmPassword"]', 'password123')
    await page1.click('button[type="submit"]')

    // Should redirect to login
    await expect(page1).toHaveURL(/\/login$/)

    await page1.fill('input[name="username"]', user1)
    await page1.fill('input[name="password"]', 'password123')
    await page1.click('button[type="submit"]')

    await page1.click('text=Crear mi primer plan')
    await page1.fill('input[name="title"]', 'Plan Colaborativo')
    await page1.fill('textarea[name="description"]', 'Plan para testing colaborativo')
    await page1.click('button[type="submit"]')

    // User 2: Register
    await page2.goto('/')
    await page2.waitForSelector('a[href="/register"]', { timeout: 15000 })
    await page2.click('a[href="/register"]')
    await page2.fill('input[name="username"]', user2)
    await page2.fill('input[name="email"]', `${user2}@example.com`)
    await page2.fill('input[name="full_name"]', 'Collaborator User')
    await page2.fill('input[name="password"]', 'password123')
    await page2.fill('input[name="confirmPassword"]', 'password123')
    await page2.click('button[type="submit"]')

    // User 1: Send invitation
    await page1.click('text=Invitar colaboradores')
    await page1.fill('input[name="email"]', `${user2}@example.com`)
    await page2.click('button[type="submit"]')

    // Should redirect to login
    await expect(page2).toHaveURL(/\/login$/)

    // User 2: Login and check notifications
    await page2.fill('input[name="username"]', user2)
    await page2.fill('input[name="password"]', 'password123')
    await page2.click('button[type="submit"]')

    // Check for invitation notification
    await expect(page2.locator('text=invitación')).toBeVisible()

    // Accept invitation
    await page2.click('text=Aceptar')

    // Both users should be able to access the plan
    await expect(page2.locator('text=Plan Colaborativo')).toBeVisible()

    await context1.close()
    await context2.close()
  })
})