-- 002_clases_profesor.sql
-- Corrige un olvido de la migración 001: la tabla `clases` no quedó
-- enlazada a `profesores`, pese a que la regla de negocio es que un
-- profesor administra varias clases propias en paralelo.

ALTER TABLE clases
    ADD COLUMN profesor_id INT UNSIGNED NOT NULL AFTER id,
    ADD CONSTRAINT fk_clases_profesor FOREIGN KEY (profesor_id) REFERENCES profesores(id) ON DELETE CASCADE,
    ADD INDEX idx_clases_profesor (profesor_id);
