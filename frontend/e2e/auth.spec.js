import { test, expect } from '@playwright/test'

test.describe('Authentication Flow', () => {
  // Ensure tests in this suite run sequentially to share state
  test.describe.configure({ mode: 'serial' })
  test('complete user registration and login', async ({ page }) => {
    // Navigate to the app
    await page.goto('/')

    // Click on register link (robusto al idioma)
    await page.waitForSelector('a[href="/register"]', { timeout: 15000 })
    await page.click('a[href="/register"]')

    // Generate a unique user to avoid collisions across runs
    const unique = Date.now()
    const username = `e2euser_${unique}`
    const email = `e2e_${unique}@example.com`
    const password = 'e2epassword123'

    // Fill registration form
    await page.fill('input[name="username"]', username)
    await page.fill('input[name="email"]', email)
    await page.fill('input[name="full_name"]', 'E2E User')
    await page.fill('input[name="password"]', password)
    await page.fill('input[name="confirmPassword"]', password)

    // Submit registration
    await page.click('button[type="submit"]')

    // Should redirect to login
    await expect(page).toHaveURL(/\/login$/)

    // Now perform login with the newly registered user
    await page.fill('input[name="username"]', username)
    await page.fill('input[name="password"]', password)

    // Esperar a que el botón esté habilitado y hacer submit
    const submit = page.locator('button[type="submit"]')
    await expect(submit).toBeEnabled({ timeout: 15000 })
    await submit.click()

    // Esperar a que el token se guarde en localStorage
    await expect.poll(async () => {
      return await page.evaluate(() => localStorage.getItem('token'))
    }, { timeout: 15000 }).not.toBeNull()

    // Verificar navegación SPA al dashboard
    await page.waitForURL(/\/dashboard/, { timeout: 15000 })
  })
})