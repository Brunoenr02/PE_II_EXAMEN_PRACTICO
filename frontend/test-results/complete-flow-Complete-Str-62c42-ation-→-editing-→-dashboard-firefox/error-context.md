# Page snapshot

```yaml
- main [ref=e4]:
  - generic [ref=e6]:
    - generic [ref=e7]:
      - img [ref=e9]
      - heading "Iniciar Sesión" [level=2] [ref=e14]
      - paragraph [ref=e15]: Accede a tu cuenta para gestionar tus planes estratégicos
    - generic [ref=e16]:
      - generic [ref=e17]:
        - generic [ref=e18]:
          - text: Nombre de Usuario
          - textbox "Tu nombre de usuario" [ref=e19]
        - generic [ref=e20]:
          - text: Contraseña
          - generic [ref=e21]:
            - textbox "Tu contraseña" [ref=e22]
            - button [ref=e23] [cursor=pointer]:
              - img [ref=e24]
      - button "Iniciar Sesión" [ref=e28] [cursor=pointer]:
        - img [ref=e29]
        - text: Iniciar Sesión
      - paragraph [ref=e34]:
        - text: ¿No tienes cuenta?
        - link "Regístrate" [ref=e35] [cursor=pointer]:
          - /url: /register
```