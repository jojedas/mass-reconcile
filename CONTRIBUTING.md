# Contributing to Mass Reconciliation

¡Gracias por tu interés en contribuir a Mass Reconciliation! 🎉

## Código de Conducta

Este proyecto sigue el [Código de Conducta de OCA](https://odoo-community.org/page/code-of-conduct). Al participar, te comprometes a mantener un ambiente respetuoso y acogedor.

## Cómo Contribuir

### Reportar Bugs

Antes de reportar un bug:
1. Busca en [issues existentes](https://github.com/jojedas/mass-reconcile/issues)
2. Verifica que estás usando la versión más reciente
3. Prueba en un ambiente limpio (Docker fresh start)

Al reportar un bug, incluye:
- **Descripción clara** del problema
- **Pasos para reproducir**
- **Comportamiento esperado** vs. comportamiento actual
- **Logs relevantes** (`make logs-odoo`)
- **Ambiente**: Odoo version, OS, Docker version
- **Screenshots** si aplica

**Template:**
```markdown
## Descripción
Breve descripción del bug

## Pasos para Reproducir
1. Ir a...
2. Hacer clic en...
3. Ver error...

## Comportamiento Esperado
Qué debería pasar

## Comportamiento Actual
Qué pasa en realidad

## Logs
```
[Pegar logs aquí]
```

## Ambiente
- Odoo: 18.0
- OS: Ubuntu 22.04
- Docker: 24.0.7
```

### Sugerir Features

Para sugerir una nueva funcionalidad:
1. Abre un issue con label `enhancement`
2. Describe el **problema** que resuelve
3. Propón una **solución** (opcional)
4. Discute con la comunidad antes de implementar

**Template:**
```markdown
## Problema / Caso de Uso
Por qué necesitamos esto

## Solución Propuesta
Cómo podría funcionar

## Alternativas Consideradas
Otras opciones que evaluaste

## Impacto
Qué beneficios trae
```

### Pull Requests

#### Workflow

```bash
# 1. Fork el repositorio en GitHub

# 2. Clonar tu fork
git clone https://github.com/TU_USUARIO/mass-reconcile.git
cd mass-reconcile

# 3. Añadir upstream remote
git remote add upstream https://github.com/jojedas/mass-reconcile.git

# 4. Crear branch desde master
git checkout master
git pull upstream master
git checkout -b feature/nombre-descriptivo

# 5. Hacer cambios y commits
git add .
git commit -m "feat: añadir feature X"

# 6. Push a tu fork
git push origin feature/nombre-descriptivo

# 7. Abrir PR en GitHub
```

#### Commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: Nueva funcionalidad
- `fix`: Bug fix
- `docs`: Solo documentación
- `style`: Formateo (sin cambios de código)
- `refactor`: Refactoring (ni feat ni fix)
- `test`: Añadir tests
- `chore`: Mantenimiento (build, deps)

**Examples:**
```bash
feat(engine): add fuzzy matching algorithm
fix(batch): correct progress calculation on empty batches
docs(tutorial): add troubleshooting section
test(scorer): add edge case tests for date scoring
refactor(models): extract common validation logic
chore(docker): upgrade PostgreSQL to 15.1
```

#### Code Style

**Python:**
- Follow [OCA Guidelines](https://github.com/OCA/odoo-community.org/blob/master/website/Contribution/CONTRIBUTING.rst)
- Use **Black** for formatting (line length 88)
- Use **flake8** for linting
- Use **pylint** with Odoo plugin

```bash
# Formatear código
black models/ tests/

# Lint
flake8 models/ tests/
pylint --load-plugins=pylint_odoo models/ tests/
```

**XML:**
- Indent: 4 spaces
- Use `<odoo>` root tag
- Follow Odoo view conventions

#### Testing

**Todo PR debe incluir tests** (excepto docs-only).

```bash
# Escribir tests en tests/
# Ejecutar tests localmente
make test

# Verificar coverage
docker-compose run --rm odoo odoo \
    --database=jumo \
    --test-enable \
    --test-tags=mass_reconcile \
    --stop-after-init \
    --coverage=mass_reconcile
```

**Test Guidelines:**
- Usa `TransactionCase` para tests de modelo
- Usa `HttpCase` para tests de controlador
- Mock external dependencies
- Tests deben ser independientes (no orden específico)
- Nombres descriptivos (`test_exact_amount_matching_creates_proposal`)

#### Documentation

Actualiza documentación si:
- Añades nueva feature → Actualizar README + TUTORIAL
- Cambias API → Actualizar docstrings
- Cambias configuración → Actualizar SETUP.md
- Añades comando → Actualizar Makefile help

#### PR Checklist

Antes de abrir PR, verifica:

- [ ] Branch actualizado con upstream master
- [ ] Commits siguen Conventional Commits
- [ ] Tests pasan (`make test`)
- [ ] Código formateado (`black`, `flake8`)
- [ ] Documentación actualizada
- [ ] CHANGELOG.md actualizado (para features/fixes)
- [ ] PR template completado

#### PR Template

```markdown
## Descripción
¿Qué cambia este PR?

## Tipo de Cambio
- [ ] Bug fix (non-breaking)
- [ ] Nueva feature (non-breaking)
- [ ] Breaking change
- [ ] Documentación

## Cómo se Ha Probado
Describe tests ejecutados

## Checklist
- [ ] Tests pasan
- [ ] Documentación actualizada
- [ ] Código formateado
- [ ] CHANGELOG actualizado
```

### Code Review Process

1. **Automatic checks**: CI runs tests y linting
2. **Maintainer review**: Revisión de código por maintainer
3. **Discussion**: Feedback y iteración
4. **Approval**: Maintainer aprueba
5. **Merge**: Squash and merge a master

**Review criteria:**
- ✅ Tests completos y pasando
- ✅ Código sigue style guide
- ✅ Documentación clara
- ✅ No breaking changes sin justificación
- ✅ Performance acceptable

## Desarrollo

### Setup Local

```bash
# Clonar
git clone https://github.com/jojedas/mass-reconcile.git
cd mass-reconcile

# Setup automático
./setup.sh

# Crear database de testing
docker-compose exec db createdb -U odoo test_jumo

# Activar developer mode en Odoo
# Settings → Activate developer mode
```

### Project Structure

```
mass_reconcile/
├── models/              # Business logic
│   ├── __init__.py
│   ├── mass_reconcile_batch.py
│   ├── mass_reconcile_match.py
│   ├── mass_reconcile_engine.py
│   └── mass_reconcile_scorer.py
├── security/            # Access control
├── tests/               # Unit tests
├── static/              # Frontend assets (future)
├── views/               # XML views (future)
└── __manifest__.py      # Module metadata
```

### Adding a New Model

```python
# 1. Create file in models/
# models/mass_reconcile_foo.py

from odoo import models, fields, api

class MassReconcileFoo(models.Model):
    _name = 'mass.reconcile.foo'
    _description = 'Foo Model'

    name = fields.Char(required=True)

# 2. Import in models/__init__.py
from . import mass_reconcile_foo

# 3. Add to __manifest__.py
'data': [
    'security/ir.model.access.csv',  # Add access rights
]

# 4. Add security in security/ir.model.access.csv
# id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_mass_reconcile_foo_user,mass.reconcile.foo.user,model_mass_reconcile_foo,account.group_account_user,1,1,1,0
access_mass_reconcile_foo_manager,mass.reconcile.foo.manager,model_mass_reconcile_foo,account.group_account_manager,1,1,1,1

# 5. Add tests
# tests/test_foo.py

from odoo.tests import TransactionCase

class TestMassReconcileFoo(TransactionCase):
    def test_create_foo(self):
        foo = self.env['mass.reconcile.foo'].create({
            'name': 'Test Foo'
        })
        self.assertEqual(foo.name, 'Test Foo')
```

### Adding a View

```xml
<!-- views/mass_reconcile_foo_views.xml -->
<odoo>
    <record id="view_mass_reconcile_foo_form" model="ir.ui.view">
        <field name="name">mass.reconcile.foo.form</field>
        <field name="model">mass.reconcile.foo</field>
        <field name="arch" type="xml">
            <form>
                <sheet>
                    <group>
                        <field name="name"/>
                    </group>
                </sheet>
            </form>
        </field>
    </record>

    <record id="action_mass_reconcile_foo" model="ir.actions.act_window">
        <field name="name">Foo</field>
        <field name="res_model">mass.reconcile.foo</field>
        <field name="view_mode">tree,form</field>
    </record>

    <menuitem id="menu_mass_reconcile_foo"
              name="Foo"
              parent="account.menu_finance"
              action="action_mass_reconcile_foo"/>
</odoo>
```

### Debugging

```bash
# View logs
make logs-odoo

# Shell into container
make shell

# Python shell
docker-compose exec odoo odoo shell -d jumo

# Enable debug mode
# In odoo.conf:
log_level = debug

# Set breakpoint in code
import pdb; pdb.set_trace()
```

### Performance Testing

```python
# Use profiler
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here
batch.action_process()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

## Release Process

(For maintainers only)

1. Update version in `__manifest__.py`
2. Update CHANGELOG.md
3. Create git tag: `git tag -a v1.1.0 -m "Release 1.1.0"`
4. Push tag: `git push origin v1.1.0`
5. Create GitHub release with notes
6. Announce in Odoo forums

## Getting Help

- **Documentation**: [SETUP.md](SETUP.md), [TUTORIAL.md](TUTORIAL.md)
- **Issues**: [GitHub Issues](https://github.com/jojedas/mass-reconcile/issues)
- **OCA**: [Odoo Community Association](https://odoo-community.org/)
- **Forum**: [Odoo Forum](https://www.odoo.com/forum)

## License

By contributing, you agree that your contributions will be licensed under the LGPL-3 License.

---

**¡Gracias por contribuir!** 🙏

Every contribution, no matter how small, makes this project better.
