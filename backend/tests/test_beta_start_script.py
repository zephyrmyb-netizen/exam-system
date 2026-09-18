from pathlib import Path


def test_beta_start_script_uses_the_default_application_database():
    script = Path("scripts/start-beta.ps1").read_text(encoding="utf-8")

    assert 'Join-Path $Root "backend\\xuexibao.db"' in script
    assert '$env:DATABASE_URL =' not in script
    assert 'xuexibao-beta.db' not in script
    assert '& $Python -m alembic -c "backend\\alembic.ini" upgrade head' in script
