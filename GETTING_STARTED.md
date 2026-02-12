# Getting Started - Inicio Rápido

## 🚀 Instalación en 3 Pasos

### 1️⃣ Clonar el Repositorio

```bash
git clone https://github.com/jojedas/mass-reconcile.git
cd mass-reconcile
```

### 2️⃣ Ejecutar Setup Automático

```bash
./setup.sh
```

⏱️ **Tiempo**: 5-10 minutos

✅ **Esto instala**:
- Docker containers (Odoo 18.0 + PostgreSQL 15)
- OCA modules (account-reconcile)
- Todas las dependencias

### 3️⃣ Crear Base de Datos y Módulos

```bash
# 1. Abre http://localhost:8069 en tu navegador
# 2. Crea database "jumo" con master password "jumo"
# 3. Espera 2-3 minutos

# 4. Instala módulos
./install-modules.sh
```

⏱️ **Tiempo**: 2-3 minutos

---

## ✅ Verificación

```bash
# Ver logs
make logs-odoo

# Verificar que Odoo esté corriendo
curl http://localhost:8069

# Deberías ver la página de login de Odoo
```

---

## 📚 ¿Qué Sigue?

### Para Usuarios (Contadores/Administradores)

👉 Lee el **[TUTORIAL.md](TUTORIAL.md)** completo:
- Cómo usar el módulo
- Casos de uso comunes
- Troubleshooting
- FAQ

### Para Desarrolladores

👉 Lee la **[CONTRIBUTING.md](CONTRIBUTING.md)**:
- Estructura del código
- Cómo añadir features
- Testing
- Code review process

---

## 🆘 ¿Problemas?

### Contenedores no inician

```bash
# Verificar puertos
sudo lsof -i :8069
sudo lsof -i :5432

# Reiniciar todo
docker-compose down
docker-compose up -d
```

### Módulo no aparece

```bash
# Actualizar lista de apps
docker-compose restart odoo

# En Odoo: Apps → Update Apps List
```

### Más ayuda

- 📖 [TUTORIAL.md](TUTORIAL.md) - Tutorial completo en español
- 🔧 [SETUP.md](SETUP.md) - Setup detallado
- 🐛 [GitHub Issues](https://github.com/jojedas/mass-reconcile/issues)

---

## 📊 Estructura del Proyecto

```
mass-reconcile/
├── 📘 README.md              # Overview general
├── 🚀 GETTING_STARTED.md     # Este archivo
├── ⚡ QUICKSTART.md          # Setup en 5 minutos
├── 📖 TUTORIAL.md            # Tutorial completo (español)
├── ⚙️  SETUP.md              # Setup detallado
├── 🤝 CONTRIBUTING.md        # Guía de contribución
├── 📜 CHANGELOG.md           # Historial de versiones
├── 🐳 docker-compose.yml     # Docker stack
├── 🔧 Makefile               # Comandos útiles
├── 🏗️  models/                # Código del módulo
├── 🔐 security/              # Seguridad y permisos
├── ✅ tests/                 # Tests unitarios
└── 📁 .planning/             # Planificación del proyecto (GSD)
```

---

## 🎯 Comandos Más Usados

```bash
# Iniciar contenedores
make start

# Ver logs en tiempo real
make logs-odoo

# Parar contenedores
make stop

# Reiniciar Odoo
make restart-odoo

# Actualizar módulo después de cambios
make upgrade-module MODULE=mass_reconcile

# Ver todos los comandos
make help
```

---

## 🌟 Features Principales

✅ **Matching Inteligente**: Algoritmos automáticos de coincidencia
✅ **Batch Processing**: Procesa miles de líneas en lotes
✅ **Confidence Scoring**: Score de confianza 0-100
✅ **3-Tier Classification**: Safe/Probable/Doubtful
✅ **Dual Mode**: Automático o manual
✅ **OCA Compatible**: Integrado con account-reconcile

---

## 📞 Soporte

- **Issues**: https://github.com/jojedas/mass-reconcile/issues
- **Documentación**: Ver carpeta raíz del proyecto
- **OCA Community**: https://odoo-community.org/

---

## 📄 Licencia

LGPL-3 (compatible con Odoo Community)

---

**¡Listo para empezar!** 🎉

👉 Siguiente paso: Abre [TUTORIAL.md](TUTORIAL.md) para ver ejemplos de uso.
