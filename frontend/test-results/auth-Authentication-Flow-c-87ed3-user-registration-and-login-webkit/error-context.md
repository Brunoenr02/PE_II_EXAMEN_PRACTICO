# Page snapshot

```yaml
- main [ref=e4]:
  - generic [ref=e6]:
    - generic [ref=e7]:
      - img [ref=e9]
      - heading "Iniciar Sesión" [level=2] [ref=e11]
      - paragraph [ref=e12]: Accede a tu cuenta para gestionar tus planes estratégicos
    - generic [ref=e13]:
      - generic [ref=e14]:
        - generic [ref=e15]:
          - text: Nombre de Usuario
          - textbox "Tu nombre de usuario" [ref=e16]
        - generic [ref=e17]:
          - text: Contraseña
          - generic [ref=e18]:
            - textbox "Tu contraseña" [ref=e19]
            - button [ref=e20] [cursor=pointer]:
              - img [ref=e21]
      - button "Iniciar Sesión" [ref=e25] [cursor=pointer]:
        - img [ref=e26]
        - text: Iniciar Sesión
      - paragraph [ref=e30]:
        - text: ¿No tienes cuenta?
        - link "Regístrate" [ref=e31]:
          - /url: /register
```